"""
Unit tests for payment system components.
Tests PaymentDAO, RazorpayClient, and background tasks.
"""

import pytest
import asyncio
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, patch, MagicMock

from dao.payments import PaymentDAO, Sku, UserPurchase
from data.models import PaymentStatus, TSku, TUserPurchase
from payments.razorpay_client import RazorpayClient
from payments.background_tasks import poll_payment_status_every_n_seconds, run_subscription_manager


class TestPaymentDAO:
    """Test PaymentDAO functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.payment_dao = PaymentDAO()
        self.test_user_id = "test-user-123"
        self.test_sku_id = "BASIC_HOROSCOPE"
        self.test_payment_link_id = "plink_test_123"

    @patch('dao.payments.get_session')
    def test_get_all_skus(self, mock_get_session):
        """Test getting all SKUs."""
        # Mock database session
        mock_db = MagicMock()
        mock_get_session.return_value.__enter__.return_value = mock_db
        
        # Mock SKU data
        mock_sku = MagicMock()
        mock_sku.id = 1
        mock_sku.name = "Basic Horoscope"
        mock_sku.sku_id = "BASIC_HOROSCOPE"
        mock_sku.amount = 99.0
        mock_sku.validity = 30
        mock_sku.created_at = datetime.now(timezone.utc)
        mock_sku.updated_at = datetime.now(timezone.utc)
        
        mock_db.exec.return_value.all.return_value = [mock_sku]
        
        # Test
        result = self.payment_dao.get_all_skus()
        
        # Assertions
        assert len(result) == 1
        assert result[0].sku_id == "BASIC_HOROSCOPE"
        assert result[0].name == "Basic Horoscope"
        assert result[0].amount == 99.0

    @patch('dao.payments.get_session')
    def test_get_sku_by_id(self, mock_get_session):
        """Test getting SKU by ID."""
        # Mock database session
        mock_db = MagicMock()
        mock_get_session.return_value.__enter__.return_value = mock_db
        
        # Mock SKU data
        mock_sku = MagicMock()
        mock_sku.id = 1
        mock_sku.name = "Basic Horoscope"
        mock_sku.sku_id = "BASIC_HOROSCOPE"
        mock_sku.amount = 99.0
        mock_sku.validity = 30
        mock_sku.created_at = datetime.now(timezone.utc)
        mock_sku.updated_at = datetime.now(timezone.utc)
        
        mock_db.exec.return_value.one_or_none.return_value = mock_sku
        
        # Test
        result = self.payment_dao.get_sku_by_id("BASIC_HOROSCOPE")
        
        # Assertions
        assert result is not None
        assert result.sku_id == "BASIC_HOROSCOPE"
        assert result.name == "Basic Horoscope"

    @patch('dao.payments.get_session')
    def test_get_sku_by_id_not_found(self, mock_get_session):
        """Test getting SKU by ID when not found."""
        # Mock database session
        mock_db = MagicMock()
        mock_get_session.return_value.__enter__.return_value = mock_db
        
        mock_db.exec.return_value.one_or_none.return_value = None
        
        # Test
        result = self.payment_dao.get_sku_by_id("NONEXISTENT")
        
        # Assertions
        assert result is None

    @patch('dao.payments.get_session')
    def test_create_user_purchase(self, mock_get_session):
        """Test creating user purchase."""
        # Mock database session
        mock_db = MagicMock()
        mock_get_session.return_value.__enter__.return_value = mock_db
        
        # Mock SKU for valid_till calculation
        mock_sku = MagicMock()
        mock_sku.validity = 30
        
        # Mock the get_sku_by_id call
        with patch.object(self.payment_dao, 'get_sku_by_id', return_value=mock_sku):
            # Mock the created purchase with proper attributes
            mock_purchase = MagicMock()
            mock_purchase.id = 1
            mock_purchase.user_id = self.test_user_id
            mock_purchase.sku_id = self.test_sku_id
            mock_purchase.payment_link_id = self.test_payment_link_id
            mock_purchase.status = PaymentStatus.PENDING
            mock_purchase.created_at = datetime.now(timezone.utc)
            mock_purchase.valid_till = None
            
            # Mock the database operations
            mock_db.add.return_value = None
            mock_db.commit.return_value = None
            mock_db.refresh.return_value = None
            
            # Mock the model_validate to return a proper UserPurchase object
            with patch('dao.payments.UserPurchase.model_validate') as mock_validate:
                mock_validate.return_value = UserPurchase(
                    id=1,
                    user_id=self.test_user_id,
                    sku_id=self.test_sku_id,
                    payment_link_id=self.test_payment_link_id,
                    status=PaymentStatus.PENDING,
                    created_at=datetime.now(timezone.utc),
                    valid_till=None
                )
                
                # Test
                result = self.payment_dao.create_user_purchase(
                    user_id=self.test_user_id,
                    sku_id=self.test_sku_id,
                    payment_link_id=self.test_payment_link_id,
                    status=PaymentStatus.PENDING
                )
                
                # Assertions
                assert result is not None
                assert result.user_id == self.test_user_id
                assert result.sku_id == self.test_sku_id
                assert result.payment_link_id == self.test_payment_link_id
                assert result.status == PaymentStatus.PENDING

    @patch('dao.payments.get_session')
    def test_get_pending_payments(self, mock_get_session):
        """Test getting pending payments."""
        # Mock database session
        mock_db = MagicMock()
        mock_get_session.return_value.__enter__.return_value = mock_db
        
        # Mock pending payment
        mock_purchase = MagicMock()
        mock_purchase.id = 1
        mock_purchase.user_id = self.test_user_id
        mock_purchase.sku_id = self.test_sku_id
        mock_purchase.payment_link_id = self.test_payment_link_id
        mock_purchase.status = PaymentStatus.PENDING
        mock_purchase.created_at = datetime.now(timezone.utc)
        mock_purchase.valid_till = None
        
        mock_db.exec.return_value.all.return_value = [mock_purchase]
        
        # Mock the model_validate
        with patch('dao.payments.UserPurchase.model_validate') as mock_validate:
            mock_validate.return_value = UserPurchase(
                id=1,
                user_id=self.test_user_id,
                sku_id=self.test_sku_id,
                payment_link_id=self.test_payment_link_id,
                status=PaymentStatus.PENDING,
                created_at=datetime.now(timezone.utc),
                valid_till=None
            )
            
            # Test
            result = self.payment_dao.get_pending_payments()
            
            # Assertions
            assert len(result) == 1
            assert result[0].status == PaymentStatus.PENDING

    @patch('dao.payments.get_session')
    def test_get_active_subscriptions(self, mock_get_session):
        """Test getting active subscriptions."""
        # Mock database session
        mock_db = MagicMock()
        mock_get_session.return_value.__enter__.return_value = mock_db
        
        # Mock active subscription
        mock_purchase = MagicMock()
        mock_purchase.id = 1
        mock_purchase.user_id = self.test_user_id
        mock_purchase.sku_id = self.test_sku_id
        mock_purchase.payment_link_id = self.test_payment_link_id
        mock_purchase.status = PaymentStatus.PAID
        mock_purchase.created_at = datetime.now(timezone.utc)
        mock_purchase.valid_till = datetime.now(timezone.utc) + timedelta(days=30)
        
        mock_db.exec.return_value.all.return_value = [mock_purchase]
        
        # Mock the model_validate
        with patch('dao.payments.UserPurchase.model_validate') as mock_validate:
            mock_validate.return_value = UserPurchase(
                id=1,
                user_id=self.test_user_id,
                sku_id=self.test_sku_id,
                payment_link_id=self.test_payment_link_id,
                status=PaymentStatus.PAID,
                created_at=datetime.now(timezone.utc),
                valid_till=datetime.now(timezone.utc) + timedelta(days=30)
            )
            
            # Test
            result = self.payment_dao.get_active_subscriptions()
            
            # Assertions
            assert len(result) == 1
            assert result[0].status == PaymentStatus.PAID

    @patch('dao.payments.get_session')
    def test_update_payment_status(self, mock_get_session):
        """Test updating payment status."""
        # Mock database session
        mock_db = MagicMock()
        mock_get_session.return_value.__enter__.return_value = mock_db
        
        # Mock existing purchase
        mock_purchase = MagicMock()
        mock_purchase.id = 1
        mock_purchase.user_id = self.test_user_id
        mock_purchase.sku_id = self.test_sku_id
        mock_purchase.payment_link_id = self.test_payment_link_id
        mock_purchase.status = PaymentStatus.PENDING
        mock_purchase.created_at = datetime.now(timezone.utc)
        mock_purchase.valid_till = None
        
        mock_db.exec.return_value.one_or_none.return_value = mock_purchase
        mock_db.add.return_value = None
        mock_db.commit.return_value = None
        mock_db.refresh.return_value = None
        
        # Mock the get_sku_by_id call
        mock_sku = MagicMock()
        mock_sku.validity = 30
        
        # Mock the model_validate
        with patch.object(self.payment_dao, 'get_sku_by_id', return_value=mock_sku):
            with patch('dao.payments.UserPurchase.model_validate') as mock_validate:
                mock_validate.return_value = UserPurchase(
                    id=1,
                    user_id=self.test_user_id,
                    sku_id=self.test_sku_id,
                    payment_link_id=self.test_payment_link_id,
                                    status=PaymentStatus.PAID,
                created_at=datetime.now(timezone.utc),
                valid_till=datetime.now(timezone.utc) + timedelta(days=30)
                )
                
                # Test
                result = self.payment_dao.update_payment_status(
                    payment_link_id=self.test_payment_link_id,
                    status=PaymentStatus.PAID
                )
                
                # Assertions
                assert result is not None
                assert result.status == PaymentStatus.PAID

    @patch('dao.payments.get_session')
    def test_expire_payment_links(self, mock_get_session):
        """Test expiring payment links."""
        # Mock database session
        mock_db = MagicMock()
        mock_get_session.return_value.__enter__.return_value = mock_db
        
        # Mock pending purchase
        mock_purchase = MagicMock()
        mock_purchase.id = 1
        mock_purchase.user_id = self.test_user_id
        mock_purchase.sku_id = self.test_sku_id
        mock_purchase.payment_link_id = self.test_payment_link_id
        mock_purchase.status = PaymentStatus.PENDING
        
        # Mock the count query
        mock_count_result = MagicMock()
        mock_count_result.all.return_value = [mock_purchase]
        mock_db.exec.return_value = mock_count_result
        
        # Mock the raw SQL execution
        mock_db.execute.return_value = None
        mock_db.commit.return_value = None
        
        # Test
        result = self.payment_dao.expire_payment_links(self.test_user_id)
        
        # Assertions
        assert result == 1
        # Note: The actual status change happens in the database via raw SQL
        # The mock object status won't change, but the method should return the count


class TestRazorpayClient:
    """Test RazorpayClient functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        with patch('payments.razorpay_client.get_settings') as mock_settings:
            mock_settings.return_value.razorpay.API_KEY = "test_key"
            mock_settings.return_value.razorpay.API_SECRET = "test_secret"
            mock_settings.return_value.razorpay.BASE_URL = "https://api.razorpay.com/v1"
            mock_settings.return_value.razorpay.CALLBACK_BASE_URL = "https://test.com"
            self.client = RazorpayClient()

    @pytest.mark.asyncio
    @patch('payments.razorpay_client.PaymentDAO')
    @patch('payments.razorpay_client.httpx.AsyncClient')
    async def test_create_payment_link(self, mock_httpx_client, mock_payment_dao_class):
        """Test creating payment link."""
        # Mock PaymentDAO
        mock_payment_dao = MagicMock()
        mock_payment_dao_class.return_value = mock_payment_dao
        
        # Mock SKU
        mock_sku = MagicMock()
        mock_sku.name = "Basic Horoscope"
        mock_sku.amount = 99.0
        mock_payment_dao.get_sku_by_id.return_value = mock_sku
        
        # Mock user purchases (empty list for expire_payment_links)
        mock_payment_dao.get_user_purchases.return_value = []
        
        # Mock HTTP response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "id": "plink_test_123",
            "short_url": "https://rzp.io/test",
            "status": "created"
        }
        
        mock_httpx_client.return_value.__aenter__.return_value.post.return_value = mock_response
        
        # Test
        result = await self.client.create_payment_link(
            user_id="test_user",
            sku_id="BASIC_HOROSCOPE"
        )
        
        # Assertions
        assert result is not None
        assert result.payment_link_id == "plink_test_123"
        # Note: expire_payment_links is no longer called directly
        # Instead, expire_payment_link is called for each pending payment
        mock_payment_dao.create_user_purchase.assert_called_once()

    @pytest.mark.asyncio
    @patch('payments.razorpay_client.PaymentDAO')
    @patch('payments.razorpay_client.httpx.AsyncClient')
    async def test_check_payment_status(self, mock_httpx_client, mock_payment_dao_class):
        """Test checking payment status."""
        # Mock PaymentDAO
        mock_payment_dao = MagicMock()
        mock_payment_dao_class.return_value = mock_payment_dao
        
        # Mock user purchase
        mock_purchase = MagicMock()
        mock_purchase.status = PaymentStatus.PENDING
        mock_payment_dao.get_payment_by_link_id.return_value = mock_purchase
        
        # Mock HTTP response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "id": "plink_test_123",
            "status": "paid"
        }
        
        mock_httpx_client.return_value.__aenter__.return_value.get.return_value = mock_response
        
        # Test
        result = await self.client.check_payment_status("plink_test_123")
        
        # Assertions
        assert result is not None
        assert result["status"] == "paid"
        mock_payment_dao.update_payment_status.assert_called_once_with(
            "plink_test_123", PaymentStatus.PAID
        )

    @pytest.mark.asyncio
    @patch('payments.razorpay_client.PaymentDAO')
    @patch('payments.razorpay_client.httpx.AsyncClient')
    async def test_expire_payment_link(self, mock_httpx_client, mock_payment_dao_class):
        """Test expiring payment link."""
        # Mock PaymentDAO
        mock_payment_dao = MagicMock()
        mock_payment_dao_class.return_value = mock_payment_dao
        
                # Mock HTTP response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"status": "expired"}

        mock_httpx_client.return_value.__aenter__.return_value.post.return_value = mock_response
        
        # Test
        result = await self.client.expire_payment_link("plink_test_123")
        
        # Assertions
        assert result is True
        mock_payment_dao.update_payment_status.assert_called_once_with(
            "plink_test_123", PaymentStatus.EXPIRED
        )


class TestBackgroundTasks:
    """Test background tasks functionality."""

    @pytest.mark.asyncio
    @patch('payments.background_tasks.PaymentDAO')
    @patch('payments.background_tasks.RazorpayClient')
    async def test_poll_payment_status_every_n_seconds(self, mock_razorpay_client_class, mock_payment_dao_class):
        """Test payment status polling background task."""
        # Mock PaymentDAO
        mock_payment_dao = MagicMock()
        mock_payment_dao_class.return_value = mock_payment_dao
        
        # Mock pending payment
        mock_payment = MagicMock()
        mock_payment.payment_link_id = "plink_test_123"
        mock_payment.created_at = datetime.now(timezone.utc)
        mock_payment_dao.get_pending_payments.return_value = [mock_payment]
        
        # Mock RazorpayClient
        mock_razorpay_client = MagicMock()
        mock_razorpay_client_class.return_value = mock_razorpay_client
        
        # Mock payment status response - make it async
        async def mock_check_status(payment_link_id):
            return {"status": "paid"}
        
        mock_razorpay_client.check_payment_status = mock_check_status
        
        # Test with mocked sleep to avoid infinite loop
        with patch('payments.background_tasks.asyncio.sleep') as mock_sleep:
            # Make sleep raise an exception after first call to break the loop
            mock_sleep.side_effect = Exception("Test complete")
            
            # Test - this should run once and then break
            try:
                await poll_payment_status_every_n_seconds(0.1)
            except Exception as e:
                if str(e) != "Test complete":
                    raise
            
            # Assertions
            mock_payment_dao.get_pending_payments.assert_called()
            # The check_payment_status method now handles status updates internally
            # So we don't expect direct update_payment_status calls from background tasks

    @pytest.mark.asyncio
    @patch('payments.background_tasks.PaymentDAO')
    async def test_run_subscription_manager(self, mock_payment_dao_class):
        """Test subscription manager background task."""
        # Mock PaymentDAO
        mock_payment_dao = MagicMock()
        mock_payment_dao_class.return_value = mock_payment_dao
        
        # Mock active subscription
        mock_subscription = MagicMock()
        mock_subscription.payment_link_id = "plink_test_123"
        mock_subscription.user_id = "test_user"
        mock_subscription.created_at = datetime.now(timezone.utc) - timedelta(days=30)
        mock_payment_dao.get_active_subscriptions.return_value = [mock_subscription]
        
        # Test with mocked sleep to avoid infinite loop
        with patch('payments.background_tasks.asyncio.sleep') as mock_sleep:
            # Make sleep raise an exception after first call to break the loop
            mock_sleep.side_effect = Exception("Test complete")
            
            # Test - this should run once and then break
            try:
                await run_subscription_manager()
            except Exception as e:
                if str(e) != "Test complete":
                    raise
            
            # Assertions
            mock_payment_dao.get_active_subscriptions.assert_called()


class TestEnumUsage:
    """Test that enums are used correctly throughout the system."""

    def test_purchase_status_enum_values(self):
        """Test PaymentStatus enum values."""
        assert PaymentStatus.PENDING.value == "pending"
        assert PaymentStatus.PAID.value == "paid"
        assert PaymentStatus.FAILED.value == "failed"
        assert PaymentStatus.EXPIRED.value == "expired"

    def test_enum_comparison(self):
        """Test that enum comparisons work correctly."""
        status = PaymentStatus.PAID
        assert status == PaymentStatus.PAID
        assert status != PaymentStatus.PENDING
        assert status.value == "paid"

    def test_enum_in_list(self):
        """Test that enums work in list operations."""
        statuses = [PaymentStatus.PAID, PaymentStatus.EXPIRED]
        assert PaymentStatus.PAID in statuses
        assert PaymentStatus.PENDING not in statuses


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
