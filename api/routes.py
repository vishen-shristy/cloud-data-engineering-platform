from __future__ import annotations

from typing import Annotated, Any

import pandas as pd
from fastapi import APIRouter, Depends, HTTPException, Query, status

from api.dependencies import get_booking_repository
from api.schemas import (
    BookingListResponse,
    BookingResponse,
    HealthResponse,
)
from database.repository import HotelBookingRepository


router = APIRouter()


def convert_to_json_safe(value: Any) -> Any:
    """
    Convert pandas and NumPy values into JSON-safe Python values.
    """
    if isinstance(value, pd.Timestamp):
        return value.isoformat()

    if pd.isna(value):
        return None

    if hasattr(value, "item"):
        return value.item()

    return value


def dataframe_to_records(
    dataframe: pd.DataFrame,
) -> list[dict[str, Any]]:
    """
    Convert a pandas DataFrame into JSON-safe dictionaries.
    """
    records = dataframe.to_dict(orient="records")

    return [
        {
            key: convert_to_json_safe(value)
            for key, value in record.items()
        }
        for record in records
    ]


@router.get(
    "/",
    response_model=HealthResponse,
    tags=["System"],
    summary="API information",
)
def root() -> HealthResponse:
    return HealthResponse(
        status="success",
        message="Hotel Booking Analytics API is running.",
    )


@router.get(
    "/health",
    response_model=HealthResponse,
    tags=["System"],
    summary="Health check",
)
def health_check() -> HealthResponse:
    return HealthResponse(
        status="healthy",
        message="Application is available.",
    )


@router.get(
    "/bookings",
    response_model=BookingListResponse,
    tags=["Bookings"],
    summary="Get hotel bookings",
)
def get_bookings(
    repository: Annotated[
        HotelBookingRepository,
        Depends(get_booking_repository),
    ],
    limit: Annotated[
        int,
        Query(
            ge=1,
            le=500,
            description="Maximum records to return.",
        ),
    ] = 100,
    offset: Annotated[
        int,
        Query(
            ge=0,
            description="Number of records to skip.",
        ),
    ] = 0,
) -> BookingListResponse:
    dataframe = repository.get_all_bookings(
        limit=limit,
        offset=offset,
    )

    records = dataframe_to_records(dataframe)

    return BookingListResponse(
        total=len(records),
        limit=limit,
        offset=offset,
        data=records,
    )


@router.get(
    "/bookings/{booking_id}",
    response_model=BookingResponse,
    responses={
        status.HTTP_404_NOT_FOUND: {
            "description": "Booking not found",
        },
    },
    tags=["Bookings"],
    summary="Get booking by ID",
)
def get_booking_by_id(
    booking_id: int,
    repository: Annotated[
        HotelBookingRepository,
        Depends(get_booking_repository),
    ],
) -> BookingResponse:
    if booking_id <= 0:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="booking_id must be greater than 0.",
        )

    booking = repository.get_booking_by_id(
        booking_id=booking_id,
    )

    if booking is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Booking {booking_id} was not found.",
        )

    safe_booking = {
        key: convert_to_json_safe(value)
        for key, value in booking.items()
    }

    return BookingResponse.model_validate(
        safe_booking
    )