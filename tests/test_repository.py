from __future__ import annotations

import pandas as pd
import pytest
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine

from database.repository import HotelBookingRepository


@pytest.fixture
def test_engine() -> Engine:
    """
    Create an in-memory SQLite database for each test.
    """
    engine = create_engine(
        "sqlite:///:memory:",
        future=True,
    )

    dataframe = pd.DataFrame(
        {
            "booking_id": [1, 2, 3, 4],
            "hotel": [
                "City Hotel",
                "City Hotel",
                "Resort Hotel",
                "Resort Hotel",
            ],
            "is_canceled": [0, 1, 0, 0],
            "lead_time": [10, 20, 30, 40],
            "arrival_date_year": [2017, 2017, 2017, 2017],
            "arrival_date_month": [
                "July",
                "July",
                "August",
                "August",
            ],
            "arrival_date_week_number": [27, 27, 31, 31],
            "stays_in_weekend_nights": [1, 1, 2, 0],
            "stays_in_week_nights": [2, 3, 2, 4],
            "country": ["IND", "PRT", "IND", "GBR"],
            "adr": [100.0, 120.0, 80.0, 90.0],
            "reservation_status": [
                "Check-Out",
                "Canceled",
                "Check-Out",
                "Check-Out",
            ],
            "reservation_status_date": [
                "2017-07-01",
                "2017-07-02",
                "2017-08-01",
                "2017-08-02",
            ],
        }
    )

    dataframe.to_sql(
        name="hotel_bookings",
        con=engine,
        if_exists="replace",
        index=False,
    )

    return engine


@pytest.fixture
def repository(
    test_engine: Engine,
) -> HotelBookingRepository:
    """
    Return a repository connected to the temporary test database.
    """
    return HotelBookingRepository(
        engine=test_engine,
    )


def test_get_all_bookings(
    repository: HotelBookingRepository,
) -> None:
    result = repository.get_all_bookings(
        limit=2,
        offset=0,
    )

    assert len(result) == 2
    assert result["booking_id"].tolist() == [1, 2]


def test_get_all_bookings_applies_offset(
    repository: HotelBookingRepository,
) -> None:
    result = repository.get_all_bookings(
        limit=2,
        offset=2,
    )

    assert result["booking_id"].tolist() == [3, 4]


def test_get_all_bookings_rejects_invalid_limit(
    repository: HotelBookingRepository,
) -> None:
    with pytest.raises(
        ValueError,
        match="limit",
    ):
        repository.get_all_bookings(
            limit=0,
        )


def test_get_booking_by_id(
    repository: HotelBookingRepository,
) -> None:
    result = repository.get_booking_by_id(
        booking_id=1,
    )

    assert result is not None
    assert result["booking_id"] == 1
    assert result["country"] == "IND"


def test_get_booking_by_id_returns_none(
    repository: HotelBookingRepository,
) -> None:
    result = repository.get_booking_by_id(
        booking_id=999,
    )

    assert result is None


def test_get_bookings_by_country(
    repository: HotelBookingRepository,
) -> None:
    result = repository.get_bookings_by_country(
        country="ind",
        limit=10,
    )

    assert len(result) == 2
    assert set(result["country"]) == {"IND"}


def test_get_cancelled_bookings(
    repository: HotelBookingRepository,
) -> None:
    result = repository.get_cancelled_bookings(
        limit=10,
    )

    assert len(result) == 1
    assert result.iloc[0]["booking_id"] == 2
    assert result.iloc[0]["is_canceled"] == 1


def test_get_average_adr(
    repository: HotelBookingRepository,
) -> None:
    result = repository.get_average_adr()

    assert result == 97.5


def test_get_average_adr_by_hotel(
    repository: HotelBookingRepository,
) -> None:
    result = repository.get_average_adr(
        hotel="City Hotel",
    )

    assert result == 110.0


def test_get_top_countries(
    repository: HotelBookingRepository,
) -> None:
    result = repository.get_top_countries(
        limit=2,
    )

    assert result.iloc[0]["country"] == "IND"
    assert result.iloc[0]["total_bookings"] == 2


def test_get_monthly_bookings(
    repository: HotelBookingRepository,
) -> None:
    result = repository.get_monthly_bookings()

    assert len(result) == 2

    july = result.loc[
        result["month"] == "July"
    ].iloc[0]

    assert july["total_bookings"] == 2
    assert july["cancelled_bookings"] == 1
    assert july["cancellation_rate"] == 50.0


def test_get_average_stay(
    repository: HotelBookingRepository,
) -> None:
    result = repository.get_average_stay()

    assert result.iloc[0]["average_weekend_nights"] == 1.0
    assert result.iloc[0]["average_week_nights"] == 2.75
    assert result.iloc[0]["average_total_nights"] == 3.75


def test_get_revenue_summary(
    repository: HotelBookingRepository,
) -> None:
    result = repository.get_revenue_summary()

    city_hotel = result.loc[
        result["hotel"] == "City Hotel"
    ].iloc[0]

    resort_hotel = result.loc[
        result["hotel"] == "Resort Hotel"
    ].iloc[0]

    assert city_hotel["completed_bookings"] == 1
    assert city_hotel["estimated_revenue"] == 300.0

    assert resort_hotel["completed_bookings"] == 2
    assert resort_hotel["estimated_revenue"] == 680.0

def test_get_cancellation_rate(
    repository: HotelBookingRepository,
) -> None:
    result = repository.get_cancellation_rate()

    assert result.iloc[0]["total_bookings"] == 4
    assert result.iloc[0]["cancelled_bookings"] == 1
    assert result.iloc[0]["cancellation_rate"] == 25.0


def test_get_cancellation_rate_by_hotel(
    repository: HotelBookingRepository,
) -> None:
    result = repository.get_cancellation_rate(
        hotel="City Hotel",
    )

    assert result.iloc[0]["total_bookings"] == 2
    assert result.iloc[0]["cancelled_bookings"] == 1
    assert result.iloc[0]["cancellation_rate"] == 50.0


def test_get_hotel_performance(
    repository: HotelBookingRepository,
) -> None:
    result = repository.get_hotel_performance()

    assert set(result["hotel"]) == {
        "City Hotel",
        "Resort Hotel",
    }

    city_hotel = result.loc[
        result["hotel"] == "City Hotel"
    ].iloc[0]

    assert city_hotel["total_bookings"] == 2
    assert city_hotel["cancelled_bookings"] == 1
    assert city_hotel["cancellation_rate"] == 50.0