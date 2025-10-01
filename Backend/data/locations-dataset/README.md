# World Cities Data Loader

The data in this dataset comes from kaggle: https://www.kaggle.com/datasets/juanmah/world-cities?resource=download

This script loads world cities data from a CSV file into the PostgreSQL `locations` table.

## Prerequisites

1. **CSV File**: Ensure the `worldcities.csv` file is located at `data/locations-dataset/worldcities.csv`
2. **Database**: PostgreSQL database must be running and accessible with the `locations` table already created
3. **Environment Variables**: Set the following database connection variables in your `.env` file:

```bash
DB_HOST=localhost
DB_PORT=5432
DB_DATABASE=your_database_name
DB_USERNAME=your_username
DB_PASSWORD=your_password
```

## Usage

Run the script from the project root:

```bash
python load_data.py
```

## What the Script Does

1. **Validates Environment**: Checks that all required database environment variables are set
2. **Verifies Table**: Checks that the `locations` table already exists in the database
3. **Loads Data**: Reads the CSV and inserts data using upsert operations
4. **Handles Errors**: Gracefully handles parsing errors and continues processing
5. **Sets Timezone**: Automatically sets timezone to "Asia/Kolkata" for Indian cities (iso3 = IND)

## Idempotent Behavior

The script is designed to be safe to run multiple times:
- Verifies table existence before proceeding
- Uses PostgreSQL's `ON CONFLICT` clause for upsert operations
- Assumes unique constraint on `source_id` already exists to prevent duplicates

## CSV Structure Expected

The script expects the following columns in your CSV:
- `city`: City name (will use `city_ascii` field for better compatibility)
- `lat`: Latitude (decimal)
- `lng`: Longitude (decimal)
- `country`: Country name
- `iso3`: ISO 3-letter country code
- `admin_name`: Administrative region/province
- `population`: Population count
- `id`: Unique identifier (used as source_id)

**Note**: The script validates that all CSV columns are present to ensure the correct file is being processed.

## Output

The script provides detailed logging of:
- Connection status
- Table/index creation
- Data processing progress (every 1000 rows)
- Final summary of processed, skipped, and error counts

## Troubleshooting

- **Missing CSV**: Ensure the file exists at the specified path
- **Database Connection**: Check your environment variables and database status
- **Missing Table**: Ensure the `locations` table exists in your database
- **Permission Issues**: Ensure your database user has INSERT permissions
- **Large Files**: The script processes data in batches and commits every 1000 rows for memory efficiency

## Performance

- Processes data in batches of 1000 rows
- Creates appropriate database indexes for common queries
- Uses parameterized queries to prevent SQL injection
- Commits in batches to balance performance and transaction safety
