"""
Payments service for Luna.
Handles payment operations, webhook processing, and coordinates between DAO and external payment providers.
"""

import hmac
import hashlib
from typing import Optional, Dict, Any
from datetime import datetime, timezone

from dao.payments import PaymentDAO
from payments.models.schemas import PaymentLinkResponse
from payments.razorpay_client import RazorpayClient
from data.models import PaymentStatus
from config.settings import get_settings
from utils.logger import get_logger

logger = get_logger()


class PaymentsService:
    """Service layer for payment operations."""
    
    def __init__(self):
        self.payment_dao = PaymentDAO()
        self.razorpay_client = RazorpayClient()
        self.settings = get_settings()
        self.webhook_secret = "1234567890"  # Live mode webhook secret
    
    def verify_razorpay_signature(self, body: bytes, signature: str) -> bool:
        """
        Verify Razorpay webhook signature using HMAC SHA256.
        
        Args:
            body: Raw request body
            signature: X-Razorpay-Signature header value
            
        Returns:
            bool: True if signature is valid, False otherwise
        """
        try:
            if not signature:
                logger.warning("No signature provided in webhook request")
                return False
            
            # Create HMAC signature
            expected_signature = hmac.new(
                self.webhook_secret.encode('utf-8'),
                body,
                hashlib.sha256
            ).hexdigest()
            
            # Compare signatures using constant-time comparison
            is_valid = hmac.compare_digest(signature, expected_signature)
            
            if is_valid:
                logger.info("✅ Razorpay webhook signature verified successfully")
            else:
                logger.warning("❌ Razorpay webhook signature verification failed")
                
            return is_valid
            
        except Exception as e:
            logger.error(f"Error verifying Razorpay signature: {e}")
            return False

    async def process_razorpay_webhook(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process Razorpay webhook payload and update payment status.
        
        Args:
            payload: Raw webhook payload from Razorpay
            
        Returns:
            Dict containing processing result
        """
        try:
            # Check if this is a payment.captured event
            event = payload.get("event")
            if event != "payment.captured":
                logger.info(f"Ignoring non-payment event: {event}")
                return {"ok": True, "message": f"Ignored event: {event}"}
            
            # Extract payment details from webhook payload
            payment_entity = payload.get("payload", {}).get("payment", {}).get("entity", {})
            payment_id = payment_entity.get("id")
            payment_link_id = payment_entity.get("payment_link_id")
            
            # Handle direct payment button payments (test mode)
            if not payment_link_id and payment_id:
                logger.info(f"Processing direct payment button payment: {payment_id}")
                # For test mode, we'll create a mock payment record
                # In production, you'd want to handle this differently
                return {
                    "ok": True,
                    "status": "paid",
                    "payment_id": payment_id,
                    "message": "Payment verified successfully (test mode)"
                }
            
            if not payment_link_id:
                logger.warning("No payment link ID found in Razorpay webhook payload")
                return {"ok": False, "error": "No payment link ID"}
            
            # Update payment status to PAID
            updated_payment = self.payment_dao.update_payment_status(payment_link_id, PaymentStatus.PAID)
            
            if updated_payment:
                logger.info(f"✅ Payment {payment_link_id} marked as PAID for user {updated_payment.user_id}")
                return {
                    "ok": True, 
                    "status": "paid",
                    "payment_link_id": payment_link_id,
                    "user_id": updated_payment.user_id,
                    "message": "Payment verified successfully"
                }
            else:
                logger.warning(f"Payment {payment_link_id} not found in database")
                return {"ok": False, "error": "Payment not found"}
                
        except Exception as e:
            logger.error(f"Error processing Razorpay webhook: {e}")
            return {"ok": False, "error": str(e)}
    
    def _map_razorpay_status(self, razorpay_status: str) -> PaymentStatus:
        """
        Map Razorpay payment status to internal PaymentStatus enum.
        
        Args:
            razorpay_status: Status string from Razorpay
            
        Returns:
            PaymentStatus enum value
        """
        if razorpay_status == "paid":
            return PaymentStatus.PAID
        elif razorpay_status in ("expired", "cancelled"):
            return PaymentStatus.EXPIRED
        elif razorpay_status in ("pending", "created", "issued"):
            return PaymentStatus.PENDING
        else:
            return PaymentStatus.FAILED
    
    async def create_payment_link(self, user_id: str, sku_id: str) -> Optional[PaymentLinkResponse]:
        """
        Create a payment link for the given user and SKU.
        
        Args:
            user_id: User identifier
            sku_id: SKU identifier
            
        Returns:
            Payment link data or None if failed
        """
        try:
            # Validate SKU exists
            sku = self.payment_dao.get_sku_by_id(sku_id)
            if not sku:
                logger.error(f"SKU not found: {sku_id}")
                return None
            
            # Create payment link via Razorpay client
            payment_link_data = await self.razorpay_client.create_payment_link(user_id, sku_id)
            
            if payment_link_data:
                logger.info(f"Payment link created for user {user_id}, SKU {sku_id}")
                return payment_link_data
            else:
                logger.error(f"Failed to create payment link for user {user_id}, SKU {sku_id}")
                return None
                
        except Exception as e:
            logger.error(f"Error creating payment link: {str(e)}")
            return None
    
    def get_user_purchases(self, user_id: str) -> list:
        """
        Get all purchases for a user.
        
        Args:
            user_id: User identifier
            
        Returns:
            List of user purchases
        """
        return self.payment_dao.get_user_purchases(user_id)
    
    def get_active_user_purchases(self, user_id: str) -> list:
        """
        Get active purchases for a user.
        
        Args:
            user_id: User identifier
            
        Returns:
            List of active user purchases
        """
        return self.payment_dao.get_active_user_purchases(user_id)
    
    def get_sku_by_id(self, sku_id: str) -> Optional[Any]:
        """
        Get SKU by ID.
        
        Args:
            sku_id: SKU identifier
            
        Returns:
            SKU object or None if not found
        """
        return self.payment_dao.get_sku_by_id(sku_id)
    
    def get_all_skus(self) -> list:
        """
        Get all available SKUs.
        
        Returns:
            List of all SKUs
        """
        return self.payment_dao.get_all_skus()
    
    def check_user_payment_status(self, user_id: str) -> Dict[str, Any]:
        """
        Check if user has any verified payments.
        
        Args:
            user_id: User identifier
            
        Returns:
            Dict containing payment status information
        """
        try:
            # Get active purchases for the user
            active_purchases = self.payment_dao.get_active_user_purchases(user_id)
            
            if active_purchases:
                # User has verified payments
                return {
                    "has_verified_payment": True,
                    "active_purchases": len(active_purchases),
                    "purchases": [
                        {
                            "sku_id": purchase.sku_id,
                            "status": purchase.status.value,
                            "valid_till": purchase.valid_till.isoformat() if purchase.valid_till else None,
                            "created_at": purchase.created_at.isoformat()
                        }
                        for purchase in active_purchases
                    ]
                }
            else:
                # Check if user has any pending payments
                all_purchases = self.payment_dao.get_user_purchases(user_id)
                pending_purchases = [p for p in all_purchases if p.status == PaymentStatus.PENDING]
                
                return {
                    "has_verified_payment": False,
                    "active_purchases": 0,
                    "pending_purchases": len(pending_purchases),
                    "purchases": []
                }
                
        except Exception as e:
            logger.error(f"Error checking user payment status: {e}")
            return {
                "has_verified_payment": False,
                "error": str(e)
            }
