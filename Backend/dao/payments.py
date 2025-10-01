"""
PaymentDAO implementation for Luna.
Handles payment operations, SKU master data, and user purchases with validity management.
"""

from datetime import datetime, timedelta, timezone
from typing import List, Optional

from pydantic import BaseModel
from sqlalchemy import DateTime, cast, update, text
from sqlalchemy.exc import IntegrityError
from sqlmodel import and_, select

from data.db import get_session
from data.models import PaymentStatus, TSku, TUserPurchase


class Sku(BaseModel):
    id: int
    name: str
    sku_id: str
    amount: float
    validity: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class UserPurchase(BaseModel):
    id: int
    user_id: str
    sku_id: str
    payment_link_id: str
    status: PaymentStatus
    created_at: datetime
    valid_till: Optional[datetime] = None

    model_config = {"from_attributes": True}
    
    @classmethod
    def model_validate(cls, obj, **kwargs):
        """Override model_validate to handle string status values."""
        if hasattr(obj, 'status') and isinstance(obj.status, str):
            # Convert string status to PaymentStatus enum
            try:
                obj.status = PaymentStatus(obj.status)
            except ValueError:
                # If string doesn't match enum, default to PENDING
                obj.status = PaymentStatus.PENDING
        return super().model_validate(obj, **kwargs)


class PaymentDAO:
    """Data access object for payment operations (synchronous)."""

    def get_all_skus(self) -> List[Sku]:
        """
        Fetch all available SKUs.
        Returns:
            List[Sku]: List of all SKU objects.
        """
        with get_session() as db:
            result = db.exec(select(TSku))
            return [Sku.model_validate(sku) for sku in result.all()]

    def get_sku_by_id(self, sku_id: str) -> Optional[Sku]:
        """
        Get SKU by sku_id.
        Args:
            sku_id (str): SKU identifier.
        Returns:
            Optional[Sku]: SKU object or None if not found.
        """
        with get_session() as db:
            result = db.exec(select(TSku).where(TSku.sku_id == sku_id))
            sku = result.one_or_none()
            return Sku.model_validate(sku) if sku else None

    def create_user_purchase(
        self,
        user_id: str,
        sku_id: str,
        payment_link_id: str,
        status: PaymentStatus = PaymentStatus.PENDING,
        valid_till: Optional[datetime] = None,
    ) -> UserPurchase:
        """
        Create a new user purchase record.
        Args:
            user_id (str): User identifier.
            sku_id (str): SKU identifier.
            payment_link_id (str): Payment link identifier.
            status (PaymentStatus): Payment status (default: PENDING).
            valid_till (Optional[datetime]): Validity end date (default: None).

        Returns:
            UserPurchase: Created user purchase object.
        Raises:
            ValueError: If creation fails or invalid data.
        """
        now = datetime.now(timezone.utc)

        # Calculate valid_till based on SKU validity
        sku = self.get_sku_by_id(sku_id)
        if not sku:
            raise ValueError(f"SKU with id '{sku_id}' not found")

        valid_till = (
            now + timedelta(days=sku.validity)
            if status == PaymentStatus.PAID
            else None
        )

        user_purchase = TUserPurchase(
            user_id=user_id,
            sku_id=sku_id,
            payment_link_id=payment_link_id,
            status=status,
            created_at=now,
            valid_till=valid_till,
        )

        with get_session() as db:
            db.add(user_purchase)
            try:
                db.commit()
                db.refresh(user_purchase)
                return UserPurchase.model_validate(user_purchase)
            except IntegrityError as e:
                db.rollback()
                raise ValueError("User purchase creation failed or invalid data") from e

    def get_user_purchases(self, user_id: str) -> List[UserPurchase]:
        """
        Fetch all user purchases for a given user_id.
        Args:
            user_id (str): User identifier.
        Returns:
            List[UserPurchase]: List of user purchase objects.
        """
        with get_session() as db:
            result = db.exec(
                select(TUserPurchase).where(TUserPurchase.user_id == user_id)
            )
            return [
                UserPurchase.model_validate(user_purchase)
                for user_purchase in result.all()
            ]

    def get_active_user_purchases(self, user_id: str) -> List[UserPurchase]:
        """
        Fetch active user purchases (status PAID and valid_till >= current time).
        Args:
            user_id (str): User identifier.
        Returns:
            List[UserPurchase]: List of active user purchase objects.
        """
        now = datetime.now(timezone.utc)
        with get_session() as db:
            result = db.exec(
                select(TUserPurchase).where(
                    and_(
                        TUserPurchase.user_id == user_id,
                        TUserPurchase.status == PaymentStatus.PAID,
                        TUserPurchase.valid_till != None,
                        cast(TUserPurchase.valid_till, DateTime) >= now,
                    )
                )
            )
            return [
                UserPurchase.model_validate(user_purchase)
                for user_purchase in result.all()
            ]

    def update_payment_status_by_payment_link_id(
        self,
        payment_link_id: str,
        status: PaymentStatus,
    ) -> Optional[UserPurchase]:
        """
        Update payment status by payment_link_id.
        Args:
            payment_link_id (str): Payment link identifier.
            status (PaymentStatus): New payment status.

        Returns:
            Optional[UserPurchase]: Updated user purchase object or None if not found.
        """
        with get_session() as db:
            result = db.exec(
                select(TUserPurchase).where(
                    TUserPurchase.payment_link_id == payment_link_id
                )
            )
            user_purchase = result.one_or_none()

            if not user_purchase:
                return None

            # Update status and related fields
            user_purchase.status = status

            # Update valid_till if status is PAID
            if status == PaymentStatus.PAID and not user_purchase.valid_till:
                sku = self.get_sku_by_id(user_purchase.sku_id)
                if sku:
                    user_purchase.valid_till = datetime.now(timezone.utc) + timedelta(
                        days=sku.validity
                    )

            db.add(user_purchase)
            try:
                db.commit()
                db.refresh(user_purchase)
                return UserPurchase.model_validate(user_purchase)
            except IntegrityError as e:
                db.rollback()
                raise ValueError("Failed to update payment status") from e

    def get_user_purchases_by_id(
        self, user_purchase_id: int
    ) -> Optional[UserPurchase]:
        """
        Get user purchase by ID.
        Args:
            user_purchase_id (int): User purchase ID.
        Returns:
            Optional[UserPurchase]: User purchase object or None if not found.
        """
        with get_session() as db:
            result = db.exec(
                select(TUserPurchase).where(TUserPurchase.id == user_purchase_id)
            )
            user_purchase = result.one_or_none()
            return (
                UserPurchase.model_validate(user_purchase) if user_purchase else None
            )

    def get_payment_by_link_id(
        self, payment_link_id: str
    ) -> Optional[UserPurchase]:
        """
        Get user purchase by payment link ID.
        Args:
            payment_link_id (str): Payment link identifier.
        Returns:
            Optional[UserPurchase]: User purchase object or None if not found.
        """
        with get_session() as db:
            result = db.exec(
                select(TUserPurchase).where(
                    TUserPurchase.payment_link_id == payment_link_id
                )
            )
            user_purchase = result.one_or_none()
            return (
                UserPurchase.model_validate(user_purchase) if user_purchase else None
            )

    def get_expired_user_purchases(self) -> List[UserPurchase]:
        """
        Get all expired user purchases (valid_till < current time).
        Returns:
            List[UserPurchase]: List of expired user purchase objects.
        """
        now = datetime.now(timezone.utc)
        with get_session() as db:
            result = db.exec(
                select(TUserPurchase).where(
                    and_(
                        TUserPurchase.valid_till != None,
                        cast(TUserPurchase.valid_till, DateTime) < now,
                        TUserPurchase.status == PaymentStatus.PAID,
                    )
                )
            )
            return [
                UserPurchase.model_validate(user_purchase)
                for user_purchase in result.all()
            ]

    def update_expired_status(self) -> int:
        """
        Update status of expired user purchases to 'expired'.
        Returns:
            int: Number of updated records.
        """
        now = datetime.now(timezone.utc)
        with get_session() as db:
            result = db.exec(
                select(TUserPurchase).where(
                    and_(
                        TUserPurchase.valid_till != None,
                        cast(TUserPurchase.valid_till, DateTime) < now,
                        TUserPurchase.status == PaymentStatus.PAID,
                    )
                )
            )
            expired_purchases = result.all()

            for user_purchase in expired_purchases:
                user_purchase.status = PaymentStatus.EXPIRED
                db.add(user_purchase)

            try:
                db.commit()
                return len(expired_purchases)
            except IntegrityError as e:
                db.rollback()
                raise ValueError("Failed to update expired status") from e

    # New methods for background tasks and razorpay client

    def get_pending_payments(self) -> List[UserPurchase]:
        """
        Get all payments that are not in PAID or EXPIRED status.
        Returns:
            List[UserPurchase]: List of pending payment objects.
        """
        with get_session() as db:
            result = db.exec(
                select(TUserPurchase).where(
                    and_(
                        TUserPurchase.status != PaymentStatus.PAID,
                        TUserPurchase.status != PaymentStatus.EXPIRED
                    )
                )
            )
            return [UserPurchase.model_validate(user_purchase) for user_purchase in result.all()]

    def get_active_subscriptions(self) -> List[UserPurchase]:
        """
        Get all active paid subscriptions (status PAID and valid_till >= current time).
        Returns:
            List[UserPurchase]: List of active subscription objects.
        """
        now = datetime.now(timezone.utc)
        with get_session() as db:
            result = db.exec(
                select(TUserPurchase).where(
                    and_(
                        TUserPurchase.status == PaymentStatus.PAID,
                        TUserPurchase.valid_till != None,
                        cast(TUserPurchase.valid_till, DateTime) >= now,
                    )
                )
            )
            return [UserPurchase.model_validate(user_purchase) for user_purchase in result.all()]

    def update_payment_status(self, payment_link_id: str, status: PaymentStatus) -> Optional[UserPurchase]:
        """
        Alias for update_payment_status_by_payment_link_id.
        Args:
            payment_link_id (str): Payment link identifier.
            status (PaymentStatus): New payment status.
        Returns:
            Optional[UserPurchase]: Updated user purchase object or None if not found.
        """
        return self.update_payment_status_by_payment_link_id(payment_link_id, status)

    def expire_payment_links(self, user_id: str) -> int:
        """
        Expire all pending payment links for a user.
        Note: This method should be called with Razorpay confirmation.
        Args:
            user_id (str): User identifier.
        Returns:
            int: Number of expired payment links.
        """
        with get_session() as db:
            # First get the count for return value
            count_result = db.exec(
                select(TUserPurchase).where(
                    and_(
                        TUserPurchase.user_id == user_id,
                        TUserPurchase.status == PaymentStatus.PENDING
                    )
                )
            )
            count = len(count_result.all())
            
            # Use raw SQL for atomic UPDATE
            stmt = text("""
                UPDATE user_purchases 
                SET status = :expired_status 
                WHERE user_id = :user_id AND status = :pending_status
            """)
            
            db.execute(
                stmt,
                {
                    "expired_status": PaymentStatus.EXPIRED.value,
                    "user_id": user_id,
                    "pending_status": PaymentStatus.PENDING.value
                }
            )
            
            db.commit()
            return count

   