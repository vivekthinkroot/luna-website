from datetime import datetime, timezone
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel
from sqlalchemy.exc import IntegrityError
from sqlmodel import select

from data.db import get_session
from data.models import ArtifactType, TArtifact


class Artifact(BaseModel):
    artifact_id: UUID
    user_id: UUID
    filename: str
    s3_url: str
    artifact_type: ArtifactType
    content_type: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ArtifactDAO:
    """DAO for managing user-uploaded artifacts stored in S3."""

    def create_artifact(
        self,
        user_id: str,
        filename: str,
        s3_url: str,
        artifact_type: ArtifactType,
        content_type: Optional[str] = None,
    ) -> Artifact:
        now = datetime.now(timezone.utc)
        user_id_uuid = user_id if isinstance(user_id, UUID) else UUID(str(user_id))
        artifact = TArtifact(
            user_id=user_id_uuid,
            filename=filename,
            s3_url=s3_url,
            artifact_type=artifact_type,
            content_type=content_type,
            created_at=now,
            updated_at=now,
        )
        with get_session() as db:
            db.add(artifact)
            try:
                db.commit()
                db.refresh(artifact)
            except IntegrityError as e:
                db.rollback()
                raise ValueError("Could not create artifact") from e
            return Artifact.model_validate(artifact)

    def get_artifact_by_id(self, artifact_id: str) -> Optional[Artifact]:
        artifact_id_uuid = (
            artifact_id if isinstance(artifact_id, UUID) else UUID(str(artifact_id))
        )
        with get_session() as db:
            result = db.exec(
                select(TArtifact).where(TArtifact.artifact_id == artifact_id_uuid)
            )
            artifact = result.one_or_none()
            return Artifact.model_validate(artifact) if artifact else None

    def list_user_artifacts(self, user_id: str) -> List[Artifact]:
        user_id_uuid = user_id if isinstance(user_id, UUID) else UUID(str(user_id))
        with get_session() as db:
            result = db.exec(select(TArtifact).where(TArtifact.user_id == user_id_uuid))
            return [Artifact.model_validate(a) for a in result.all()]

    def delete_artifact(self, artifact_id: str) -> bool:
        artifact_id_uuid = (
            artifact_id if isinstance(artifact_id, UUID) else UUID(str(artifact_id))
        )
        with get_session() as db:
            result = db.exec(
                select(TArtifact).where(TArtifact.artifact_id == artifact_id_uuid)
            )
            artifact = result.one_or_none()
            if not artifact:
                return False
            db.delete(artifact)
            db.commit()
            return True

    def update_artifact(
        self,
        artifact_id: str,
        filename: Optional[str] = None,
        s3_url: Optional[str] = None,
        content_type: Optional[str] = None,
        artifact_type: Optional[ArtifactType] = None,
    ) -> Optional[Artifact]:
        artifact_id_uuid = (
            artifact_id if isinstance(artifact_id, UUID) else UUID(str(artifact_id))
        )
        with get_session() as db:
            result = db.exec(
                select(TArtifact).where(TArtifact.artifact_id == artifact_id_uuid)
            )
            artifact = result.one_or_none()
            if not artifact:
                return None
            if filename is not None:
                artifact.filename = filename
            if s3_url is not None:
                artifact.s3_url = s3_url
            if content_type is not None:
                artifact.content_type = content_type
            if artifact_type is not None:
                artifact.artifact_type = artifact_type
            artifact.updated_at = datetime.now(timezone.utc)
            db.add(artifact)
            db.commit()
            db.refresh(artifact)
            return Artifact.model_validate(artifact)
