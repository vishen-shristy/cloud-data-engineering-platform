from __future__ import annotations

import logging
from pathlib import Path
from typing import Final

import pandas as pd

from ingestion.load_data import load_booking_data


PROJECT_ROOT: Final[Path] = Path(__file__).resolve().parents[1]

PROCESSED_DATA_PATH: Final[Path] = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "hotel_bookings_cleaned.csv"
)

LOG_PATH: Final[Path] = (
    PROJECT_ROOT
    / "logs"
    / "application.log"
)


def configure_logging() -> None:
    """
    Configure application logging.

    Logs are written both to the terminal and to logs/application.log.
    """
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)

    logging.basicConfig(
        level=logging.INFO,
        format=(
            "%(asctime)s | "
            "%(levelname)s | "
            "%(name)s | "
            "%(message)s"
        ),
        handlers=[
            logging.FileHandler(
                LOG_PATH,
                encoding="utf-8",
            ),
            logging.StreamHandler(),
        ],
        force=True,
    )


logger = logging.getLogger(__name__)


def clean_missing_values(
    dataframe: pd.DataFrame,
) -> pd.DataFrame:
    """
    Apply business-specific missing-value rules.

    Rules:
    - children -> 0
    - country -> "Unknown"
    - agent -> 0
    - company -> 0

    The input DataFrame is not modified directly.

    Args:
        dataframe: Raw hotel-booking DataFrame.

    Returns:
        A copied DataFrame with selected missing values filled.
    """
    cleaned_dataframe = dataframe.copy()

    missing_value_rules: dict[str, object] = {
        "children": 0,
        "country": "Unknown",
        "agent": 0,
        "company": 0,
    }

    for column, replacement_value in missing_value_rules.items():
        if column not in cleaned_dataframe.columns:
            logger.warning(
                "Column '%s' was not found. "
                "Missing-value cleaning was skipped for it.",
                column,
            )
            continue

        missing_before = int(
            cleaned_dataframe[column].isna().sum()
        )

        cleaned_dataframe[column] = (
            cleaned_dataframe[column]
            .fillna(replacement_value)
        )

        logger.info(
            "Filled %s missing values in '%s' with %r.",
            missing_before,
            column,
            replacement_value,
        )

    return cleaned_dataframe


def remove_duplicates(
    dataframe: pd.DataFrame,
) -> pd.DataFrame:
    """
    Remove exact duplicate rows.

    The first occurrence is retained.

    Args:
        dataframe: Hotel-booking DataFrame.

    Returns:
        A copied DataFrame without exact duplicate rows.
    """
    duplicate_count = int(
        dataframe.duplicated().sum()
    )

    cleaned_dataframe = (
        dataframe
        .drop_duplicates()
        .reset_index(drop=True)
        .copy()
    )

    logger.info(
        "Removed %s duplicate rows.",
        duplicate_count,
    )

    return cleaned_dataframe

def standardize_data_types(
    dataframe: pd.DataFrame,
) -> pd.DataFrame:
    """
    Standardize selected columns to appropriate data types.

    Args:
        dataframe: Hotel-booking DataFrame.

    Returns:
        Cleaned DataFrame with standardized data types.
    """
    cleaned_dataframe = dataframe.copy()

    # -----------------------------
    # Convert numeric columns
    # -----------------------------
    integer_columns = [
        "children",
        "agent",
        "company",
    ]

    for column in integer_columns:
        if column in cleaned_dataframe.columns:
            cleaned_dataframe[column] = (
                pd.to_numeric(
                    cleaned_dataframe[column],
                    errors="coerce",
                )
                .fillna(0)
                .astype("int64")
            )

            logger.info(
                "Converted '%s' to int64.",
                column,
            )

    # -----------------------------
    # Reservation Status Date
    # -----------------------------
    if "reservation_status_date" in cleaned_dataframe.columns:
        reservation_dates = pd.to_datetime(
        cleaned_dataframe["reservation_status_date"],
        errors="coerce",
    )

    invalid_reservation_dates = int(
        reservation_dates.isna().sum()
    )

    if invalid_reservation_dates > 0:
        raise ValueError(
            "Found "
            f"{invalid_reservation_dates} invalid values in "
            "'reservation_status_date'."
        )

    cleaned_dataframe["reservation_status_date"] = (
        reservation_dates
    )

    logger.info(
        "Converted 'reservation_status_date' to datetime."
    )

    # -----------------------------
    # Arrival Date
    # -----------------------------
    arrival_columns = [
        "arrival_date_year",
        "arrival_date_month",
        "arrival_date_day_of_month",
    ]

    if all(
        column in cleaned_dataframe.columns
        for column in arrival_columns
    ):

        month_mapping = {
            "January": 1,
            "February": 2,
            "March": 3,
            "April": 4,
            "May": 5,
            "June": 6,
            "July": 7,
            "August": 8,
            "September": 9,
            "October": 10,
            "November": 11,
            "December": 12,
        }

        arrival_dataframe = pd.DataFrame(
            {
                "year": cleaned_dataframe[
                    "arrival_date_year"
                ],
                "month": cleaned_dataframe[
                    "arrival_date_month"
                ].map(month_mapping),
                "day": cleaned_dataframe[
                    "arrival_date_day_of_month"
                ],
            }
        )

        cleaned_dataframe["arrival_date"] = pd.to_datetime(
            arrival_dataframe,
            errors="coerce",
        )

        invalid_dates = int(
            cleaned_dataframe["arrival_date"]
            .isna()
            .sum()
        )

        if invalid_dates > 0:
            logger.warning(
                "%s invalid arrival dates found.",
                invalid_dates,
            )

        logger.info(
            "Created standardized 'arrival_date' column."
        )

    return cleaned_dataframe


def remove_invalid_guest_records(
    dataframe: pd.DataFrame,
) -> pd.DataFrame:
    """
    Remove bookings where adults, children, and babies are all zero.

    Args:
        dataframe: Hotel-booking DataFrame.

    Returns:
        A copied DataFrame without zero-guest bookings.
    """
    required_columns = {
        "adults",
        "children",
        "babies",
    }

    if not required_columns.issubset(
        dataframe.columns
    ):
        logger.warning(
            "Zero-guest validation was skipped because "
            "one or more guest columns are missing."
        )
        return dataframe.copy()

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

    invalid_guest_mask = (
        (adults == 0)
        & (children == 0)
        & (babies == 0)
    )

    invalid_guest_count = int(
        invalid_guest_mask.sum()
    )

    cleaned_dataframe = (
        dataframe
        .loc[~invalid_guest_mask]
        .reset_index(drop=True)
        .copy()
    )

    logger.info(
        "Removed %s bookings without guests.",
        invalid_guest_count,
    )

    return cleaned_dataframe


def save_cleaned_data(
    dataframe: pd.DataFrame,
    output_path: Path = PROCESSED_DATA_PATH,
) -> Path:
    """
    Save the cleaned DataFrame as a CSV file.

    Args:
        dataframe: Cleaned hotel-booking DataFrame.
        output_path: Destination path.

    Returns:
        The path where the cleaned dataset was saved.
    """
    output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    dataframe.to_csv(
        output_path,
        index=False,
    )

    logger.info(
        "Saved %s cleaned rows to %s.",
        len(dataframe),
        output_path,
    )

    return output_path


def clean_booking_data(
    dataframe: pd.DataFrame,
) -> pd.DataFrame:
    """
    Execute the complete cleaning pipeline.

    Pipeline:
    1. Fill selected missing values.
    2. Remove exact duplicates.
    3. Remove bookings without guests.
    4. Standardize data types and dates.

    Args:
        dataframe: Raw hotel-booking DataFrame.

    Returns:
        Fully cleaned DataFrame.
    """
    logger.info(
        "Starting cleaning pipeline with %s rows.",
        len(dataframe),
    )

    cleaned_dataframe = clean_missing_values(
        dataframe
    )

    cleaned_dataframe = remove_duplicates(
        cleaned_dataframe
    )

    cleaned_dataframe = remove_invalid_guest_records(
        cleaned_dataframe
    )

    cleaned_dataframe = standardize_data_types(
        cleaned_dataframe
    )

    logger.info(
        "Cleaning pipeline completed with %s rows.",
        len(cleaned_dataframe),
    )

    return cleaned_dataframe


def main() -> None:
    configure_logging()

    logger.info(
        "Loading raw hotel-booking dataset."
    )

    raw_dataframe = load_booking_data()

    cleaned_dataframe = clean_booking_data(
        raw_dataframe
    )

    output_path = save_cleaned_data(
        cleaned_dataframe
    )

    print("=" * 70)
    print("HOTEL BOOKING DATA CLEANING COMPLETED")
    print("=" * 70)
    print(f"Raw rows: {len(raw_dataframe):,}")
    print(f"Cleaned rows: {len(cleaned_dataframe):,}")
    print(f"Output file: {output_path}")


if __name__ == "__main__":
    main()