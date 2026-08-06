from __future__ import annotations

from typing import Annotated, Any

import pandas as pd
from fastapi import APIRouter, Depends, HTTPException, Query, status

from api.dependencies import get_booking_repository
from api.schemas import (
    BookingListResponse,
    BookingResponse,
    CancellationRateResponse,
    CountryBookingSummary,
    HealthResponse,
    HotelPerformanceSummary,
    MonthlyBookingSummary,
    RevenueSummary,
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

@router.get(
    "/api/v1/analytics/top-countries",
    response_model=list[CountryBookingSummary],
    tags=["Analytics"],
    summary="Get top booking countries",
)
def get_top_countries(
    repository: Annotated[
        HotelBookingRepository,
        Depends(get_booking_repository),
    ],
    limit: Annotated[
        int,
        Query(
            ge=1,
            le=100,
            description="Number of countries to return.",
        ),
    ] = 10,
) -> list[CountryBookingSummary]:
    dataframe = repository.get_top_countries(
        limit=limit,
    )

    records = dataframe_to_records(dataframe)

    return [
        CountryBookingSummary.model_validate(record)
        for record in records
    ]

@router.get(
    "/api/v1/analytics/revenue",
    response_model=list[RevenueSummary],
    tags=["Analytics"],
    summary="Get estimated booking-value summary",
    description=(
        "Returns estimated booking value calculated as ADR multiplied "
        "by stayed nights for non-cancelled bookings."
    ),
)
def get_revenue_summary(
    repository: Annotated[
        HotelBookingRepository,
        Depends(get_booking_repository),
    ],
) -> list[RevenueSummary]:
    dataframe = repository.get_revenue_summary()

    records = dataframe_to_records(dataframe)

    return [
        RevenueSummary.model_validate(record)
        for record in records
    ]

@router.get(
    "/api/v1/analytics/monthly-bookings",
    response_model=list[MonthlyBookingSummary],
    tags=["Analytics"],
    summary="Get monthly booking trends",
)
def get_monthly_bookings(
    repository: Annotated[
        HotelBookingRepository,
        Depends(get_booking_repository),
    ],
) -> list[MonthlyBookingSummary]:
    dataframe = repository.get_monthly_bookings()

    records = dataframe_to_records(dataframe)

    return [
        MonthlyBookingSummary.model_validate(record)
        for record in records
    ]
@router.get(
    "/api/v1/analytics/cancellation-rate",
    response_model=CancellationRateResponse,
    tags=["Analytics"],
    summary="Get cancellation metrics",
)
def get_cancellation_rate(
    repository: Annotated[
        HotelBookingRepository,
        Depends(get_booking_repository),
    ],
    hotel: Annotated[
        str | None,
        Query(
            description=(
                "Optional hotel filter, such as City Hotel "
                "or Resort Hotel."
            ),
        ),
    ] = None,
) -> CancellationRateResponse:
    dataframe = repository.get_cancellation_rate(
        hotel=hotel,
    )

    record = dataframe_to_records(dataframe)[0]

    return CancellationRateResponse.model_validate(
        record
    )

@router.get(
    "/api/v1/analytics/hotel-performance",
    response_model=list[HotelPerformanceSummary],
    tags=["Analytics"],
    summary="Compare hotel performance",
)
def get_hotel_performance(
    repository: Annotated[
        HotelBookingRepository,
        Depends(get_booking_repository),
    ],
) -> list[HotelPerformanceSummary]:
    dataframe = repository.get_hotel_performance()

    records = dataframe_to_records(dataframe)

    return [
        HotelPerformanceSummary.model_validate(record)
        for record in records
    ]