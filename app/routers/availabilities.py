from typing import Annotated

from fastapi import APIRouter, Depends, Query, Response
from starlette.status import HTTP_201_CREATED, HTTP_204_NO_CONTENT

from app.core.listing import build_page
from app.dependencies import get_availability_service
from app.schemas.availability import AvailabilityCreate, AvailabilityResponse, AvailabilityUpdate
from app.schemas.error import ErrorResponse
from app.schemas.filter import AvailabilityListQuery
from app.schemas.pagination import Paginated
from app.services.availability_service import AvailabilityService

router = APIRouter(prefix="/availabilities", tags=["Availabilities"])
ServiceDep = Annotated[AvailabilityService, Depends(get_availability_service)]

ERROR_RESPONSES = {
    400: {"model": ErrorResponse, "description": "Business rule violation"},
    404: {"model": ErrorResponse, "description": "Resource not found"},
    409: {"model": ErrorResponse, "description": "Overlapping availability window"},
    422: {"model": ErrorResponse, "description": "Invalid request data"},
}


@router.post("", status_code=HTTP_201_CREATED, response_model=AvailabilityResponse, responses=ERROR_RESPONSES)
async def create_availability(data: AvailabilityCreate, service: ServiceDep) -> AvailabilityResponse:
    """Create an availability window. Overlapping windows for the same space+weekday are rejected (409)."""
    return AvailabilityResponse.model_validate(await service.create(data))


@router.get("", response_model=Paginated[AvailabilityResponse], responses=ERROR_RESPONSES)
async def list_availabilities(
    service: ServiceDep, query: Annotated[AvailabilityListQuery, Query()]
) -> Paginated[AvailabilityResponse]:
    """List availabilities with filtering, sorting and pagination."""
    availabilities = await service.get_all()
    if query.space_id is not None:
        availabilities = [item for item in availabilities if item.space_id == query.space_id]
    if query.weekday is not None:
        availabilities = [item for item in availabilities if item.weekday == query.weekday]
    return build_page(availabilities, query.page, query.limit, query.sort_by, query.direction)


@router.get("/{availability_id}", response_model=AvailabilityResponse, responses=ERROR_RESPONSES)
async def get_availability(availability_id: str, service: ServiceDep) -> AvailabilityResponse:
    """Get a single availability window by ID."""
    return AvailabilityResponse.model_validate(await service.get_by_id(availability_id))


@router.put("/{availability_id}", response_model=AvailabilityResponse, responses=ERROR_RESPONSES)
@router.patch(
    "/{availability_id}", response_model=AvailabilityResponse, responses=ERROR_RESPONSES, include_in_schema=False
)
async def update_availability(
    availability_id: str, data: AvailabilityUpdate, service: ServiceDep
) -> AvailabilityResponse:
    """Update an availability window (partial updates accepted; PATCH is an alias of PUT)."""
    return AvailabilityResponse.model_validate(await service.update(availability_id, data))


@router.delete("/{availability_id}", status_code=HTTP_204_NO_CONTENT, responses=ERROR_RESPONSES)
async def delete_availability(availability_id: str, service: ServiceDep) -> Response:
    """Delete an availability window."""
    await service.delete(availability_id)
    return Response(status_code=HTTP_204_NO_CONTENT)
