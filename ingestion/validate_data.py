import json
from pathlib import Path
from typing import Any

import pandas as pd

try:
    from ingestion.load_data import load_booking_data
except ModuleNotFoundError:
    from load_data import load_booking_data


PROJECT_ROOT = Path(__file__).resolve().parents[1]
REPORT_DIRECTORY = PROJECT_ROOT / "logs"
REPORT_PATH = REPORT_DIRECTORY / "data_validation_report.json"

EXPECTED_COLUMNS = {
    "hotel",
    "is_canceled",
    "lead_time",
    "arrival_date_year",
    "arrival_date_month",
    "arrival_date_week_number",
    "arrival_date_day_of_month",
    "stays_in_weekend_nights",
    "stays_in_week_nights",
    "adults",
    "children",
    "babies",
    "meal",
    "country",
    "market_segment",
    "distribution_channel",
    "is_repeated_guest",
    "previous_cancellations",
    "previous_bookings_not_canceled",
    "reserved_room_type",
    "assigned_room_type",
    "booking_changes",
    "deposit_type",
    "agent",
    "company",
    "days_in_waiting_list",
    "customer_type",
    "adr",
    "required_car_parking_spaces",
    "total_of_special_requests",
    "reservation_status",
    "reservation_status_date",
}

EXPECTED_HOTEL_VALUES = {
    "City Hotel",
    "Resort Hotel",
}

EXPECTED_BINARY_VALUES = {
    0,
    1,
}

VALID_MONTHS = {
    "January",
    "February",
    "March",
    "April",
    "May",
    "June",
    "July",
    "August",
    "September",
    "October",
    "November",
    "December",
}

EXPECTED_RESERVATION_STATUSES = {
    "Check-Out",
    "Canceled",
    "No-Show",
}

NON_NEGATIVE_COLUMNS = [
    "lead_time",
    "stays_in_weekend_nights",
    "stays_in_week_nights",
    "adults",
    "children",
    "babies",
    "previous_cancellations",
    "previous_bookings_not_canceled",
    "booking_changes",
    "days_in_waiting_list",
    "required_car_parking_spaces",
    "total_of_special_requests",
]


def convert_to_serializable(value: Any) -> Any:
    """
    Convert pandas and NumPy values into JSON-serializable Python values.
    """
    if pd.isna(value):
        return None

    if hasattr(value, "item"):
        return value.item()

    return value


def get_missing_value_report(
    dataframe: pd.DataFrame,
) -> list[dict[str, Any]]:
    """
    Return missing-value counts and percentages for each column.
    """
    total_rows = len(dataframe)
    missing_counts = dataframe.isna().sum()

    report: list[dict[str, Any]] = []

    for column, missing_count in missing_counts.items():
        missing_percentage = (
            float(missing_count) / total_rows * 100
            if total_rows > 0
            else 0.0
        )

        report.append(
            {
                "column": column,
                "missing_count": int(missing_count),
                "missing_percentage": round(
                    missing_percentage,
                    2,
                ),
            }
        )

    return sorted(
        report,
        key=lambda item: item["missing_count"],
        reverse=True,
    )


def get_data_type_report(
    dataframe: pd.DataFrame,
) -> dict[str, str]:
    """
    Return the detected pandas data type for every column.
    """
    return {
        column: str(dtype)
        for column, dtype in dataframe.dtypes.items()
    }


def get_unexpected_columns(
    dataframe: pd.DataFrame,
) -> list[str]:
    """
    Return columns that are present but not part of the expected schema.
    """
    actual_columns = set(dataframe.columns)
    return sorted(actual_columns - EXPECTED_COLUMNS)


def get_missing_columns(
    dataframe: pd.DataFrame,
) -> list[str]:
    """
    Return expected columns that are missing from the dataset.
    """
    actual_columns = set(dataframe.columns)
    return sorted(EXPECTED_COLUMNS - actual_columns)


def get_invalid_categorical_values(
    dataframe: pd.DataFrame,
) -> dict[str, list[Any]]:
    """
    Find unexpected values in key categorical columns.
    """
    checks: dict[str, set[Any]] = {
        "hotel": EXPECTED_HOTEL_VALUES,
        "is_canceled": EXPECTED_BINARY_VALUES,
        "is_repeated_guest": EXPECTED_BINARY_VALUES,
        "arrival_date_month": VALID_MONTHS,
        "reservation_status": EXPECTED_RESERVATION_STATUSES,
    }

    invalid_values: dict[str, list[Any]] = {}

    for column, valid_values in checks.items():
        if column not in dataframe.columns:
            continue

        actual_values = set(
            dataframe[column]
            .dropna()
            .map(convert_to_serializable)
            .unique()
            .tolist()
        )

        unexpected_values = actual_values - valid_values

        if unexpected_values:
            invalid_values[column] = sorted(
                unexpected_values,
                key=str,
            )

    return invalid_values


def get_negative_value_report(
    dataframe: pd.DataFrame,
) -> dict[str, int]:
    """
    Count negative values in columns that should never be negative.
    """
    report: dict[str, int] = {}

    for column in NON_NEGATIVE_COLUMNS:
        if column not in dataframe.columns:
            continue

        numeric_series = pd.to_numeric(
            dataframe[column],
            errors="coerce",
        )

        negative_count = int((numeric_series < 0).sum())

        if negative_count > 0:
            report[column] = negative_count

    return report


def get_invalid_guest_records(
    dataframe: pd.DataFrame,
) -> int:
    """
    Count bookings where adults, children, and babies are all zero.

    Such rows represent reservations without any guests and are usually
    considered invalid from a business perspective.
    """
    required_columns = {"adults", "children", "babies"}

    if not required_columns.issubset(dataframe.columns):
        return 0

    adults = pd.to_numeric(
        dataframe["adults"],
        errors="coerce",
    ).fillna(0)

    children = pd.to_numeric(
        dataframe["children"],
        errors="coerce",
    ).fillna(0)

    babies = pd.to_numeric(
        dataframe["babies"],
        errors="coerce",
    ).fillna(0)

    invalid_mask = (
        (adults == 0)
        & (children == 0)
        & (babies == 0)
    )

    return int(invalid_mask.sum())


def get_invalid_stay_records(
    dataframe: pd.DataFrame,
) -> int:
    """
    Count bookings where both weekend and weekday stay lengths are zero.
    """
    required_columns = {
        "stays_in_weekend_nights",
        "stays_in_week_nights",
    }

    if not required_columns.issubset(dataframe.columns):
        return 0

    weekend_nights = pd.to_numeric(
        dataframe["stays_in_weekend_nights"],
        errors="coerce",
    ).fillna(0)

    weekday_nights = pd.to_numeric(
        dataframe["stays_in_week_nights"],
        errors="coerce",
    ).fillna(0)

    invalid_mask = (
        (weekend_nights == 0)
        & (weekday_nights == 0)
    )

    return int(invalid_mask.sum())


def get_invalid_arrival_dates(
    dataframe: pd.DataFrame,
) -> int:
    """
    Count rows that cannot form a valid arrival date.
    """
    required_columns = {
        "arrival_date_year",
        "arrival_date_month",
        "arrival_date_day_of_month",
    }

    if not required_columns.issubset(dataframe.columns):
        return 0

    date_components = (
        dataframe[
            [
                "arrival_date_year",
                "arrival_date_month",
                "arrival_date_day_of_month",
            ]
        ]
        .rename(
            columns={
                "arrival_date_year": "year",
                "arrival_date_month": "month",
                "arrival_date_day_of_month": "day",
            }
        )
        .copy()
    )

    parsed_dates = pd.to_datetime(
        date_components,
        errors="coerce",
    )

    return int(parsed_dates.isna().sum())


def get_invalid_reservation_status_dates(
    dataframe: pd.DataFrame,
) -> int:
    """
    Count reservation status dates that cannot be parsed.
    """
    if "reservation_status_date" not in dataframe.columns:
        return 0

    parsed_dates = pd.to_datetime(
        dataframe["reservation_status_date"],
        errors="coerce",
    )

    return int(parsed_dates.isna().sum())


def build_validation_report(
    dataframe: pd.DataFrame,
) -> dict[str, Any]:
    """
    Build a complete validation report for the dataset.
    """
    duplicate_count = int(dataframe.duplicated().sum())

    report: dict[str, Any] = {
        "dataset_summary": {
            "row_count": int(dataframe.shape[0]),
            "column_count": int(dataframe.shape[1]),
            "duplicate_row_count": duplicate_count,
            "duplicate_percentage": round(
                duplicate_count / len(dataframe) * 100,
                2,
            )
            if len(dataframe) > 0
            else 0.0,
        },
        "schema_validation": {
            "missing_columns": get_missing_columns(dataframe),
            "unexpected_columns": get_unexpected_columns(dataframe),
            "column_data_types": get_data_type_report(dataframe),
        },
        "missing_values": get_missing_value_report(dataframe),
        "invalid_categorical_values": (
            get_invalid_categorical_values(dataframe)
        ),
        "invalid_numerical_values": {
            "negative_value_counts": (
                get_negative_value_report(dataframe)
            ),
            "bookings_without_guests": (
                get_invalid_guest_records(dataframe)
            ),
            "bookings_without_nights": (
                get_invalid_stay_records(dataframe)
            ),
        },
        "date_validation": {
            "invalid_arrival_dates": (
                get_invalid_arrival_dates(dataframe)
            ),
            "invalid_reservation_status_dates": (
                get_invalid_reservation_status_dates(dataframe)
            ),
        },
    }

    return report


def save_validation_report(
    report: dict[str, Any],
    report_path: Path = REPORT_PATH,
) -> None:
    """
    Save the validation report as formatted JSON.
    """
    report_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with report_path.open(
        mode="w",
        encoding="utf-8",
    ) as report_file:
        json.dump(
            report,
            report_file,
            indent=2,
            ensure_ascii=False,
        )


def print_validation_summary(
    report: dict[str, Any],
) -> None:
    """
    Print the most important validation findings.
    """
    dataset_summary = report["dataset_summary"]
    schema_validation = report["schema_validation"]
    numerical_validation = report["invalid_numerical_values"]
    date_validation = report["date_validation"]

    missing_columns = schema_validation["missing_columns"]
    unexpected_columns = schema_validation["unexpected_columns"]

    columns_with_missing_values = [
        item
        for item in report["missing_values"]
        if item["missing_count"] > 0
    ]

    print("=" * 70)
    print("HOTEL BOOKING DATA VALIDATION REPORT")
    print("=" * 70)

    print(
        f"Rows: {dataset_summary['row_count']:,}"
    )
    print(
        f"Columns: {dataset_summary['column_count']}"
    )
    print(
        "Duplicate rows: "
        f"{dataset_summary['duplicate_row_count']:,} "
        f"({dataset_summary['duplicate_percentage']}%)"
    )

    print("\nSchema validation:")
    print(
        f"- Missing columns: "
        f"{missing_columns or 'None'}"
    )
    print(
        f"- Unexpected columns: "
        f"{unexpected_columns or 'None'}"
    )

    print("\nColumns containing missing values:")

    if not columns_with_missing_values:
        print("- None")
    else:
        for item in columns_with_missing_values:
            print(
                f"- {item['column']}: "
                f"{item['missing_count']:,} "
                f"({item['missing_percentage']}%)"
            )

    print("\nBusiness-rule validation:")
    print(
        "- Bookings without guests: "
        f"{numerical_validation['bookings_without_guests']:,}"
    )
    print(
        "- Bookings without nights: "
        f"{numerical_validation['bookings_without_nights']:,}"
    )
    print(
        "- Invalid arrival dates: "
        f"{date_validation['invalid_arrival_dates']:,}"
    )
    print(
        "- Invalid reservation-status dates: "
        f"{date_validation['invalid_reservation_status_dates']:,}"
    )

    print(
        "\nFull JSON report saved to:"
        f"\n{REPORT_PATH}"
    )


def main() -> None:
    dataframe = load_booking_data()
    report = build_validation_report(dataframe)
    save_validation_report(report)
    print_validation_summary(report)


if __name__ == "__main__":
    main()