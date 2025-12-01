# FAFCAB Data Warehouse ETL Pipeline

## Overview
This directory contains the ETL (Extract, Transform, Load) pipeline for the FAFCAB Management Platform. The pipeline extracts data from various microservices, transforms it into a consistent format, and loads it into a centralized data warehouse for analytics and reporting.

## Architecture
The ETL pipeline is designed to work with the microservices architecture of the FAFCAB platform:

- **Source Databases**: Multiple PostgreSQL databases used by different microservices
- **ETL Pipeline**: Python-based extraction, transformation, and loading processes
- **Data Warehouse**: Centralized PostgreSQL database for analytics
- **Monitoring API**: REST API for monitoring ETL pipeline status

## Directory Structure
```
data-warehouse/
├── .env                  # Environment variables
├── docker-compose.yml    # Docker configuration
├── Dockerfile            # ETL pipeline Dockerfile
├── Dockerfile.api        # API service Dockerfile
├── requirements.txt      # Python dependencies
├── dw-schema.sql         # Data warehouse schema
├── etl_pipeline.py       # Main ETL pipeline implementation
├── api.py                # Monitoring API
├── test_connections.py   # Database connection test script
├── DATABASE_CONNECTIONS.md # Database connection documentation
└── etl-logs/             # Log directory
```

## Services

### Data Warehouse Database
- **Purpose**: Stores consolidated data for analytics
- **Port**: 5433 (externally mapped from 5432 internally)
- **Database**: `fafcab_dw`
- **User**: `dw_user`

### ETL Pipeline Service
- **Purpose**: Runs the ETL process on a schedule
- **Language**: Python 3.10
- **Scheduling**: Configurable interval (default: every 60 minutes)

### ETL Monitoring API
- **Purpose**: Provides REST API for monitoring the ETL pipeline
- **Port**: 8001 (externally mapped from 8000 internally)
- **Endpoints**:
  - `GET /health` - Health check
  - `GET /stats` - ETL run statistics
  - `POST /trigger` - Manually trigger ETL process
  - `GET /quality-reports` - Latest data quality report
  - `GET /quality-reports/all` - All recent quality reports

## Setup

### Prerequisites
- Docker and Docker Compose
- Python 3.10+ (for local development)

### Environment Variables
The following environment variables need to be configured in the `.env` file:

```bash
# Data Warehouse Database Configuration
DW_POSTGRES_USER=dw_user
DW_POSTGRES_PASSWORD=dw_password
DW_POSTGRES_DB=fafcab_dw
DW_POSTGRES_HOST=localhost
DW_POSTGRES_PORT=5433

# Source Database Configurations
SOURCE_MAIN_DB_HOST=postgres
SOURCE_MAIN_DB_PORT=5432
POSTGRES_DB=fafcab
POSTGRES_USER=user
POSTGRES_PASSWORD=password

# Check-in Service database
SOURCE_CHECKIN_DB_HOST=checkin-db
SOURCE_CHECKIN_DB_PORT=5432
SOURCE_CHECKIN_DB_NAME=checkin_service
SOURCE_CHECKIN_DB_USER=checkin_user
SOURCE_CHECKIN_DB_PASSWORD=checkin_pass

# Additional service databases
POSTGRES_DB_1=fafcab_db1
POSTGRES_DB_2=fafcab_db2

# ETL Configuration
SCHEDULER_INTERVAL_MINUTES=60
```

### Running with Docker Compose
1. Navigate to the `data-warehouse` directory
2. Configure the environment variables in `.env`
3. Run `docker-compose up -d` to start all services
4. The ETL pipeline will automatically run based on the configured schedule

### Running Locally (Development)
1. Install Python dependencies: `pip install -r requirements.txt`
2. Configure environment variables in `.env`
3. Run the ETL pipeline: `python etl_pipeline.py`
4. Run the monitoring API: `python api.py`

## Testing Database Connections
To verify that all database connections are working correctly:

```bash
python test_connections.py
```

## Monitoring
The ETL pipeline provides several ways to monitor its operation:

1. **Log Files**: Check `/app/logs/etl_pipeline.log` in the container
2. **REST API**: Use the monitoring API endpoints
3. **Data Quality Reports**: Generated after each ETL run and stored in `/app/logs/`

## Extending the ETL Pipeline
To add support for additional services:

1. Add the database configuration to the `source_configs` dictionary in `ETLPipeline.__init__()`
2. Create a new extraction method for the service data
3. Create transformation methods as needed
4. Create loading methods to insert data into the data warehouse
5. Update the main ETL process to call the new methods

## Troubleshooting

### Connection Issues
- Verify that all Docker services are running: `docker-compose ps`
- Check that the environment variables are correctly set
- Ensure that the database credentials are correct
- Verify network connectivity between services

### Data Extraction Issues
- Check the service-specific database schemas
- Verify that the SQL queries in the extraction methods match the actual table structures
- Ensure that the required tables and columns exist in the source databases

### Performance Issues
- Monitor the log files for slow queries
- Consider adding indexes to source databases if needed
- Adjust the ETL schedule frequency based on system load