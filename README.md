## Data Validation

The validation pipeline performs:

- Schema validation
- Missing-value profiling
- Duplicate detection
- Categorical-value validation
- Numerical business-rule validation
- Date validation
- JSON validation-report generation

Run the validation pipeline:

```bash
python -m ingestion.validate_data

## SQL Repository Layer

The repository layer provides reusable, parameterized SQL queries for:

- Paginated booking retrieval
- Booking lookup by ID
- Country filtering
- Cancellation analysis
- Average Daily Rate analysis
- Country-level aggregation
- Monthly booking trends
- Stay-duration analysis
- Estimated booking-value summaries

Run the manual query demonstration:

```bash
python -m database.test_queries

## Analytics API Endpoints

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/api/v1/analytics/top-countries` | Top countries by booking count |
| GET | `/api/v1/analytics/revenue` | Estimated booking-value summary |
| GET | `/api/v1/analytics/monthly-bookings` | Monthly booking and cancellation trends |
| GET | `/api/v1/analytics/cancellation-rate` | Overall or hotel-specific cancellation rate |
| GET | `/api/v1/analytics/hotel-performance` | Compare hotel-level performance |

> Revenue figures are estimated booking values calculated from ADR and stayed nights. They are not verified accounting revenue.