# FAFCAB Management Services Deployment Issues

## Overview
This document outlines the deployment issues encountered with several services in the FAFCAB Management system, particularly on AMD64 architecture systems.

## Services with Deployment Issues

### 1. Fundraising Service (`pavel28/fundraising-service:latest`)
- **Issue**: `exec /usr/local/openjdk-17/bin/java: exec format error`
- **Image Architecture**: arm64
- **Host Architecture**: amd64 (x86_64)
- **Status**: Fails to start

### 2. Cab Booking Service (`vl4d09/cab-booking-service:latest`)
- **Issue**: `exec /usr/bin/dumb-init: exec format error`
- **Image Architecture**: arm64
- **Host Architecture**: amd64 (x86_64)
- **Status**: Fails to start

### 3. Checkin Service (`vl4d09/checkin-service:latest`)
- **Issue**: `exec /usr/local/bin/docker-entrypoint.sh: exec format error`
- **Image Architecture**: arm64
- **Host Architecture**: amd64 (x86_64)
- **Status**: Fails to start

## Attempts Made
1. Specified `platform: linux/arm64` in docker-compose.yml
2. Specified `platform: linux/amd64` in docker-compose.yml
3. Removed platform specification entirely
4. Used `DOCKER_DEFAULT_PLATFORM=linux/arm64` environment variable
5. Pulled the latest versions of all images
6. Attempted to run containers with explicit platform specification using `--platform`
7. Attempted to use Docker's emulation capabilities

## Analysis
All three problematic services show "exec format error" which indicates an architecture mismatch:
- The container images are built for ARM64 architecture
- The host system is running on AMD64 (x86_64) architecture
- Docker's emulation capabilities are not working properly for these images

## Root Cause
The root cause of the issue is that the Docker images for these three services were built specifically for ARM64 architecture and are not compatible with AMD64 systems. Even attempts to use Docker's emulation features have failed, suggesting potential issues with the images themselves or limitations in the emulation capabilities.

## Possible Solutions

### 1. Contact Image Maintainers
Reach out to the maintainers of these images to:
- Report the compatibility issues
- Request multi-architecture images that support both AMD64 and ARM64
- Ask for updated images with compatible binaries

### 2. Build Images Locally
If source code is available:
- Clone the repositories
- Build the images locally for the AMD64 architecture
- Push to a private registry or use local images

### 3. Use Alternative Images
Look for alternative images on Docker Hub that provide the same functionality but are built for AMD64 architecture.

### 4. Run on Compatible Hardware
Deploy these services on ARM64 hardware or cloud instances (such as AWS Graviton, Apple M1 Macs, or Raspberry Pi).

### 5. Cross-platform Building
If access to the source code is available, use Docker's buildx tool to create multi-architecture images:
```bash
docker buildx build --platform linux/amd64,linux/arm64 -t your-username/service-name:latest --push .
```

## Current Status
The following services are currently working:
- PostgreSQL Database
- Communication Service
- Consumables Service
- Budgeting Service
- Lost and Found Service
- User Management Service
- Notification Service

The following services are not working:
- Fundraising Service
- Cab Booking Service
- Checkin Service

## Recommendations
1. Prioritize contacting the image maintainers to resolve compatibility issues
2. Consider building these services from source if the repositories are accessible
3. For immediate development needs, use cloud-based ARM64 instances for these services
4. Investigate if source code is available to build AMD64-compatible images
5. Consider using development environments that match the target architecture (ARM64)
6. Update this document as solutions are implemented

## Additional Notes
- The issue was initially thought to be related to ARM64 deployment (as mentioned in the original document), but our investigation shows it's actually an AMD64 system trying to run ARM64 images
- Docker's emulation features did not resolve the issue, which may indicate problems with the images themselves
- The working services use images that are either multi-architecture or built for AMD64