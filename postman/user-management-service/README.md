# Postman Testing Collection

This folder contains Postman collections and environments for testing the User Management Service API.

## Files

- `User-Management-Service.postman_collection.json` - Main API collection with all endpoints
- `User-Management-Local.postman_environment.json` - Local development environment variables
- `README.md` - This documentation file

## Setup Instructions

### 1. Import Collection and Environment

1. Open Postman
2. Click **Import** button (or File → Import)
3. Select **Upload Files** or drag and drop both JSON files:
   - `User-Management-Service.postman_collection.json`
   - `User-Management-Local.postman_environment.json`
4. Click **Import**

### 2. Select Environment

1. In the top-right corner of Postman, select **User Management - Local** from the environment dropdown
2. Verify that variables are loaded by clicking the eye icon next to the environment selector

## Testing Workflow

### Step 1: Start the Service
```bash
# Using Docker Compose
docker-compose up

# OR using Maven
./mvnw spring-boot:run
```

### Step 2: Test Authentication
1. Open **Authentication → Login User**
2. Ensure `test_username` is set to an existing user (default: `john_doe`)
3. Send the request
4. Verify that `jwt_token` and `user_id` are automatically saved to environment variables

### Step 3: Test User Management
After successful login, test these endpoints:
- **Get All Users** - List all users with pagination
- **Get User by ID** - Get details of the logged-in user
- **Create User** - Add a new user to the system
- **Delete User** - Remove a user (update `delete_user_id` first)
- **Get Users by Role** - Filter users by specific roles (Administrator, Moderator, Member)

### Step 4: Test Role Management
Test role-related endpoints:
- **Get All Roles** - Retrieve all available roles
- **Get Role by ID** - Get specific role details by ID
- **Get Role by Name** - Search for roles by name (Administrator, Moderator, Member)

### Step 5: Test Discord Integration
Test Discord API endpoints:
- **Get Guild Members** - Fetch members from Discord guild
- **Get Guild Member by ID** - Get specific Discord member
- **Get Guild Roles** - Retrieve Discord guild roles

### Step 6: Health Checks
- **Service Health Check** - Verify service is running
- **Get OpenAPI Documentation** - Access API specs
- **Access Swagger UI** - Interactive API documentation

## Environment Variables

| Variable | Default Value | Description |
|----------|---------------|-------------|
| `base_url` | `http://localhost:8080` | Service base URL |
| `test_username` | `john_doe` | Username for login testing |
| `jwt_token` | `""` | JWT token (auto-populated after login) |
| `user_id` | `""` | User ID (auto-populated after login) |
| `delete_user_id` | `replace-with-actual-user-id` | User ID for deletion tests |
| `page_limit` | `1000` | Default page size for paginated requests |
| `discord_user_id` | `80351110224678912` | Discord user ID for testing |
| `discord_guild_id` | `1419580348660187198` | Discord guild ID |
| `role_id` | `admin_role_id` | Role ID for testing role endpoints |
| `role_name` | `Administrator` | Role name for testing role endpoints |

## API Endpoint Categories

### 1. Authentication
- **POST** `/api/auth/login` - User authentication with username

### 2. User Management
- **GET** `/api/users` - Get all users (paginated)
- **GET** `/api/users/{userId}` - Get user by Discord ID
- **POST** `/api/users` - Create new user
- **DELETE** `/api/users/{userId}` - Delete user
- **GET** `/api/users/role/{roleName}` - Get users by role name

### 3. Role Management
- **GET** `/api/roles` - Get all roles
- **GET** `/api/roles/{roleId}` - Get role by ID
- **GET** `/api/roles/name/{roleName}` - Get role by name

### 4. Discord Integration
- **GET** `/api/discord/members` - Get Discord guild members
- **GET** `/api/discord/member/{userId}` - Get Discord member by ID
- **GET** `/api/discord/roles` - Get Discord guild roles

### 5. Health & Documentation
- **GET** `/actuator/health` - Service health check
- **GET** `/api-docs` - OpenAPI documentation
- **GET** `/swagger-ui.html` - Swagger UI

## Test Data

The service includes pre-populated test data:

### Users
- **admin_user** (ID: `123456789012345678`) - Administrator role
- **mod_user** (ID: `234567890123456789`) - Moderator role  
- **john_doe** (ID: `345678901234567890`) - Member role
- **jane_smith** (ID: `456789012345678901`) - Member role
- **helper_bot** (ID: `567890123456789012`) - Bot user

### Roles
- **Administrator** (ID: `admin_role_id`) - Full permissions
- **Moderator** (ID: `mod_role_id`) - Moderation permissions
- **Member** (ID: `member_role_id`) - Basic permissions

## Troubleshooting

### Authentication Issues

**404 User Not Found (Login)**
- Verify test user exists in database (check DataLoader)
- Update `test_username` to match actual usernames: `admin_user`, `mod_user`, `john_doe`, `jane_smith`
- Ensure database is populated with test data on startup

**401 Unauthorized (Protected Endpoints)**
- Run Login request first to get JWT token
- Check if JWT token is saved in environment variables
- Verify token hasn't expired (check JWT expiration settings)

### Connection Issues

**Connection Refused**
- Ensure service is running on port 8080
- Check Docker containers: `docker-compose ps`
- Verify `base_url` environment variable matches actual service URL

**Database Connection Issues**
- Ensure PostgreSQL is running: `docker-compose up postgres`
- Check application logs for database connection errors
- Verify database schema is created properly

### Discord Integration Issues

**Discord API 401 Unauthorized**
- Verify `DISCORD_BOT_TOKEN` environment variable is set
- Check bot token validity in Discord Developer Portal
- Ensure bot has proper permissions in Discord guild

**Empty Discord Responses**
- Verify bot is added to the Discord guild
- Check bot permissions: "View Server Members"
- Enable "Server Members Intent" in Discord Developer Portal

### Role and User Testing

**Role Not Found**
- Check role names are exact matches: `Administrator`, `Moderator`, `Member`
- Verify roles were created during application startup
- Use "Get All Roles" endpoint to see available roles

**User-Role Relationships**
- Users are assigned roles during DataLoader execution
- Check logs for role assignment during startup
- Use "Get Users by Role" to verify role assignments

## Collection Features

### Automatic Token Management
- Login request automatically saves JWT token to `jwt_token` variable
- All protected endpoints use the saved token via Bearer authentication
- User ID is automatically set in `user_id` variable for subsequent requests

### Request Examples
Each endpoint includes:
- Proper authentication headers where required
- Example request bodies with realistic test data
- Expected response formats
- Comprehensive descriptions

### Test Scripts
The Login endpoint includes automated test scripts that:
- Verify successful authentication (200 status)
- Validate JWT token format and presence
- Check user ID format and presence
- Automatically save tokens for subsequent requests
- Handle authentication failures gracefully

### Environment Variable Usage
- Dynamic URLs using `{{base_url}}`
- Configurable test data via environment variables
- Automatic token management for seamless testing
- Support for both local and production environments

## Production Testing

For testing against production/staging environments:

1. **Create Production Environment**
   - Duplicate the Local environment
   - Update `base_url` to production URL
   - Use production-appropriate Discord IDs and tokens

2. **Security Considerations**
   - Use production-safe test credentials
   - **BE VERY CAREFUL** with DELETE operations in production
   - Consider using read-only operations for production testing
   - Verify proper authentication and authorization

3. **Environment Variables**
   - Update Discord-related variables for production guild
   - Use production database connection settings
   - Ensure JWT secrets match production configuration

4. **Testing Strategy**
   - Start with health checks and documentation endpoints
   - Test authentication with known production users
   - Verify role assignments and permissions
   - Test Discord integration if configured for production guild
