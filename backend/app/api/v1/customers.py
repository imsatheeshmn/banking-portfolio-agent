"""Customer master endpoints."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.customer import Customer
from app.schemas.customer import CustomerCreate, CustomerResponse

router = APIRouter(prefix="/customers", tags=["Customers"])


@router.post("", response_model=CustomerResponse, status_code=status.HTTP_201_CREATED)
def create_customer(payload: CustomerCreate, db: Session = Depends(get_db)) -> Customer:
    """Register a new institutional or legal customer."""
    customer = Customer(
        legal_name=payload.legal_name,
        country_code=payload.country_code.upper(),
        created_by=payload.created_by,
        status="ACTIVE",
    )
    db.add(customer)
    db.commit()
    db.refresh(customer)
    return customer


@router.get("/{customer_id}", response_model=CustomerResponse)
def get_customer(customer_id: int, db: Session = Depends(get_db)) -> Customer:
    """Retrieve customer by primary key ID."""
    customer = db.query(Customer).filter_by(customer_id=customer_id).first()
    if not customer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Customer with ID {customer_id} not found.",
        )
    return customer


@router.get("", response_model=list[CustomerResponse])
def list_customers(
    skip: int = 0, limit: int = 100, db: Session = Depends(get_db)
) -> list[Customer]:
    """List active customers."""
    return db.query(Customer).offset(skip).limit(limit).all()
