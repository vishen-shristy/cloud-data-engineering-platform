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