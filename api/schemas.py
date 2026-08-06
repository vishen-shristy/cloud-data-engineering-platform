from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict


class HealthResponse(BaseModel):
    status: str
    message: str


class BookingResponse(BaseModel):
    """
    Flexible response model for a hotel-booking record.

    Extra fields are allowed because the database table currently contains
    the complete hotel-booking dataset.
    """

    model_config = ConfigDict(extra="allow")

    booking_id: int
    hotel: str
    is_canceled: int
    lead_time: int
    country: str | None = None
    adr: float | None = None


class BookingListResponse(BaseModel):
    total: int
    limit: int
    offset: int
    data: list[dict[str, Any]]


class ErrorResponse(BaseModel):
    detail: str

class CountryBookingSummary(BaseModel):
    country: str
    total_bookings: int


class CancellationRateResponse(BaseModel):
    total_bookings: int
    cancelled_bookings: int
    cancellation_rate: float


class MonthlyBookingSummary(BaseModel):
    year: int
    month: str
    total_bookings: int
    cancelled_bookings: int
    cancellation_rate: float
    average_adr: float | None = None


class RevenueSummary(BaseModel):
    hotel: str
    completed_bookings: int
    average_adr: float | None = None
    estimated_revenue: float


class HotelPerformanceSummary(BaseModel):
    hotel: str
    total_bookings: int
    cancelled_bookings: int
    cancellation_rate: float
    average_adr: float | None = None
    average_stay_nights: float | None = None
    estimated_booking_value: float