"""
Integration test for Razorpay webhook endpoint.
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock

from api.app import app
from data.models import PaymentStatus

client = TestClient(app)


class TestRazorpayWebhook:
    """Test Razorpay webhook endpoint."""

    def test_razorpay_webhook_success(self):
        """Test successful webhook processing."""
        # Mock webhook payload
        webhook_payload = {
            "payload": {
                "payment_link": {
                    "entity": {
                        "id": "plink_test_123",
                        "status": "paid"
                    }
                }
            }
        }
        
        # Mock PaymentDAO
        with patch('api.app.PaymentDAO') as mock_payment_dao_class:
            mock_payment_dao = MagicMock()
            mock_payment_dao_class.return_value = mock_payment_dao
            
            # Mock successful update
            mock_updated_payment = MagicMock()
            mock_updated_payment.status = PaymentStatus.PAID
            mock_payment_dao.update_payment_status.return_value = mock_updated_payment
            
            # Test webhook endpoint
            response = client.post("/razorpay/webhook", json=webhook_payload)
            
            # Assertions
            assert response.status_code == 200
            assert response.json()["ok"] is True
            assert response.json()["status"] == "paid"
            
            # Verify DAO was called correctly
            mock_payment_dao.update_payment_status.assert_called_once_with(
                "plink_test_123", PaymentStatus.PAID
            )

    def test_razorpay_webhook_expired_status(self):
        """Test webhook with expired status."""
        # Mock webhook payload
        webhook_payload = {
            "payload": {
                "payment_link": {
                    "entity": {
                        "id": "plink_test_456",
                        "status": "expired"
                    }
                }
            }
        }
        
        # Mock PaymentDAO
        with patch('api.app.PaymentDAO') as mock_payment_dao_class:
            mock_payment_dao = MagicMock()
            mock_payment_dao_class.return_value = mock_payment_dao
            
            # Mock successful update
            mock_updated_payment = MagicMock()
            mock_updated_payment.status = PaymentStatus.EXPIRED
            mock_payment_dao.update_payment_status.return_value = mock_updated_payment
            
            # Test webhook endpoint
            response = client.post("/razorpay/webhook", json=webhook_payload)
            
            # Assertions
            assert response.status_code == 200
            assert response.json()["ok"] is True
            assert response.json()["status"] == "expired"
            
            # Verify DAO was called correctly
            mock_payment_dao.update_payment_status.assert_called_once_with(
                "plink_test_456", PaymentStatus.EXPIRED
            )

    def test_razorpay_webhook_missing_payment_link_id(self):
        """Test webhook with missing payment link ID."""
        # Mock webhook payload without payment link ID
        webhook_payload = {
            "payload": {
                "payment_link": {
                    "entity": {
                        "status": "paid"
                    }
                }
            }
        }
        
        # Test webhook endpoint
        response = client.post("/razorpay/webhook", json=webhook_payload)
        
        # Assertions
        assert response.status_code == 200
        assert response.json()["ok"] is False
        assert "No payment link ID" in response.json()["error"]

    def test_razorpay_webhook_missing_status(self):
        """Test webhook with missing status."""
        # Mock webhook payload without status
        webhook_payload = {
            "payload": {
                "payment_link": {
                    "entity": {
                        "id": "plink_test_789"
                    }
                }
            }
        }
        
        # Test webhook endpoint
        response = client.post("/razorpay/webhook", json=webhook_payload)
        
        # Assertions
        assert response.status_code == 200
        assert response.json()["ok"] is False
        assert "No status found" in response.json()["error"]

    def test_razorpay_webhook_payment_not_found(self):
        """Test webhook when payment is not found in database."""
        # Mock webhook payload
        webhook_payload = {
            "payload": {
                "payment_link": {
                    "entity": {
                        "id": "plink_nonexistent",
                        "status": "paid"
                    }
                }
            }
        }
        
        # Mock PaymentDAO returning None (payment not found)
        with patch('api.app.PaymentDAO') as mock_payment_dao_class:
            mock_payment_dao = MagicMock()
            mock_payment_dao_class.return_value = mock_payment_dao
            
            # Mock payment not found
            mock_payment_dao.update_payment_status.return_value = None
            
            # Test webhook endpoint
            response = client.post("/razorpay/webhook", json=webhook_payload)
            
            # Assertions
            assert response.status_code == 200
            assert response.json()["ok"] is False
            assert "Payment not found" in response.json()["error"]

    def test_razorpay_webhook_unknown_status(self):
        """Test webhook with unknown status."""
        # Mock webhook payload with unknown status
        webhook_payload = {
            "payload": {
                "payment_link": {
                    "entity": {
                        "id": "plink_test_999",
                        "status": "unknown_status"
                    }
                }
            }
        }
        
        # Mock PaymentDAO
        with patch('api.app.PaymentDAO') as mock_payment_dao_class:
            mock_payment_dao = MagicMock()
            mock_payment_dao_class.return_value = mock_payment_dao
            
            # Mock successful update
            mock_updated_payment = MagicMock()
            mock_updated_payment.status = PurchaseStatus.FAILED
            mock_payment_dao.update_payment_status.return_value = mock_updated_payment
            
            # Test webhook endpoint
            response = client.post("/razorpay/webhook", json=webhook_payload)
            
            # Assertions
            assert response.status_code == 200
            assert response.json()["ok"] is True
            assert response.json()["status"] == "failed"
            
            # Verify DAO was called with FAILED status
            mock_payment_dao.update_payment_status.assert_called_once_with(
                "plink_test_999", PurchaseStatus.FAILED
            )


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
