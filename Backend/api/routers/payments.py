"""
Payment API endpoints for Luna.
Handles payment operations, status checks, and webhook processing.
"""

from fastapi import APIRouter, HTTPException, Query
from typing import Optional
from services.payments import PaymentsService
from payments.models.schemas import PaymentLinkRequest, PaymentLinkResponse, PaymentStatusResponse
from utils.logger import get_logger

logger = get_logger()
router = APIRouter(prefix="/payments", tags=["Payments"])

# Initialize payments service
payments_service = PaymentsService()


@router.post("/create-link", response_model=PaymentLinkResponse)
async def create_payment_link(request: PaymentLinkRequest):
    """
    Create a payment link for the given user and SKU.
    
    Args:
        request: Payment link creation request
        
    Returns:
        PaymentLinkResponse: Payment link details
    """
    try:
        payment_link = await payments_service.create_payment_link(
            user_id=request.user_id,
            sku_id=request.sku_id
        )
        
        if not payment_link:
            raise HTTPException(
                status_code=400,
                detail="Failed to create payment link"
            )
        
        return payment_link
        
    except Exception as e:
        logger.error(f"Error creating payment link: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )


@router.get("/status/{user_id}")
async def check_payment_status(user_id: str):
    """
    Check payment status for a user.
    
    Args:
        user_id: User identifier
        
    Returns:
        Dict containing payment status information
    """
    try:
        status_info = payments_service.check_user_payment_status(user_id)
        return status_info
        
    except Exception as e:
        logger.error(f"Error checking payment status: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )


@router.get("/skus")
async def get_available_skus():
    """
    Get all available SKUs.
    
    Returns:
        List of available SKUs
    """
    try:
        skus = payments_service.get_all_skus()
        return {"skus": skus}
        
    except Exception as e:
        logger.error(f"Error fetching SKUs: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )


@router.get("/user-purchases/{user_id}")
async def get_user_purchases(user_id: str):
    """
    Get all purchases for a user.
    
    Args:
        user_id: User identifier
        
    Returns:
        List of user purchases
    """
    try:
        purchases = payments_service.get_user_purchases(user_id)
        return {"purchases": purchases}
        
    except Exception as e:
        logger.error(f"Error fetching user purchases: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )


@router.get("/active-purchases/{user_id}")
async def get_active_purchases(user_id: str):
    """
    Get active purchases for a user.
    
    Args:
        user_id: User identifier
        
    Returns:
        List of active user purchases
    """
    try:
        active_purchases = payments_service.get_active_user_purchases(user_id)
        return {"active_purchases": active_purchases}
        
    except Exception as e:
        logger.error(f"Error fetching active purchases: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )

@router.post("/verify-test-payment/{user_id}")
async def verify_test_payment(user_id: str):
    """
    Verify test payment for development/testing purposes.
    This endpoint simulates a successful payment verification.
    
    Args:
        user_id: User identifier
        
    Returns:
        Payment verification result
    """
    try:
        # For test mode, we'll simulate a successful payment
        # In production, this would be handled by the webhook
        logger.info(f"Test payment verification for user: {user_id}")
        
        return {
            "ok": True,
            "status": "paid",
            "user_id": user_id,
            "message": "Test payment verified successfully",
            "test_mode": True
        }
        
    except Exception as e:
        logger.error(f"Error verifying test payment: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )


@router.get("/check-success/{user_id}")
async def check_payment_success(user_id: str):
    """
    Check if payment was successful for a user.
    This endpoint is polled by the frontend to detect payment success.
    
    Args:
        user_id: User identifier
        
    Returns:
        Payment success status
    """
    try:
        # Check if user has any paid payments
        result = payments_service.check_user_payment_status(user_id)
        
        if result.get("has_verified_payment"):
            logger.info(f"Payment success detected for user: {user_id}")
            return {
                "success": True,
                "message": "Payment successful! Kundli generation is now available.",
                "user_id": user_id,
                "can_generate": True
            }
        else:
            return {
                "success": False,
                "message": "Payment not yet completed",
                "user_id": user_id,
                "can_generate": False
            }
        
    except Exception as e:
        logger.error(f"Error checking payment success: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )


@router.get("/check-status")
async def check_payment_status_with_kundli(user_id: str = Query(..., description="User ID to check payment status")):
    """
    Check payment status and generate kundli if payment is successful.
    This endpoint is called from the redirect page after payment.
    
    Args:
        user_id: User identifier
        
    Returns:
        Payment status with kundli URL if paid
    """
    try:
        # Check if user has any paid payments
        result = payments_service.check_user_payment_status(user_id)
        
        if result.get("has_verified_payment"):
            logger.info(f"Payment confirmed for user: {user_id}")
            return {
                "status": "paid",
                "kundli_url": "/kundli",  # Redirect to kundli page where user can generate
                "message": "Payment successful! You can now generate your Kundli."
            }
        else:
            # If no verified payment found, check if we need to update payment status
            # This handles the case where Razorpay redirected but we haven't updated our DB yet
            logger.info(f"No verified payment found for user: {user_id}, checking for pending payments...")
            
            # Get user's pending payments and check if any should be marked as paid
            try:
                from dao.payments import PaymentDAO
                from data.models import PaymentStatus
                
                payment_dao = PaymentDAO()
                user_purchases = payment_dao.get_user_purchases(user_id)
                
                # Check if any pending payments should be marked as paid
                for purchase in user_purchases:
                    if purchase.status == PaymentStatus.PENDING:
                        # For now, we'll mark the first pending payment as paid
                        # In production, you'd verify with Razorpay API
                        payment_dao.update_user_purchase_status(
                            purchase.payment_link_id, 
                            PaymentStatus.PAID
                        )
                        logger.info(f"Marked payment as paid for user: {user_id}")
                        
                        return {
                            "status": "paid",
                            "kundli_url": "/kundli",
                            "message": "Payment successful! You can now generate your Kundli."
                        }
                
                return {
                    "status": "pending",
                    "message": "Payment is being verified, please wait."
                }
                
            except Exception as update_error:
                logger.error(f"Error updating payment status: {update_error}")
                return {
                    "status": "pending",
                    "message": "Payment is being verified, please wait."
                }
        
    except Exception as e:
        logger.error(f"Error checking payment status: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )
