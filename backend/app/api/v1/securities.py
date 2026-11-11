"""Security Master endpoints."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.security import Security
from app.models.security_identifier import SecurityIdentifier
from app.schemas.security import (
    SecurityCreate,
    SecurityIdentifierCreate,
    SecurityIdentifierResponse,
    SecurityResponse,
)

router = APIRouter(prefix="/securities", tags=["Securities"])


@router.post("", response_model=SecurityResponse, status_code=status.HTTP_201_CREATED)
def create_security(payload: SecurityCreate, db: Session = Depends(get_db)) -> Security:
    """Create a new security master record and optional identifiers."""
    security = Security(
        ticker=payload.ticker.upper(),
        security_name=payload.security_name,
        instrument_type=payload.instrument_type.value,
        primary_exchange=payload.primary_exchange.upper(),
        currency=payload.currency.upper(),
        country_of_risk=payload.country_of_risk.upper(),
        created_by=payload.created_by,
        is_active=True,
    )
    db.add(security)
    db.flush()

    for ident in payload.identifiers:
        sec_id = SecurityIdentifier(
            security_id=security.security_id,
            identifier_type=ident.identifier_type.value,
            identifier_value=ident.identifier_value.upper(),
            valid_from=ident.valid_from,
            valid_to=ident.valid_to,
            created_by=ident.created_by,
        )
        db.add(sec_id)

    db.commit()
    db.refresh(security)
    return security


@router.get("/{security_id}", response_model=SecurityResponse)
def get_security(security_id: int, db: Session = Depends(get_db)) -> Security:
    """Retrieve security by ID."""
    security = db.query(Security).filter_by(security_id=security_id).first()
    if not security:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Security with ID {security_id} not found.",
        )
    return security


@router.post(
    "/{security_id}/identifiers",
    response_model=SecurityIdentifierResponse,
    status_code=status.HTTP_201_CREATED,
)
def add_security_identifier(
    security_id: int, payload: SecurityIdentifierCreate, db: Session = Depends(get_db)
) -> SecurityIdentifier:
    """Attach an identifier cross-reference to an existing security."""
    security = db.query(Security).filter_by(security_id=security_id).first()
    if not security:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Security with ID {security_id} not found.",
        )

    identifier = SecurityIdentifier(
        security_id=security.security_id,
        identifier_type=payload.identifier_type.value,
        identifier_value=payload.identifier_value.upper(),
        valid_from=payload.valid_from,
        valid_to=payload.valid_to,
        created_by=payload.created_by,
    )
    db.add(identifier)
    db.commit()
    db.refresh(identifier)
    return identifier
