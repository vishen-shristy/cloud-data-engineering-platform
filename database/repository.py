from __future__ import annotations

from typing import Any

import pandas as pd
from sqlalchemy import text
from sqlalchemy.engine import Engine

from database.create_database import get_engine


class HotelBookingRepository:
    """
    Repository for querying hotel-booking data.

    The repository keeps SQL queries separate from the API and business logic.
    """

    def __init__(
        self,
        engine: Engine | None = None,
    ) -> None:
        """
        Initialize the repository.

        Args:
            engine: Optional SQLAlchemy engine. A default engine is created
                when one is not supplied.
        """
        self.engine = engine or get_engine()

    def get_all_bookings(
        self,
        limit: int = 100,
        offset: int = 0,
    ) -> pd.DataFrame:
        """
        Return bookings using pagination.

        Args:
            limit: Maximum number of rows to return.
            offset: Number of rows to skip.

        Returns:
            DataFrame containing booking records.

        Raises:
            ValueError: If limit is not positive or offset is negative.
        """
        if limit <= 0:
            raise ValueError("limit must be greater than 0.")

        if offset < 0:
            raise ValueError("offset cannot be negative.")

        query = text(
            """
            SELECT *
            FROM hotel_bookings
            ORDER BY booking_id
            LIMIT :limit
            OFFSET :offset
            """
        )

        return pd.read_sql_query(
            sql=query,
            con=self.engine,
            params={
                "limit": limit,
                "offset": offset,
            },
        )

    def get_booking_by_id(
        self,
        booking_id: int,
    ) -> dict[str, Any] | None:
        """
        Return one booking by its booking ID.

        Args:
            booking_id: Unique booking identifier.

        Returns:
            Booking dictionary, or None when no booking is found.

        Raises:
            ValueError: If booking_id is not positive.
        """
        if booking_id <= 0:
            raise ValueError(
                "booking_id must be greater than 0."
            )

        query = text(
            """
            SELECT *
            FROM hotel_bookings
            WHERE booking_id = :booking_id
            """
        )

        dataframe = pd.read_sql_query(
            sql=query,
            con=self.engine,
            params={
                "booking_id": booking_id,
            },
        )

        if dataframe.empty:
            return None

        return dataframe.iloc[0].to_dict()

    def get_bookings_by_country(
        self,
        country: str,
        limit: int = 100,
    ) -> pd.DataFrame:
        """
        Return bookings for a specific country.

        Args:
            country: Country code, such as PRT or GBR.
            limit: Maximum number of rows to return.

        Returns:
            Matching booking records.

        Raises:
            ValueError: If country is empty or limit is invalid.
        """
        normalized_country = country.strip().upper()

        if not normalized_country:
            raise ValueError("country cannot be empty.")

        if limit <= 0:
            raise ValueError("limit must be greater than 0.")

        query = text(
            """
            SELECT *
            FROM hotel_bookings
            WHERE UPPER(country) = :country
            ORDER BY booking_id
            LIMIT :limit
            """
        )

        return pd.read_sql_query(
            sql=query,
            con=self.engine,
            params={
                "country": normalized_country,
                "limit": limit,
            },
        )

    def get_cancelled_bookings(
        self,
        limit: int = 100,
    ) -> pd.DataFrame:
        """
        Return cancelled bookings.

        Args:
            limit: Maximum number of records to return.

        Returns:
            Cancelled booking records.
        """
        if limit <= 0:
            raise ValueError("limit must be greater than 0.")

        query = text(
            """
            SELECT *
            FROM hotel_bookings
            WHERE is_canceled = 1
            ORDER BY reservation_status_date DESC
            LIMIT :limit
            """
        )

        return pd.read_sql_query(
            sql=query,
            con=self.engine,
            params={
                "limit": limit,
            },
        )

    def get_average_adr(
        self,
        hotel: str | None = None,
    ) -> float:
        """
        Return the average daily rate.

        Args:
            hotel: Optional hotel type, such as City Hotel or Resort Hotel.

        Returns:
            Average daily rate rounded to two decimals.
        """
        if hotel is None:
            query = text(
                """
                SELECT AVG(adr) AS average_adr
                FROM hotel_bookings
                WHERE adr IS NOT NULL
                """
            )

            params: dict[str, Any] = {}
        else:
            normalized_hotel = hotel.strip()

            if not normalized_hotel:
                raise ValueError("hotel cannot be empty.")

            query = text(
                """
                SELECT AVG(adr) AS average_adr
                FROM hotel_bookings
                WHERE adr IS NOT NULL
                  AND LOWER(hotel) = LOWER(:hotel)
                """
            )

            params = {
                "hotel": normalized_hotel,
            }

        dataframe = pd.read_sql_query(
            sql=query,
            con=self.engine,
            params=params,
        )

        average_adr = dataframe.loc[0, "average_adr"]

        if pd.isna(average_adr):
            return 0.0

        return round(float(average_adr), 2)

    def get_top_countries(
        self,
        limit: int = 10,
    ) -> pd.DataFrame:
        """
        Return countries with the highest number of bookings.

        Args:
            limit: Number of countries to return.

        Returns:
            Country-level booking counts.
        """
        if limit <= 0:
            raise ValueError("limit must be greater than 0.")

        query = text(
            """
            SELECT
                country,
                COUNT(*) AS total_bookings
            FROM hotel_bookings
            WHERE country IS NOT NULL
              AND country <> ''
            GROUP BY country
            ORDER BY total_bookings DESC, country ASC
            LIMIT :limit
            """
        )

        return pd.read_sql_query(
            sql=query,
            con=self.engine,
            params={
                "limit": limit,
            },
        )

    def get_monthly_bookings(self) -> pd.DataFrame:
        """
        Return monthly booking totals and cancellation metrics.

        Returns:
            Monthly analytical summary.
        """
        query = text(
            """
            SELECT
                arrival_date_year AS year,
                arrival_date_month AS month,
                arrival_date_week_number AS week_number,
                COUNT(*) AS total_bookings,
                SUM(is_canceled) AS cancelled_bookings,
                ROUND(
                    AVG(CAST(is_canceled AS REAL)) * 100,
                    2
                ) AS cancellation_rate
            FROM hotel_bookings
            GROUP BY
                arrival_date_year,
                arrival_date_month,
                arrival_date_week_number
            ORDER BY
                arrival_date_year,
                arrival_date_week_number
            """
        )

        return pd.read_sql_query(
            sql=query,
            con=self.engine,
        )

    def get_average_stay(
        self,
        hotel: str | None = None,
    ) -> pd.DataFrame:
        """
        Return average weekend, weekday, and total stay lengths.

        Args:
            hotel: Optional hotel type filter.

        Returns:
            DataFrame containing average stay metrics.
        """
        if hotel is None:
            query = text(
                """
                SELECT
                    ROUND(
                        AVG(stays_in_weekend_nights),
                        2
                    ) AS average_weekend_nights,
                    ROUND(
                        AVG(stays_in_week_nights),
                        2
                    ) AS average_week_nights,
                    ROUND(
                        AVG(
                            stays_in_weekend_nights
                            + stays_in_week_nights
                        ),
                        2
                    ) AS average_total_nights
                FROM hotel_bookings
                """
            )

            params: dict[str, Any] = {}
        else:
            normalized_hotel = hotel.strip()

            if not normalized_hotel:
                raise ValueError("hotel cannot be empty.")

            query = text(
                """
                SELECT
                    ROUND(
                        AVG(stays_in_weekend_nights),
                        2
                    ) AS average_weekend_nights,
                    ROUND(
                        AVG(stays_in_week_nights),
                        2
                    ) AS average_week_nights,
                    ROUND(
                        AVG(
                            stays_in_weekend_nights
                            + stays_in_week_nights
                        ),
                        2
                    ) AS average_total_nights
                FROM hotel_bookings
                WHERE LOWER(hotel) = LOWER(:hotel)
                """
            )

            params = {
                "hotel": normalized_hotel,
            }

        return pd.read_sql_query(
            sql=query,
            con=self.engine,
            params=params,
        )

    def get_revenue_summary(self) -> pd.DataFrame:
        """
        Return estimated booking revenue metrics.

        Estimated revenue is calculated using:

        adr * total stayed nights

        Cancelled bookings are excluded.

        Returns:
            Revenue metrics grouped by hotel type.
        """
        query = text(
            """
            SELECT
                hotel,
                COUNT(*) AS completed_bookings,
                ROUND(AVG(adr), 2) AS average_adr,
                ROUND(
                    SUM(
                        adr * (
                            stays_in_weekend_nights
                            + stays_in_week_nights
                        )
                    ),
                    2
                ) AS estimated_revenue
            FROM hotel_bookings
            WHERE is_canceled = 0
              AND adr IS NOT NULL
              AND adr >= 0
            GROUP BY hotel
            ORDER BY estimated_revenue DESC
            """
        )

        return pd.read_sql_query(
            sql=query,
            con=self.engine,
        )