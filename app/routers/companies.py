from typing import Annotated

from fastapi import APIRouter, Depends, Query, Response
from starlette.status import HTTP_201_CREATED, HTTP_204_NO_CONTENT

from app.core.listing import build_page
from app.dependencies import get_company_service
from app.schemas.company import CompanyCreate, CompanyResponse, CompanyUpdate
from app.schemas.error import ErrorResponse
from app.schemas.filter import CompanyListQuery
from app.schemas.pagination import Paginated
from app.services.company_service import CompanyService

router = APIRouter(prefix="/companies", tags=["Companies"])
ServiceDep = Annotated[CompanyService, Depends(get_company_service)]

ERROR_RESPONSES = {
    400: {"model": ErrorResponse, "description": "Business rule violation"},
    404: {"model": ErrorResponse, "description": "Resource not found"},
    409: {"model": ErrorResponse, "description": "Duplicate RUT/email or active reservations"},
    422: {"model": ErrorResponse, "description": "Invalid request data"},
}


@router.post("", status_code=HTTP_201_CREATED, response_model=CompanyResponse, responses=ERROR_RESPONSES)
async def create_company(data: CompanyCreate, service: ServiceDep) -> CompanyResponse:
    """Create a new company. RUT and email must be unique (409 otherwise)."""
    return CompanyResponse.model_validate(await service.create(data))


@router.get("", response_model=Paginated[CompanyResponse], responses=ERROR_RESPONSES)
async def list_companies(
    service: ServiceDep, query: Annotated[CompanyListQuery, Query()]
) -> Paginated[CompanyResponse]:
    """List companies with filtering, sorting and pagination."""
    companies = await service.get_all()
    if query.name is not None:
        needle = query.name.lower()
        companies = [company for company in companies if needle in company.company_name.lower()]
    if query.rut is not None:
        companies = [company for company in companies if company.rut == query.rut.strip().upper()]
    return build_page(companies, query.page, query.limit, query.sort_by, query.direction)


@router.get("/{company_id}", response_model=CompanyResponse, responses=ERROR_RESPONSES)
async def get_company(company_id: str, service: ServiceDep) -> CompanyResponse:
    """Get a single company by ID."""
    return CompanyResponse.model_validate(await service.get_by_id(company_id))


@router.put("/{company_id}", response_model=CompanyResponse, responses=ERROR_RESPONSES)
@router.patch("/{company_id}", response_model=CompanyResponse, responses=ERROR_RESPONSES, include_in_schema=False)
async def update_company(company_id: str, data: CompanyUpdate, service: ServiceDep) -> CompanyResponse:
    """Update a company (partial updates accepted; PATCH is an alias of PUT)."""
    return CompanyResponse.model_validate(await service.update(company_id, data))


@router.delete("/{company_id}", status_code=HTTP_204_NO_CONTENT, responses=ERROR_RESPONSES)
async def delete_company(company_id: str, service: ServiceDep) -> Response:
    """Delete a company. Blocked (409) if it has active reservations."""
    await service.delete(company_id)
    return Response(status_code=HTTP_204_NO_CONTENT)
