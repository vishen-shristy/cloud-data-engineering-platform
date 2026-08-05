from database.repository import HotelBookingRepository


def main() -> None:
    repository = HotelBookingRepository()

    print("\nFirst five bookings:")
    print(
        repository.get_all_bookings(
            limit=5,
        )
    )

    print("\nBooking ID 1:")
    print(
        repository.get_booking_by_id(
            booking_id=1,
        )
    )

    print("\nTop five countries:")
    print(
        repository.get_top_countries(
            limit=5,
        )
    )

    print("\nAverage ADR:")
    print(
        repository.get_average_adr()
    )

    print("\nAverage stay:")
    print(
        repository.get_average_stay()
    )

    print("\nRevenue summary:")
    print(
        repository.get_revenue_summary()
    )


if __name__ == "__main__":
    main()