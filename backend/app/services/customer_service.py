from __future__ import annotations

from sqlalchemy.orm import Session

from app.models import Customer


def ensure_customer(db: Session, customer_id: str, org_id: int) -> Customer:
    customer_id = (customer_id or "").strip()
    if not customer_id:
        raise ValueError("customer_id is required")

    row = db.query(Customer).filter(Customer.customer_id == customer_id, Customer.org_id == org_id).one_or_none()
    if row is not None:
        return row

    row = Customer(customer_id=customer_id, org_id=org_id)
    db.add(row)
    db.flush()
    return row

