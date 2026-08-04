from pathlib import Path
from typing import Final


PROJECT_ROOT: Final[Path] = Path(__file__).resolve().parents[1]

DATABASE_PATH: Final[Path] = (
    PROJECT_ROOT
    / "database"
    / "hotel_bookings.db"
)

DATABASE_URL: Final[str] = (
    f"sqlite:///{DATABASE_PATH.as_posix()}"
)