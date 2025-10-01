#!/usr/bin/env python3
"""
World Cities Data Loader

This script loads world cities data from CSV into the PostgreSQL cities table
using optimized bulk inserts. It processes data in batches of 50 rows per INSERT 
statement and commits every 10 statements (500 rows) for optimal performance.

Designed for loading into an empty table - uses bulk INSERT without conflict handling.

Usage:
    python load_data.py

Requirements:
    - CSV file at C:/Users/vivek/Downloads/worldcities.csv
    - Database connection configured for 'looooona' database
    - psycopg2-binary (already in requirements.txt)
    - Empty cities table (no existing data)
"""

import csv
import logging
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

import psycopg2
import psycopg2.extras
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Database configuration from environment variables
DB_CONFIG = {
    "host": "localhost",
    "port": 5432,
    "database": "looooona",
    "user": "postgres",
    "password": "tiger",
}

# CSV file path
CSV_FILE_PATH = Path(r"C:\Users\vivek\Downloads\worldcities.csv")


# Bulk INSERT SQL for cities table (no conflict handling needed)
BULK_INSERT_SQL = """
INSERT INTO cities (city, city_ascii, lat, lng, country, iso2, iso3, admin_name, capital, population, id)
VALUES %s
"""

# Configuration for bulk processing
ROWS_PER_STATEMENT = 50  # Number of rows per INSERT statement
STATEMENTS_PER_BATCH = 10  # Number of INSERT statements per commit batch

# Check table existence SQL
CHECK_TABLE_SQL = """
SELECT EXISTS (
    SELECT FROM information_schema.tables 
    WHERE table_schema = 'public' 
    AND table_name = 'cities'
);
"""


def validate_environment() -> bool:
    """Validate that all required database configuration is set."""
    missing_vars = []
    for key, value in DB_CONFIG.items():
        if value is None or (isinstance(value, str) and not value.strip()):
            missing_vars.append(f"DB_{key.upper()}")

    if missing_vars:
        logger.error(
            f"Missing required database configuration: {', '.join(missing_vars)}"
        )
        logger.error("Please update DB_CONFIG in the script with correct values")
        return False

    return True


def get_database_connection():
    """Create and return a database connection."""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        conn.autocommit = False
        return conn
    except psycopg2.Error as e:
        logger.error(f"Failed to connect to database: {e}")
        raise


def check_table_exists(conn) -> bool:
    """Check if the cities table exists."""
    with conn.cursor() as cursor:
        cursor.execute(CHECK_TABLE_SQL)
        exists = cursor.fetchone()[0]
        return exists


def parse_csv_row(row: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Parse a CSV row and convert it to the cities table format."""
    try:
        # Handle population - convert to float or None if invalid
        population_str = row.get("population", "").strip()
        population = None
        if population_str and population_str.replace(",", "").replace(".", "").isdigit():
            population = float(population_str.replace(",", ""))

        # Handle coordinates - ensure they're valid decimals
        lat = float(row.get("lat", 0))
        lng = float(row.get("lng", 0))

        # Validate coordinate ranges
        if not (-90 <= lat <= 90):
            logger.warning(
                f"Invalid latitude {lat} for city {row.get('city', 'Unknown')}, skipping"
            )
            return None
        if not (-180 <= lng <= 180):
            logger.warning(
                f"Invalid longitude {lng} for city {row.get('city', 'Unknown')}, skipping"
            )
            return None

        return {
            "city": row.get("city", "").strip(),
            "city_ascii": row.get("city_ascii", "").strip(),
            "lat": lat,
            "lng": lng,
            "country": row.get("country", "").strip(),
            "iso2": row.get("iso2", "").strip()[:2],
            "iso3": row.get("iso3", "").strip()[:3],
            "admin_name": row.get("admin_name", "").strip(),
            "capital": row.get("capital", "").strip(),
            "population": population,
            "id": int(row.get("id", 0)),
        }
    except (ValueError, KeyError) as e:
        logger.warning(f"Error parsing row {row.get('city', 'Unknown')}: {e}")
        return None


def bulk_insert_rows(cursor, rows_batch: List[tuple]) -> None:
    """Execute a bulk insert for a batch of rows."""
    if not rows_batch:
        return
    
    # Use psycopg2.extras.execute_values for efficient bulk insert
    psycopg2.extras.execute_values(
        cursor,
        BULK_INSERT_SQL,
        rows_batch,
        template=None,
        page_size=len(rows_batch)
    )


def load_csv_data(conn, csv_path: Path) -> int:
    """Load data from CSV into the database using bulk inserts."""
    if not csv_path.exists():
        raise FileNotFoundError(f"CSV file not found: {csv_path}")

    loaded_count = 0
    skipped_count = 0
    error_count = 0
    
    # Buffers for bulk processing
    current_statement_batch = []  # Rows for current INSERT statement
    statement_batches = []  # List of statement batches for commit batch

    with open(csv_path, "r", encoding="utf-8") as csvfile:
        # Use DictReader to get column names from header
        reader = csv.DictReader(csvfile)

        # Validate CSV structure
        expected_columns = {
            "city",
            "city_ascii",
            "lat",
            "lng",
            "country",
            "iso2",
            "iso3",
            "admin_name",
            "capital",
            "population",
            "id",
        }
        fieldnames = reader.fieldnames or []
        if not expected_columns.issubset(set(fieldnames)):
            missing = expected_columns - set(fieldnames)
            raise ValueError(f"CSV missing required columns: {missing}")

        logger.info(f"CSV columns found: {fieldnames}")
        logger.info(f"Using bulk insert: {ROWS_PER_STATEMENT} rows per statement, {STATEMENTS_PER_BATCH} statements per batch commit")

        with conn.cursor() as cursor:
            for row_num, row in enumerate(reader, start=2):  # Start at 2 since row 1 is header
                try:
                    parsed_data = parse_csv_row(row)
                    if parsed_data is None:
                        skipped_count += 1
                        continue

                    # Convert parsed data to tuple for bulk insert
                    # Order matches: city, city_ascii, lat, lng, country, iso2, iso3, admin_name, capital, population, id
                    row_tuple = (
                        parsed_data["city"],
                        parsed_data["city_ascii"],
                        parsed_data["lat"],
                        parsed_data["lng"],
                        parsed_data["country"],
                        parsed_data["iso2"],
                        parsed_data["iso3"],
                        parsed_data["admin_name"],
                        parsed_data["capital"],
                        parsed_data["population"],
                        parsed_data["id"]
                    )
                    
                    current_statement_batch.append(row_tuple)
                    loaded_count += 1

                    # When we have enough rows for one INSERT statement
                    if len(current_statement_batch) >= ROWS_PER_STATEMENT:
                        statement_batches.append(current_statement_batch)
                        current_statement_batch = []
                        
                        # When we have enough statements for one commit batch
                        if len(statement_batches) >= STATEMENTS_PER_BATCH:
                            # Execute all statements in this batch
                            for batch in statement_batches:
                                bulk_insert_rows(cursor, batch)
                            
                            # Commit the batch
                            conn.commit()
                            
                            rows_in_batch = sum(len(batch) for batch in statement_batches)
                            logger.info(f"Committed batch: {rows_in_batch} rows (Total processed: {loaded_count})")
                            
                            # Reset for next batch
                            statement_batches = []

                except Exception as e:
                    error_count += 1
                    logger.error(f"Error processing row {row_num}: {e}")
                    if error_count > 100:  # Stop if too many errors
                        logger.error("Too many errors, stopping processing")
                        break

            # Handle remaining rows
            if current_statement_batch:
                statement_batches.append(current_statement_batch)
            
            if statement_batches:
                # Execute remaining statements
                for batch in statement_batches:
                    bulk_insert_rows(cursor, batch)
                
                # Final commit
                conn.commit()
                
                remaining_rows = sum(len(batch) for batch in statement_batches)
                logger.info(f"Committed final batch: {remaining_rows} rows")

    logger.info("Data loading completed:")
    logger.info(f"  - Successfully processed: {loaded_count} rows")
    logger.info(f"  - Skipped: {skipped_count} rows")
    logger.info(f"  - Errors: {error_count} rows")

    return loaded_count


def main():
    """Main function to orchestrate the data loading process."""
    logger.info("Starting world cities data loading process...")

    # Validate environment
    if not validate_environment():
        sys.exit(1)

    # Check if CSV file exists
    if not CSV_FILE_PATH.exists():
        logger.error(f"CSV file not found: {CSV_FILE_PATH}")
        logger.error("Please ensure the file exists at the specified path")
        sys.exit(1)

    conn = None
    try:
        # Connect to database
        logger.info("Connecting to database...")
        conn = get_database_connection()
        logger.info("Database connection established")

        # Check if table exists
        if not check_table_exists(conn):
            logger.error("Table 'cities' does not exist in the database")
            logger.error("Please create the table first using the provided SQL schema")
            sys.exit(1)
        logger.info("Table 'cities' exists and is ready for data loading")

        # Note: Using bulk INSERT for empty table (no conflict handling needed)
        logger.info("Proceeding with bulk data loading into empty table")

        # Load data
        logger.info(f"Loading data from {CSV_FILE_PATH}...")
        loaded_count = load_csv_data(conn, CSV_FILE_PATH)

        logger.info(f"Successfully loaded {loaded_count} cities into the database")
        logger.info("Data loading process completed successfully!")

    except Exception as e:
        logger.error(f"An error occurred: {e}")
        if conn:
            conn.rollback()
        sys.exit(1)

    finally:
        if conn:
            conn.close()
            logger.info("Database connection closed")


if __name__ == "__main__":
    main()
