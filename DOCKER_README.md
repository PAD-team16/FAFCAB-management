# FAFCAB Management System - Docker Compose Setup

This Docker Compose setup includes the PostgreSQL database and the Communication Service for the FAFCAB management system.

## Prerequisites

- Docker
- Docker Compose

## Setup Instructions

1. Clone this repository (if you haven't already):
   ```bash
   git clone <repository-url>
   cd FAFCAB-management
   ```

2. Update the `.env` file with your preferred credentials and secrets:
   ```bash
   cp .env.example .env
   # Edit .env file with your preferred text editor
   ```

3. Start the services:
   ```bash
   docker-compose up -d
   ```

4. Check the status of the services:
   ```bash
   docker-compose ps
   ```

5. View logs:
   ```bash
   docker-compose logs -f
   ```

## Services

- **PostgreSQL Database**: Running on port 5433
- **Communication Service**: Running on port 8089

## Stopping Services

To stop the services:
```bash
docker-compose down
```

To stop the services and remove the volumes:
```bash
docker-compose down -v
```

## Security Notes

- The `.env` file contains sensitive information and should never be committed to version control
- In production, use stronger passwords and secrets
- The JWT secret should be a long, random string in production