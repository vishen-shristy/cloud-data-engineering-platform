from pathlib import Path

import pandas as pd
import pytest

from transformation.clean_data import (
    clean_booking_data,
    clean_missing_values,
    remove_duplicates,
    remove_invalid_guest_records,
    save_cleaned_data,
    standardize_data_types,
)


def test_clean_missing_values() -> None:
    dataframe = pd.DataFrame(
        {
            "children": [1, None],
            "country": ["IND", None],
            "agent": [10, None],
            "company": [20, None],
        }
    )

    result = clean_missing_values(dataframe)

    assert result["children"].tolist() == [1, 0]
    assert result["country"].tolist() == [
        "IND",
        "Unknown",
    ]
    assert result["agent"].tolist() == [10, 0]
    assert result["company"].tolist() == [20, 0]

    assert dataframe["children"].isna().sum() == 1
    assert dataframe["country"].isna().sum() == 1


def test_remove_duplicates() -> None:
    dataframe = pd.DataFrame(
        {
            "hotel": [
                "City Hotel",
                "City Hotel",
                "Resort Hotel",
            ],
            "lead_time": [
                10,
                10,
                20,
            ],
        }
    )

    result = remove_duplicates(dataframe)

    assert len(result) == 2
    assert result.duplicated().sum() == 0
    assert result.index.tolist() == [0, 1]


def test_remove_invalid_guest_records() -> None:
    dataframe = pd.DataFrame(
        {
            "adults": [2, 0, 0],
            "children": [0, 0, 1],
            "babies": [0, 0, 0],
        }
    )

    result = remove_invalid_guest_records(
        dataframe
    )

    assert len(result) == 2

    invalid_mask = (
        (result["adults"] == 0)
        & (result["children"] == 0)
        & (result["babies"] == 0)
    )

    assert not invalid_mask.any()


def test_standardize_data_types() -> None:
    dataframe = pd.DataFrame(
        {
            "children": [1.0, 0.0],
            "agent": [10.0, 0.0],
            "company": [20.0, 0.0],
            "reservation_status_date": [
                "2017-07-01",
                "2017-07-02",
            ],
            "arrival_date_year": [
                2017,
                2017,
            ],
            "arrival_date_month": [
                "July",
                "July",
            ],
            "arrival_date_day_of_month": [
                1,
                2,
            ],
        }
    )

    result = standardize_data_types(dataframe)

    assert str(result["children"].dtype) == "int64"
    assert str(result["agent"].dtype) == "int64"
    assert str(result["company"].dtype) == "int64"

    assert pd.api.types.is_datetime64_any_dtype(
        result["reservation_status_date"]
    )

    assert pd.api.types.is_datetime64_any_dtype(
        result["arrival_date"]
    )

    assert result["arrival_date"].dt.strftime(
        "%Y-%m-%d"
    ).tolist() == [
        "2017-07-01",
        "2017-07-02",
    ]


def test_standardize_data_types_rejects_invalid_date() -> None:
    dataframe = pd.DataFrame(
        {
            "children": [0],
            "agent": [0],
            "company": [0],
            "reservation_status_date": [
                "not-a-date",
            ],
        }
    )

    with pytest.raises(
        ValueError,
        match="invalid values",
    ):
        standardize_data_types(dataframe)


def test_clean_booking_data() -> None:
    dataframe = pd.DataFrame(
        {
            "hotel": [
                "City Hotel",
                "City Hotel",
                "Resort Hotel",
            ],
            "children": [
                None,
                None,
                1,
            ],
            "country": [
                None,
                None,
                "IND",
            ],
            "agent": [
                None,
                None,
                10,
            ],
            "company": [
                None,
                None,
                20,
            ],
            "adults": [
                2,
                2,
                0,
            ],
            "babies": [
                0,
                0,
                0,
            ],
            "reservation_status_date": [
                "2017-07-01",
                "2017-07-01",
                "2017-07-02",
            ],
            "arrival_date_year": [
                2017,
                2017,
                2017,
            ],
            "arrival_date_month": [
                "July",
                "July",
                "July",
            ],
            "arrival_date_day_of_month": [
                1,
                1,
                2,
            ],
        }
    )

    result = clean_booking_data(dataframe)

    # First two rows become exact duplicates after null cleaning,
    # so one is removed.
    assert len(result) == 2

    assert result["children"].isna().sum() == 0
    assert result["country"].isna().sum() == 0
    assert result["agent"].isna().sum() == 0
    assert result["company"].isna().sum() == 0
    assert "arrival_date" in result.columns


def test_save_cleaned_data(
    tmp_path: Path,
) -> None:
    dataframe = pd.DataFrame(
        {
            "hotel": [
                "City Hotel",
                "Resort Hotel",
            ]
        }
    )

    output_path = (
        tmp_path
        / "processed"
        / "cleaned.csv"
    )

    saved_path = save_cleaned_data(
        dataframe=dataframe,
        output_path=output_path,
    )

    assert saved_path == output_path
    assert output_path.exists()

    saved_dataframe = pd.read_csv(
        output_path
    )

    pd.testing.assert_frame_equal(
        saved_dataframe,
        dataframe,
    )