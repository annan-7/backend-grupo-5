from typing import Annotated

from fastapi import APIRouter, Depends, Query, Response
from starlette.status import HTTP_201_CREATED, HTTP_204_NO_CONTENT

from app.core.listing import build_page
from app.dependencies import get_reservation_service
from app.schemas.error import ErrorResponse
from app.schemas.filter import ReservationListQuery
from app.schemas.pagination import Paginated
from app.schemas.reservation import ReservationCreate, ReservationResponse, ReservationUpdate
from app.services.reservation_service import ReservationService

router = APIRouter(prefix="/reservations", tags=["Reservations"])
ServiceDep = Annotated[ReservationService, Depends(get_reservation_service)]

ERROR_RESPONSES = {
    400: {"model": ErrorResponse, "description": "Business rule violation"},
    404: {"model": ErrorResponse, "description": "Resource not found"},
    409: {"model": ErrorResponse, "description": "Schedule conflict"},
    422: {"model": ErrorResponse, "description": "Invalid request data"},
}


@router.post("", status_code=HTTP_201_CREATED, response_model=ReservationResponse, responses=ERROR_RESPONSES)
async def create_reservation(data: ReservationCreate, service: ServiceDep) -> ReservationResponse:
    """Create a reservation (always born as `pending`). Validates RN1-RN4 and availability windows."""
    return ReservationResponse.model_validate(await service.create(data))


@router.get("", response_model=Paginated[ReservationResponse], responses=ERROR_RESPONSES)
async def list_reservations(
    service: ServiceDep, query: Annotated[ReservationListQuery, Query()]
) -> Paginated[ReservationResponse]:
    """List reservations with filtering, sorting and pagination."""
    reservations = await service.get_all()
    if query.space_id is not None:
        reservations = [item for item in reservations if item.space_id == query.space_id]
    if query.company_id is not None:
        reservations = [item for item in reservations if item.company_id == query.company_id]
    if query.status is not None:
        reservations = [item for item in reservations if item.status == query.status]
    return build_page(reservations, query.page, query.limit, query.sort_by, query.direction)


@router.get("/{reservation_id}", response_model=ReservationResponse, responses=ERROR_RESPONSES)
async def get_reservation(reservation_id: str, service: ServiceDep) -> ReservationResponse:
    """Get a single reservation by ID."""
    return ReservationResponse.model_validate(await service.get_by_id(reservation_id))


@router.put("/{reservation_id}", response_model=ReservationResponse, responses=ERROR_RESPONSES)
@router.patch(
    "/{reservation_id}", response_model=ReservationResponse, responses=ERROR_RESPONSES, include_in_schema=False
)
async def update_reservation(reservation_id: str, data: ReservationUpdate, service: ServiceDep) -> ReservationResponse:
    """Update a reservation. Status changes go through the state machine;
    terminal states only allow `reason` edits."""
    return ReservationResponse.model_validate(await service.update(reservation_id, data))


@router.post("/{reservation_id}/confirm", response_model=ReservationResponse, responses=ERROR_RESPONSES)
async def confirm_reservation(reservation_id: str, service: ServiceDep) -> ReservationResponse:
    """Transition a pending reservation to `confirmed`."""
    return ReservationResponse.model_validate(await service.confirm(reservation_id))


@router.post("/{reservation_id}/cancel", response_model=ReservationResponse, responses=ERROR_RESPONSES)
async def cancel_reservation(reservation_id: str, service: ServiceDep) -> ReservationResponse:
    """Transition a pending/confirmed reservation to `canceled` (frees the slot)."""
    return ReservationResponse.model_validate(await service.cancel(reservation_id))


@router.post("/{reservation_id}/complete", response_model=ReservationResponse, responses=ERROR_RESPONSES)
async def complete_reservation(reservation_id: str, service: ServiceDep) -> ReservationResponse:
    """Transition a confirmed reservation to `completed`."""
    return ReservationResponse.model_validate(await service.complete(reservation_id))


@router.delete("/{reservation_id}", status_code=HTTP_204_NO_CONTENT, responses=ERROR_RESPONSES)
async def delete_reservation(reservation_id: str, service: ServiceDep) -> Response:
    """Delete a reservation (hard delete)."""
    await service.delete(reservation_id)
    return Response(status_code=HTTP_204_NO_CONTENT)
