from fastapi import FastAPI

from api.routes import router


app = FastAPI(
    title="Hotel Booking Analytics API",
    description=(
        "REST API for accessing cleaned hotel-booking data "
        "and analytical insights."
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.include_router(router)