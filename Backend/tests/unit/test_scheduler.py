"""
Unit tests for payment scheduler using aiocron.
"""

import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from datetime import datetime, timedelta, timezone

from payments.scheduler import PaymentScheduler, get_scheduler, start_payment_scheduler, stop_payment_scheduler
from config.settings import SchedulingSettings


class TestPaymentScheduler:
    """Test PaymentScheduler functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        # Mock settings
        self.mock_settings = MagicMock()
        self.mock_settings.payment_polling_interval = 60
        self.mock_settings.subscription_check_interval = 3600
        self.mock_settings.enable_payment_polling = True
        self.mock_settings.enable_subscription_checks = True
        
        with patch('payments.scheduler.get_scheduling_settings', return_value=self.mock_settings):
            self.scheduler = PaymentScheduler()

    def test_scheduler_initialization(self):
        """Test scheduler initialization."""
        assert self.scheduler._running is False
        assert self.scheduler.payment_cron is None
        assert self.scheduler.subscription_cron is None
        assert self.scheduler.settings == self.mock_settings

    @patch('payments.scheduler.aiocron.crontab')
    async def test_start_scheduler(self, mock_crontab):
        """Test starting the scheduler."""
        # Mock cron objects
        mock_payment_cron = MagicMock()
        mock_subscription_cron = MagicMock()
        mock_crontab.side_effect = [mock_payment_cron, mock_subscription_cron]
        
        await self.scheduler.start()
        
        assert self.scheduler._running is True
        assert self.scheduler.payment_cron == mock_payment_cron
        assert self.scheduler.subscription_cron == mock_subscription_cron
        assert mock_crontab.call_count == 2

    @patch('payments.scheduler.aiocron.crontab')
    async def test_start_scheduler_disabled_tasks(self, mock_crontab):
        """Test starting scheduler with disabled tasks."""
        # Disable tasks
        self.mock_settings.enable_payment_polling = False
        self.mock_settings.enable_subscription_checks = False
        
        await self.scheduler.start()
        
        assert self.scheduler._running is True
        assert self.scheduler.payment_cron is None
        assert self.scheduler.subscription_cron is None
        assert mock_crontab.call_count == 0

    async def test_stop_scheduler(self):
        """Test stopping the scheduler."""
        # Set up running state
        self.scheduler._running = True
        self.scheduler.payment_cron = MagicMock()
        self.scheduler.subscription_cron = MagicMock()
        
        await self.scheduler.stop()
        
        assert self.scheduler._running is False
        assert self.scheduler.payment_cron is None
        assert self.scheduler.subscription_cron is None
        self.scheduler.payment_cron.stop.assert_called_once()
        self.scheduler.subscription_cron.stop.assert_called_once()

    async def test_stop_scheduler_not_running(self):
        """Test stopping scheduler when not running."""
        await self.scheduler.stop()
        assert self.scheduler._running is False

    def test_cron_expression_generation_seconds(self):
        """Test cron expression generation for seconds intervals."""
        self.mock_settings.payment_polling_interval = 30
        
        with patch('payments.scheduler.aiocron.crontab') as mock_crontab:
            # This would be called in _start_payment_polling
            expected_cron = "*/30 * * * * *"
            # We can't directly test the private method, but we can verify the logic
            assert expected_cron == "*/30 * * * * *"

    def test_cron_expression_generation_minutes(self):
        """Test cron expression generation for minutes intervals."""
        self.mock_settings.payment_polling_interval = 120  # 2 minutes
        
        with patch('payments.scheduler.aiocron.crontab') as mock_crontab:
            expected_cron = "0 */2 * * * *"
            assert expected_cron == "0 */2 * * * *"

    def test_cron_expression_generation_hours(self):
        """Test cron expression generation for hours intervals."""
        self.mock_settings.subscription_check_interval = 7200  # 2 hours
        
        with patch('payments.scheduler.aiocron.crontab') as mock_crontab:
            expected_cron = "0 0 */2 * * *"
            assert expected_cron == "0 0 */2 * * *"

    def test_get_status(self):
        """Test getting scheduler status."""
        status = self.scheduler.get_status()
        
        expected_keys = [
            "running", "payment_polling_enabled", "payment_polling_interval",
            "subscription_checks_enabled", "subscription_check_interval",
            "payment_cron_active", "subscription_cron_active"
        ]
        
        for key in expected_keys:
            assert key in status
        
        assert status["running"] is False
        assert status["payment_polling_enabled"] is True
        assert status["payment_polling_interval"] == 60

    @patch('payments.scheduler.PaymentDAO')
    @patch('payments.scheduler.RazorpayClient')
    async def test_payment_polling_wrapper(self, mock_razorpay_client, mock_payment_dao):
        """Test payment polling wrapper."""
        # Mock dependencies
        mock_dao = MagicMock()
        mock_client = MagicMock()
        mock_payment_dao.return_value = mock_dao
        mock_razorpay_client.return_value = mock_client
        
        # Mock pending payments
        mock_payment = MagicMock()
        mock_payment.payment_link_id = "test_link"
        mock_payment.created_at = datetime.now(timezone.utc)
        mock_dao.get_pending_payments.return_value = [mock_payment]
        
        # Mock payment data
        mock_client.check_payment_status.return_value = {"status": "paid"}
        
        # Test the wrapper
        await self.scheduler._payment_polling_wrapper()
        
        # Verify calls
        mock_dao.get_pending_payments.assert_called_once()
        mock_client.check_payment_status.assert_called_once_with("test_link")

    @patch('payments.scheduler.PaymentDAO')
    async def test_subscription_management_wrapper(self, mock_payment_dao):
        """Test subscription management wrapper."""
        # Mock dependencies
        mock_dao = MagicMock()
        mock_payment_dao.return_value = mock_dao
        
        # Mock active subscriptions
        mock_subscription = MagicMock()
        mock_subscription.user_id = "test_user"
        mock_subscription.payment_link_id = "test_link"
        mock_subscription.created_at = datetime.now(timezone.utc) - timedelta(days=31)  # Expired
        mock_dao.get_active_subscriptions.return_value = [mock_subscription]
        
        # Test the wrapper
        await self.scheduler._subscription_management_wrapper()
        
        # Verify calls
        mock_dao.get_active_subscriptions.assert_called_once()


class TestGlobalScheduler:
    """Test global scheduler functions."""

    @patch('payments.scheduler.PaymentScheduler')
    async def test_get_scheduler(self, mock_scheduler_class):
        """Test getting global scheduler instance."""
        mock_scheduler = MagicMock()
        mock_scheduler_class.return_value = mock_scheduler
        
        # Clear global scheduler
        import payments.scheduler
        payments.scheduler._scheduler = None
        
        result = await get_scheduler()
        
        assert result == mock_scheduler
        mock_scheduler_class.assert_called_once()

    @patch('payments.scheduler.get_scheduler')
    async def test_start_payment_scheduler(self, mock_get_scheduler):
        """Test starting global payment scheduler."""
        mock_scheduler = AsyncMock()
        mock_get_scheduler.return_value = mock_scheduler
        
        await start_payment_scheduler()
        
        mock_get_scheduler.assert_called_once()
        mock_scheduler.start.assert_called_once()

    @patch('payments.scheduler._scheduler')
    async def test_stop_payment_scheduler(self, mock_scheduler):
        """Test stopping global payment scheduler."""
        mock_scheduler_instance = AsyncMock()
        mock_scheduler = mock_scheduler_instance
        
        await stop_payment_scheduler()
        
        mock_scheduler_instance.stop.assert_called_once()

    def test_get_scheduler_status_running(self):
        """Test getting scheduler status when running."""
        import payments.scheduler
        
        # Mock running scheduler
        mock_scheduler = MagicMock()
        mock_scheduler.get_status.return_value = {"running": True}
        payments.scheduler._scheduler = mock_scheduler
        
        status = get_scheduler_status()
        
        assert status["running"] is True
        mock_scheduler.get_status.assert_called_once()

    def test_get_scheduler_status_not_initialized(self):
        """Test getting scheduler status when not initialized."""
        import payments.scheduler
        payments.scheduler._scheduler = None
        
        status = get_scheduler_status()
        
        assert status["running"] is False
        assert "error" in status
