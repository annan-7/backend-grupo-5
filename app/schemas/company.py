from datetime import datetime

from pydantic import EmailStr, Field

from app.core.base_schema import ApiModel


class CompanyBase(ApiModel):
    company_name: str = Field(min_length=3, max_length=100)
    rut: str = Field(
        pattern=r"^\d{7,8}-[\dkK]$",
        description="Format: 12345678-5 (verification digit is validated with modulo 11)",
    )
    email: EmailStr
    phone: str = Field(min_length=8, max_length=15)
    address: str = Field(min_length=5, max_length=100)


class CompanyCreate(CompanyBase):
    pass


class CompanyUpdate(ApiModel):
    company_name: str | None = Field(None, min_length=3, max_length=100)
    rut: str | None = Field(None, pattern=r"^\d{7,8}-[\dkK]$")
    email: EmailStr | None = None
    phone: str | None = Field(None, min_length=8, max_length=15)
    address: str | None = Field(None, min_length=5, max_length=100)


class CompanyResponse(CompanyBase):
    company_id: str
    created_at: datetime
    updated_at: datetime
