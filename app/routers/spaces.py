from typing import Annotated

from fastapi import APIRouter, Depends, Query, Response
from starlette.status import HTTP_201_CREATED, HTTP_204_NO_CONTENT

from app.core.listing import build_page
from app.dependencies import get_space_service
from app.schemas.error import ErrorResponse
from app.schemas.filter import SpaceListQuery
from app.schemas.pagination import Paginated
from app.schemas.space import SpaceCreate, SpaceResponse, SpaceUpdate
from app.services.space_service import SpaceService

router = APIRouter(prefix="/spaces", tags=["Spaces"])
ServiceDep = Annotated[SpaceService, Depends(get_space_service)]

ERROR_RESPONSES = {
    400: {"model": ErrorResponse, "description": "Business rule violation"},
    404: {"model": ErrorResponse, "description": "Resource not found"},
    409: {"model": ErrorResponse, "description": "Conflict with related records"},
    422: {"model": ErrorResponse, "description": "Invalid request data"},
}


@router.post("", status_code=HTTP_201_CREATED, response_model=SpaceResponse, responses=ERROR_RESPONSES)
async def create_space(data: SpaceCreate, service: ServiceDep) -> SpaceResponse:
    """Create a new coworking space."""
    return SpaceResponse.model_validate(await service.create(data))


@router.get("", response_model=Paginated[SpaceResponse], responses=ERROR_RESPONSES)
async def list_spaces(service: ServiceDep, query: Annotated[SpaceListQuery, Query()]) -> Paginated[SpaceResponse]:
    """List spaces with filtering, sorting and pagination."""
    spaces = await service.get_all()
    if query.type is not None:
        spaces = [space for space in spaces if space.type == query.type]
    if query.status is not None:
        spaces = [space for space in spaces if space.status == query.status]
    if query.min_capacity is not None:
        spaces = [space for space in spaces if space.capacity >= query.min_capacity]
    return build_page(spaces, query.page, query.limit, query.sort_by, query.direction)


@router.get("/{space_id}", response_model=SpaceResponse, responses=ERROR_RESPONSES)
async def get_space(space_id: str, service: ServiceDep) -> SpaceResponse:
    """Get a single space by ID."""
    return SpaceResponse.model_validate(await service.get_by_id(space_id))


@router.put("/{space_id}", response_model=SpaceResponse, responses=ERROR_RESPONSES)
@router.patch("/{space_id}", response_model=SpaceResponse, responses=ERROR_RESPONSES, include_in_schema=False)
async def update_space(space_id: str, data: SpaceUpdate, service: ServiceDep) -> SpaceResponse:
    """Update a space (partial updates accepted; PATCH is an alias of PUT)."""
    return SpaceResponse.model_validate(await service.update(space_id, data))


@router.delete("/{space_id}", status_code=HTTP_204_NO_CONTENT, responses=ERROR_RESPONSES)
async def delete_space(space_id: str, service: ServiceDep) -> Response:
    """Delete a space. Blocked (409) if it has active reservations; availabilities are cascaded."""
    await service.delete(space_id)
    return Response(status_code=HTTP_204_NO_CONTENT)
