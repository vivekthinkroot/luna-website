"""
Payment scheduling service using aiocron.
Handles scheduled background tasks for payment polling and subscription management.
"""

import asyncio
from typing import Optional

import aiocron
from config.settings import get_scheduling_settings
from payments.background_tasks import poll_payment_status_once, run_subscription_manager_once
from utils.logger import get_logger

logger = get_logger()


class PaymentScheduler:
    """Scheduler for payment-related background tasks using aiocron."""
    
    def __init__(self):
        self.settings = get_scheduling_settings()
        self.payment_cron: Optional[aiocron.Cron] = None
        self.subscription_cron: Optional[aiocron.Cron] = None
        self._running = False
    
    async def start(self):
        """Start the payment scheduler with configured tasks."""
        if self._running:
            logger.warning("Payment scheduler is already running")
            return
        
        logger.info("Starting payment scheduler...")
        self._running = True
        
        # Start payment polling task if enabled
        if self.settings.enable_payment_polling:
            await self._start_payment_polling()
        
        # Start subscription management task if enabled
        if self.settings.enable_subscription_checks:
            await self._start_subscription_management()
        
        logger.info("Payment scheduler started successfully")
    
    async def stop(self):
        """Stop the payment scheduler."""
        if not self._running:
            logger.warning("Payment scheduler is not running")
            return
        
        logger.info("Stopping payment scheduler...")
        self._running = False
        
        # Stop payment polling task
        if self.payment_cron:
            self.payment_cron.stop()
            self.payment_cron = None
        
        # Stop subscription management task
        if self.subscription_cron:
            self.subscription_cron.stop()
            self.subscription_cron = None
        
        logger.info("Payment scheduler stopped successfully")
    
    async def _start_payment_polling(self):
        """Start the payment polling task with configured interval."""
        interval_seconds = self.settings.payment_polling_interval
        
        # Convert seconds to cron expression (every N seconds)
        if interval_seconds < 60:
            # For intervals less than 60 seconds, use every N seconds
            cron_expression = f"*/{interval_seconds} * * * * *"
        else:
            # For intervals >= 60 seconds, convert to minutes/hours
            minutes = interval_seconds // 60
            if minutes < 60:
                cron_expression = f"0 */{minutes} * * * *"
            else:
                hours = minutes // 60
                cron_expression = f"0 0 */{hours} * * *"
        
        logger.info(f"Starting payment polling task with cron: {cron_expression}")
        
        # Create cron job for payment polling
        self.payment_cron = aiocron.crontab(
            cron_expression,
            func=self._payment_polling_wrapper,
            start=True
        )
    
    async def _start_subscription_management(self):
        """Start the subscription management task with configured interval."""
        interval_seconds = self.settings.subscription_check_interval
        
        # Convert seconds to cron expression
        if interval_seconds < 60:
            cron_expression = f"*/{interval_seconds} * * * * *"
        else:
            minutes = interval_seconds // 60
            if minutes < 60:
                cron_expression = f"0 */{minutes} * * * *"
            else:
                hours = minutes // 60
                cron_expression = f"0 0 */{hours} * * *"
        
        logger.info(f"Starting subscription management task with cron: {cron_expression}")
        
        # Create cron job for subscription management
        self.subscription_cron = aiocron.crontab(
            cron_expression,
            func=self._subscription_management_wrapper,
            start=True
        )
    
    async def _payment_polling_wrapper(self):
        """Wrapper for payment polling task to handle errors gracefully."""
        try:
            logger.debug("Running scheduled payment polling task")
            # Use the existing background task function for one execution
            await self._run_payment_polling_once()
        except Exception as e:
            logger.error(f"Error in scheduled payment polling task: {e}")
    
    async def _subscription_management_wrapper(self):
        """Wrapper for subscription management task to handle errors gracefully."""
        try:
            logger.debug("Running scheduled subscription management task")
            # Use the existing background task function for one execution
            await self._run_subscription_management_once()
        except Exception as e:
            logger.error(f"Error in scheduled subscription management task: {e}")
    
    async def _run_payment_polling_once(self):
        """Run payment polling task once using existing background task logic."""
        # Use the reusable function from background_tasks
        await poll_payment_status_once()
    
    async def _run_subscription_management_once(self):
        """Run subscription management task once using existing background task logic."""
        # Use the reusable function from background_tasks
        await run_subscription_manager_once()
    
    def is_running(self) -> bool:
        """Check if the scheduler is running."""
        return self._running
    
    def get_status(self) -> dict:
        """Get the current status of the scheduler."""
        return {
            "running": self._running,
            "payment_polling_enabled": self.settings.enable_payment_polling,
            "payment_polling_interval": self.settings.payment_polling_interval,
            "subscription_checks_enabled": self.settings.enable_subscription_checks,
            "subscription_check_interval": self.settings.subscription_check_interval,
            "payment_cron_active": self.payment_cron is not None,
            "subscription_cron_active": self.subscription_cron is not None
        }


# Global scheduler instance
_scheduler: Optional[PaymentScheduler] = None


async def get_scheduler() -> PaymentScheduler:
    """Get the global scheduler instance."""
    global _scheduler
    if _scheduler is None:
        _scheduler = PaymentScheduler()
    return _scheduler


async def start_payment_scheduler():
    """Start the global payment scheduler."""
    scheduler = await get_scheduler()
    await scheduler.start()


async def stop_payment_scheduler():
    """Stop the global payment scheduler."""
    global _scheduler
    if _scheduler:
        await _scheduler.stop()
        _scheduler = None


def get_scheduler_status() -> dict:
    """Get the status of the global scheduler."""
    global _scheduler
    if _scheduler:
        return _scheduler.get_status()
    return {"running": False, "error": "Scheduler not initialized"}
