from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
RAW_DATA_PATH = PROJECT_ROOT / "data" / "raw" / "hotel_bookings.csv"


def load_booking_data(file_path: Path = RAW_DATA_PATH) -> pd.DataFrame:
    """
    Load the raw hotel-booking dataset.

    Args:
        file_path: Path to the source CSV file.

    Returns:
        A pandas DataFrame containing the booking data.

    Raises:
        FileNotFoundError: If the CSV file does not exist.
        ValueError: If the CSV file is empty.
        RuntimeError: If pandas cannot read the file.
    """
    if not file_path.exists():
        raise FileNotFoundError(
            f"Dataset was not found at: {file_path}"
        )

    try:
        dataframe = pd.read_csv(file_path)
    except pd.errors.EmptyDataError as exc:
        raise ValueError(
            f"The dataset is empty: {file_path}"
        ) from exc
    except pd.errors.ParserError as exc:
        raise RuntimeError(
            f"The dataset could not be parsed: {file_path}"
        ) from exc
    except Exception as exc:
        raise RuntimeError(
            f"Unexpected error while loading dataset: {exc}"
        ) from exc

    if dataframe.empty:
        raise ValueError("The loaded dataset contains no rows.")

    return dataframe


def display_dataset_summary(dataframe: pd.DataFrame) -> None:
    """
    Display basic information about the loaded dataset.

    Args:
        dataframe: Hotel-booking DataFrame.
    """
    rows, columns = dataframe.shape

    print("=" * 60)
    print("HOTEL BOOKING DATASET SUMMARY")
    print("=" * 60)
    print(f"Rows: {rows:,}")
    print(f"Columns: {columns}")
    print("\nColumn names:")

    for index, column in enumerate(dataframe.columns, start=1):
        print(f"{index:02}. {column}")

    print("\nFirst five rows:")
    print(dataframe.head())


def main() -> None:
    dataframe = load_booking_data()
    display_dataset_summary(dataframe)


if __name__ == "__main__":
    main()