from datetime import date
from decimal import Decimal
from pydantic import BaseModel, Field

class LineItem(BaseModel):
    description: str
    quantity: Decimal = Field(ge=0)
    unit_price: Decimal = Field(ge=0)
    total: Decimal = Field(ge=0)

class Invoice(BaseModel):
    supplier_name: str
    invoice_number: str
    invoice_date: date
    currency: str = "USD"
    line_items: list[LineItem]
    subtotal: Decimal
    tax: Decimal
    total: Decimal
    po_number: str | None = None