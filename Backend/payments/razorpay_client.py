"""
Razorpay API client for payment operations.
"""

import base64
import time
from datetime import datetime, timedelta, timezone
from typing import Dict, Optional

import httpx

from config.settings import get_settings
from dao.payments import PaymentDAO
from data.models import PaymentStatus
from payments.models.schemas import PaymentLinkResponse
from utils.logger import get_logger

logger = get_logger()


class RazorpayClient:
    """Razorpay API client for payment operations."""

    def __init__(self):
        self.settings = get_settings().razorpay
        self.base_url = self.settings.BASE_URL
        self.api_key = self.settings.API_KEY
        self.api_secret = self.settings.API_SECRET
        
        # Create basic auth header
        credentials = f"{self.api_key}:{self.api_secret}"
        encoded_credentials = base64.b64encode(credentials.encode()).decode()
        self.auth_header = f"Basic {encoded_credentials}"
        
        self.headers = {
            "Authorization": self.auth_header,
            "Content-Type": "application/json"
        }

    async def create_payment_link(
        self, 
        user_id: str, 
        sku_id: str, 
    ) -> Optional[PaymentLinkResponse]:
        """
        Create a payment link for the given user and SKU.
        
        Args:
            user_id: User identifier
            sku_id: SKU identifier
            
            
        Returns:
            PaymentLinkResponse containing payment link details or None if failed        
        """
        try:
            payment_dao = PaymentDAO()
            
            # Expire all previous unpaid links for this user first
            
          
            pending_payments = payment_dao.get_user_purchases(user_id)
            for payment in pending_payments:
                if payment.status == PaymentStatus.PENDING:
                    # Expire via Razorpay API
                    await self.expire_payment_link(payment.payment_link_id)
                    # Database will be updated by expire_payment_link method
            
            # Get SKU details from database using DAO
            sku = payment_dao.get_sku_by_id(sku_id)
            
            if not sku:
                logger.error(f"SKU not found: {sku_id}")
                return None
            
            # Prepare payment link request
            timestamp = int(time.time())
            # Create shorter reference_id to fit 40 char limit
            short_user_id = user_id.replace('-', '')[:8]  # Take first 8 chars of UUID
            short_sku = sku_id[:6]  # Take first 6 chars of SKU
            reference_id = f"{short_user_id}_{short_sku}_{timestamp}"
            
            # Calculate expiry time (18 minutes from now)
            expire_by = int((datetime.now(timezone.utc) + timedelta(minutes=18)).timestamp())
            
            payment_data = {
                "amount": int(sku.amount * 100),  # Convert to paise
                "currency": "INR",
                "accept_partial": False,
                "reference_id": reference_id,
                "description": f"Payment for {sku.name}",
                "callback_url": f"{self.settings.CALLBACK_BASE_URL}/kundli/redirect?user_id={user_id}",
                "callback_method": "get",
                "expire_by": expire_by,
                "notes": {
                    "user_id": user_id,
                    "sku_id": sku_id,
                    "sku_name": sku.name
                }
            }
            
            # Create payment link via Razorpay API
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/payment_links",
                    json=payment_data,
                    headers=self.headers,
                    timeout=10.0
                )
                
                if response.status_code == 200:
                    payment_link_data = response.json()
                    
                    # Save to database using DAO
                    payment_dao.create_user_purchase(
                        user_id=user_id,
                        sku_id=sku_id,
                        payment_link_id=payment_link_data["id"],
                        status=PaymentStatus.PENDING
                    )
                    
                    logger.info(f"Payment link created for user {user_id}, SKU {sku_id}")
                    return PaymentLinkResponse(
                        payment_url=payment_link_data["short_url"],
                        payment_link_id=payment_link_data["id"],
                        status=payment_link_data["status"]
                    )
                else:
                    logger.error(f"Failed to create payment link: {response.status_code} - {response.text}")
                    return None
                    
        except Exception as e:
            logger.error(f"Error creating payment link: {str(e)}")
            return None

    async def check_payment_status(
        self, 
        payment_link_id: str
    ) -> Optional[Dict]:
        """
        Check the status of a payment link.
        
        Args:
            payment_link_id: Payment link identifier
            
        Returns:
            Dict: Payment data or None if failed
        """
        try:
            payment_dao = PaymentDAO()
            
            # Get payment link details from database using DAO
            user_purchase = payment_dao.get_payment_by_link_id(payment_link_id)
            
            if not user_purchase:
                logger.error(f"Payment link not found in database: {payment_link_id}")
                return None
            
            # Check status via Razorpay API
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/payment_links/{payment_link_id}",
                    headers=self.headers,
                    timeout=10.0
                )
                
                if response.status_code == 200:
                    payment_data = response.json()
                    razorpay_status = payment_data.get("status", "unknown")
                    
                    # Map Razorpay status to PaymentStatus enum values
                    if razorpay_status == "paid":
                        new_status = PaymentStatus.PAID
                    elif razorpay_status in ("expired", "cancelled"):
                        new_status = PaymentStatus.EXPIRED
                    elif razorpay_status in ("pending", "created", "issued"):
                        new_status = PaymentStatus.PENDING
                    else:
                        new_status = PaymentStatus.FAILED
                    
                    # Update database status if changed using DAO
                    if user_purchase.status != new_status:
                        payment_dao.update_payment_status(payment_link_id, new_status)
                        logger.info(f"Updated payment status for {payment_link_id}: {new_status}")
                    
                    return payment_data
                else:
                    logger.error(f"Failed to check payment status: {response.status_code} - {response.text}")
                    return None
                    
        except Exception as e:
            logger.error(f"Error checking payment status: {str(e)}")
            return None

    async def expire_payment_link(self, payment_link_id: str) -> bool:
        """
        Expire a single payment link via Razorpay API.
        
        Args:
            payment_link_id: Payment link identifier
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Cancel payment link via Razorpay API
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/payment_links/{payment_link_id}/cancel",
                    headers=self.headers,
                    timeout=10.0
                )
                
                if response.status_code == 200:
                    # Confirm the status with Razorpay before updating database
                    payment_data = response.json()
                    razorpay_status = payment_data.get("status", "unknown")
                    
                    if razorpay_status in ("expired", "cancelled"):
                        # Only update database if Razorpay confirms the status
                        payment_dao = PaymentDAO()
                        payment_dao.update_payment_status(payment_link_id, PaymentStatus.EXPIRED)
                        logger.info(f"Expired payment link {payment_link_id} (confirmed by Razorpay)")
                        return True
                    else:
                        logger.warning(f"Payment link {payment_link_id} not expired by Razorpay (status: {razorpay_status})")
                        return False
                else:
                    logger.warning(f"Failed to expire payment link {payment_link_id}: {response.status_code}")
                    return False
                    
        except Exception as e:
            logger.error(f"Error expiring payment link {payment_link_id}: {e}")
            return False 