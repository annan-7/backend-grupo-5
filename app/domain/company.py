from dataclasses import dataclass
from datetime import datetime

from app.domain.validators import utc_now, validate_email, validate_rut, validate_text


@dataclass
class Company:
    company_id: str
    company_name: str
    rut: str
    email: str
    phone: str
    address: str
    created_at: datetime
    updated_at: datetime

    @classmethod
    def create(
        cls,
        company_id: str,
        company_name: str,
        rut: str,
        email: str,
        phone: str,
        address: str,
    ) -> "Company":
        now = utc_now()
        return cls(
            company_id=company_id,
            company_name=validate_text(company_name, "company name"),
            rut=validate_rut(rut),
            email=validate_email(email),
            phone=validate_text(phone, "phone"),
            address=validate_text(address, "address"),
            created_at=now,
            updated_at=now,
        )

    def update(
        self,
        company_name: str | None = None,
        rut: str | None = None,
        email: str | None = None,
        phone: str | None = None,
        address: str | None = None,
    ) -> None:
        if company_name is not None:
            self.company_name = validate_text(company_name, "company name")
        if rut is not None:
            self.rut = validate_rut(rut)
        if email is not None:
            self.email = validate_email(email)
        if phone is not None:
            self.phone = validate_text(phone, "phone")
        if address is not None:
            self.address = validate_text(address, "address")
        self.updated_at = utc_now()
