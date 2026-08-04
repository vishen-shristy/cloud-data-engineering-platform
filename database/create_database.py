from __future__ import annotations

import logging
from pathlib import Path
from typing import Final

import pandas as pd
from sqlalchemy import create_engine, inspect
from sqlalchemy.engine import Engine

from database.database_config import DATABASE_PATH, DATABASE_URL


PROJECT_ROOT: Final[Path] = Path(__file__).resolve().parents[1]

CLEANED_DATA_PATH: Final[Path] = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "hotel_bookings_cleaned.csv"
)

TABLE_NAME: Final[str] = "hotel_bookings"

logger = logging.getLogger(__name__)


def get_engine() -> Engine:
    """
    Create and return the SQLAlchemy database engine.
    """
    DATABASE_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    return create_engine(
        DATABASE_URL,
        future=True,
    )


def load_cleaned_data(
    file_path: Path = CLEANED_DATA_PATH,
) -> pd.DataFrame:
    """
    Load the cleaned hotel-booking CSV.

    Args:
        file_path: Path to the cleaned CSV file.

    Returns:
        Cleaned hotel-booking DataFrame.

    Raises:
        FileNotFoundError: If the cleaned CSV does not exist.
        ValueError: If the cleaned CSV contains no rows.
    """
    if not file_path.exists():
        raise FileNotFoundError(
            f"Cleaned dataset was not found at: {file_path}"
        )

    dataframe = pd.read_csv(
        file_path,
        parse_dates=[
            "reservation_status_date",
            "arrival_date",
        ],
    )

    if dataframe.empty:
        raise ValueError(
            "The cleaned dataset contains no rows."
        )

    return dataframe


def prepare_database_dataframe(
    dataframe: pd.DataFrame,
) -> pd.DataFrame:
    """
    Prepare the cleaned DataFrame for database insertion.

    A booking_id column is added as the table's unique identifier.

    Args:
        dataframe: Cleaned hotel-booking DataFrame.

    Returns:
        Database-ready DataFrame.
    """
    database_dataframe = (
        dataframe
        .reset_index(drop=True)
        .copy()
    )

    database_dataframe.insert(
        loc=0,
        column="booking_id",
        value=range(
            1,
            len(database_dataframe) + 1,
        ),
    )

    return database_dataframe


def create_and_load_database(
    dataframe: pd.DataFrame,
    engine: Engine,
    table_name: str = TABLE_NAME,
) -> None:
    """
    Create or replace the hotel_bookings table and load all rows.

    Args:
        dataframe: Database-ready hotel-booking DataFrame.
        engine: SQLAlchemy database engine.
        table_name: Destination table name.
    """
    dataframe.to_sql(
    name=table_name,
    con=engine,
    if_exists="replace",
    index=False,
    chunksize=500,
    )

    logger.info(
        "Loaded %s rows into table '%s'.",
        len(dataframe),
        table_name,
    )


def verify_database(
    engine: Engine,
    table_name: str = TABLE_NAME,
) -> None:
    """
    Verify that the table exists and contains records.

    Args:
        engine: SQLAlchemy database engine.
        table_name: Table to verify.

    Raises:
        RuntimeError: If the table was not created.
    """
    inspector = inspect(engine)

    if not inspector.has_table(table_name):
        raise RuntimeError(
            f"Table '{table_name}' was not created."
        )

    row_count_query = (
        f"SELECT COUNT(*) AS row_count "
        f"FROM {table_name}"
    )

    result = pd.read_sql_query(
        row_count_query,
        con=engine,
    )

    row_count = int(
        result.loc[0, "row_count"]
    )

    print("=" * 70)
    print("DATABASE CREATION COMPLETED")
    print("=" * 70)
    print(f"Database: {DATABASE_PATH}")
    print(f"Table: {table_name}")
    print(f"Rows loaded: {row_count:,}")


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format=(
            "%(asctime)s | "
            "%(levelname)s | "
            "%(name)s | "
            "%(message)s"
        ),
    )

    cleaned_dataframe = load_cleaned_data()

    database_dataframe = prepare_database_dataframe(
        cleaned_dataframe
    )

    engine = get_engine()

    create_and_load_database(
        dataframe=database_dataframe,
        engine=engine,
    )

    verify_database(
        engine=engine,
    )


if __name__ == "__main__":
    main()