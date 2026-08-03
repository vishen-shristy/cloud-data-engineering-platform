import pandas as pd

from ingestion.validate_data import (
    build_validation_report,
    get_invalid_guest_records,
    get_missing_columns,
    get_missing_value_report,
)


def test_missing_value_report() -> None:
    dataframe = pd.DataFrame(
        {
            "hotel": [
                "City Hotel",
                None,
            ],
            "lead_time": [
                10,
                20,
            ],
        }
    )

    report = get_missing_value_report(dataframe)

    hotel_report = next(
        item
        for item in report
        if item["column"] == "hotel"
    )

    assert hotel_report["missing_count"] == 1
    assert hotel_report["missing_percentage"] == 50.0


def test_detects_booking_without_guests() -> None:
    dataframe = pd.DataFrame(
        {
            "adults": [2, 0, 0],
            "children": [0, 0, 1],
            "babies": [0, 0, 0],
        }
    )

    result = get_invalid_guest_records(dataframe)

    assert result == 1


def test_detects_missing_expected_columns() -> None:
    dataframe = pd.DataFrame(
        {
            "hotel": [
                "City Hotel",
            ]
        }
    )

    missing_columns = get_missing_columns(dataframe)

    assert "is_canceled" in missing_columns
    assert "lead_time" in missing_columns


def test_build_validation_report() -> None:
    dataframe = pd.DataFrame(
        {
            "hotel": [
                "City Hotel",
                "City Hotel",
            ],
            "is_canceled": [
                0,
                0,
            ],
            "adults": [
                2,
                2,
            ],
            "children": [
                0,
                0,
            ],
            "babies": [
                0,
                0,
            ],
            "stays_in_weekend_nights": [
                1,
                1,
            ],
            "stays_in_week_nights": [
                2,
                2,
            ],
        }
    )

    report = build_validation_report(dataframe)

    assert report["dataset_summary"]["row_count"] == 2
    assert report["dataset_summary"]["duplicate_row_count"] == 1