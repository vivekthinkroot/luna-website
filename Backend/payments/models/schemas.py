"""
Pydantic models for payment requests and responses.
"""

from pydantic import BaseModel


class PaymentLinkRequest(BaseModel):
    """Request model for creating a payment link."""
    user_id: str
    sku_id: str


class PaymentLinkResponse(BaseModel):
    """Response model for payment link creation."""
    payment_url: str
    payment_link_id: str
    status: str


class PaymentStatusResponse(BaseModel):
    """Response model for payment status check."""
    status: str
    payment_link_id: str
    payment_url: str 