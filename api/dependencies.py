from database.repository import HotelBookingRepository


def get_booking_repository() -> HotelBookingRepository:
    """
    Return the repository used by API endpoints.

    Later, this dependency can be overridden during automated testing.
    """
    return HotelBookingRepository()