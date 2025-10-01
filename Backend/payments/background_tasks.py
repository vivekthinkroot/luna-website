"""
Background tasks for payment operations.
"""

import asyncio
from datetime import datetime, timedelta, timezone

from data.models import PaymentStatus
from dao.payments import PaymentDAO
from payments.razorpay_client import RazorpayClient
from utils.logger import get_logger

logger = get_logger()


async def poll_payment_status_once():
    """Poll payment status once (core logic without loop)."""
    payment_dao = PaymentDAO()
    client = RazorpayClient()
    
    try:
        # Get all non-final status payment links using DAO
        pending_payments = payment_dao.get_pending_payments()
        
        now = datetime.now(timezone.utc)
        
        for payment in pending_payments:
            try:
                # Fetch latest status from Razorpay
                payment_data = await client.check_payment_status(payment.payment_link_id)
                
                if payment_data:
                    # Only update status based on Razorpay API response
                    # The check_payment_status method already handles status updates
                    razorpay_status = payment_data.get("status", "unknown")
                    logger.debug(f"Payment {payment.payment_link_id} status from Razorpay: {razorpay_status}")
                    
                    # Note: Status updates are handled by razorpay_client.check_payment_status()
                    # which calls Razorpay API and updates database accordingly

            except Exception as e:
                logger.error(f"Error processing payment link {payment.payment_link_id}: {e}")
                continue

        logger.info(f"✅ Checked {len(pending_payments)} links at {now.isoformat()}")

    except Exception as e:
        logger.error(f"⚠️ Payment polling task error: {e}")


async def poll_payment_status_every_n_seconds(n: int = 60):
    """Background task to poll payment status every n seconds."""
    logger.info("Starting payment status polling background task")
    
    while True:
        await poll_payment_status_once()
        await asyncio.sleep(n)


async def poll_payment_status_fast():
    """Background task to poll payment status every 5 seconds for real-time updates."""
    logger.info("Starting fast payment status polling (every 5 seconds)")
    
    while True:
        await poll_payment_status_once()
        await asyncio.sleep(5)  # Check every 5 seconds


async def check_payment_success_and_notify():
    """Check for successful payments and trigger notifications."""
    payment_dao = PaymentDAO()
    
    try:
        # Get all payments that just became PAID (recently updated)
        now = datetime.now(timezone.utc)
        recent_threshold = now - timedelta(minutes=1)  # Check payments updated in last minute
        
        from data.db import get_session
        from data.models import TUserPurchase
        from sqlmodel import select, and_
        
        with get_session() as db:
            # Get recently paid payments
            result = db.exec(
                select(TUserPurchase).where(
                    and_(
                        TUserPurchase.status == PaymentStatus.PAID,
                        TUserPurchase.updated_at >= recent_threshold
                    )
                )
            )
            recent_payments = result.all()
            
            for payment in recent_payments:
                logger.info(f"🎉 Payment successful for user {payment.user_id}! Payment ID: {payment.payment_link_id}")
                
                # Here you can add notification logic:
                # - Send email
                # - Send SMS
                # - Update frontend via WebSocket
                # - Store notification in database
                
                # For now, we'll just log the success
                logger.info(f"✅ Kundli generation now available for user {payment.user_id}")
                
    except Exception as e:
        logger.error(f"⚠️ Payment success notification error: {e}")


async def payment_success_monitor():
    """Background task to monitor payment success and trigger notifications."""
    logger.info("Starting payment success monitor (every 5 seconds)")
    
    while True:
        await check_payment_success_and_notify()
        await asyncio.sleep(5)  # Check every 5 seconds


async def run_subscription_manager_once() -> None:
    """Run the subscription manager once (core logic without loop)."""
    payment_dao = PaymentDAO()
    
    try:
        # Get active paid subscriptions using DAO
        active_subscriptions = payment_dao.get_active_subscriptions()
        
        now = datetime.now(timezone.utc)
        
        for subscription in active_subscriptions:
            # Use valid_till field to determine subscription expiry
            # valid_till is set when payment becomes PAID based on SKU validity
            if subscription.valid_till:
                days_until_expiry = (subscription.valid_till - now).days
            else:
                # Fallback: calculate based on created_at + 30 days (legacy)
                expiry_date = subscription.created_at + timedelta(days=30)
                days_until_expiry = (expiry_date - now).days
            
            # Send notifications for different expiry periods
            if days_until_expiry == 7:
                logger.info(f"Subscription expiring in 7 days for user {subscription.user_id}")
            elif days_until_expiry == 3:
                logger.info(f"Subscription expiring in 3 days for user {subscription.user_id}")
            elif days_until_expiry == 1:
                logger.info(f"Subscription expiring in 1 day for user {subscription.user_id}")
            elif days_until_expiry <= 0:
                # Subscription has expired based on valid_till
                # DO NOT change payment status - that should only be changed by Razorpay
                # The payment status remains PAID since the user actually paid
                logger.info(f"Subscription expired for user {subscription.user_id} (valid_till: {subscription.valid_till})")
        
        logger.info("✅ Subscription manager check completed")
        
    except Exception as e:
        logger.error(f"⚠️ Subscription manager error: {e}")


async def run_subscription_manager() -> None:
    """Run the subscription manager background task."""
    logger.info("Starting subscription manager background task")
    
    while True:
        await run_subscription_manager_once()
        # Run every 24 hours
        await asyncio.sleep(24 * 60 * 60) 