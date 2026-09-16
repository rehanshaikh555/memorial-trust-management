from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import CurrentUser, get_db, require_permission
from app.core.permissions import Permission
from app.schemas.trust import TrustCreate, TrustResponse, TrustUpdate
from app.services.scope_service import has_trust_access
from app.services.trust_service import TrustService


router = APIRouter(prefix="/trust", tags=["Trust"])

DbSession = Annotated[Session, Depends(get_db)]


@router.post(
    "",
    response_model=TrustResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission(Permission.TRUST_CREATE.value))],
)
def create_trust(data: TrustCreate, db: DbSession) -> TrustResponse:
    try:
        trust = TrustService.create(db, data)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc

    return trust


@router.get(
    "",
    response_model=list[TrustResponse],
    dependencies=[Depends(require_permission(Permission.TRUST_READ.value))],
)
def list_trusts(db: DbSession) -> list[TrustResponse]:
    return TrustService.list_all(db)


@router.get(
    "/{trust_id}",
    response_model=TrustResponse,
    dependencies=[Depends(require_permission(Permission.TRUST_READ.value))],
)
def get_trust(
    trust_id: UUID,
    db: DbSession,
    current_user: CurrentUser,
) -> TrustResponse:
    trust = TrustService.get_by_id(db, trust_id)

    if trust is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Trust not found.",
        )

    if not has_trust_access(db, current_user, trust_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have access to this trust.",
        )

    return trust


@router.patch(
    "/{trust_id}",
    response_model=TrustResponse,
    dependencies=[Depends(require_permission(Permission.TRUST_UPDATE.value))],
)
def update_trust(
    trust_id: UUID,
    data: TrustUpdate,
    db: DbSession,
    current_user: CurrentUser,
) -> TrustResponse:
    trust = TrustService.get_by_id(db, trust_id)

    if trust is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Trust not found.",
        )

    if not has_trust_access(db, current_user, trust_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have access to this trust.",
        )

    try:
        trust = TrustService.update(db, trust, data)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc

    return trust
