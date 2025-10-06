# Postman Testing Collection

This folder contains Postman collections and environments for testing the Notification Service API.

## Files

- `Notification-Service.postman_collection.json` - Main API collection with all endpoints
- `Notification-Service-Local.postman_environment.json` - Local development environment variables
- `README.md` - This documentation file

## Setup Instructions

### 1. Import Collection and Environment

1. Open Postman
2. Click **Import** button (or File → Import)
3. Select **Upload Files** or drag and drop both JSON files:
   - `Notification-Service.postman_collection.json`
   - `Notification-Service-Local.postman_environment.json`
4. Click **Import**

**Note:** If the JSON files appear empty or corrupted, copy the content from the actual files in this directory.

### 2. Select Environment

1. In the top-right corner of Postman, select **Notification Service - Local** from the environment dropdown
2. Verify that variables are loaded by clicking the eye icon next to the environment selector

## Testing Workflow

### Step 1: Start the Service
```bash
# Using Docker Compose (Recommended)
docker-compose up --build

# OR using Maven
./mvnw spring-boot:run
```

### Step 2: Test Email Notifications
1. Open **Email Notifications → Send Email**
2. Update the recipient email in the request body
3. Send the request
4. Check MailHog at `http://localhost:8025` to see the sent email

### Step 3: Test Discord Notifications
Test these endpoints in order:
- **Send Message to General Channel** - Basic message sending
- **Send Message to Specific Channel** - Targeted channel messaging
- **Mention User** - User mention functionality
- **Mention Role** - Role mention functionality
- **Mention Everyone** - Broadcast notifications
- **Mention Here** - Online user notifications
- **Mention Multiple Users** - Bulk user mentions
- **Mention Role by Name** - Role mention by name

### Step 4: Health Checks
- **Service Health Check** - Verify service is running
- **Get OpenAPI Documentation** - Access API specs
- **Access Swagger UI** - Interactive API documentation

## Environment Variables

| Variable | Default Value | Description |
|----------|---------------|-------------|
| `base_url` | `http://localhost:8090` | Service base URL |
| `test_email` | `test@example.com` | Test recipient email |
| `test_message` | `Hello from Notification Service!` | Default test message |
| `discord_channel_id` | `123456789012345678` | Discord channel ID for testing |
| `discord_user_id` | `987654321098765432` | Discord user ID for mentions |
| `discord_role_id` | `111222333444555666` | Discord role ID for mentions |
| `discord_role_name` | `admin` | Discord role name for testing |

## Testing with MailHog

For email testing, the service includes MailHog:

1. **Start services:** `docker-compose up`
2. **Send test emails** via Postman
3. **Check results** at `http://localhost:8025`
4. **No real emails** are sent when using MailHog

### MailHog Configuration
To test with MailHog instead of Gmail:
- Update your `.env` file:
  ```env
  SPRING_MAIL_HOST=mailhog
  SPRING_MAIL_PORT=1025
  EMAIL_USERNAME=test@example.com
  EMAIL_PASSWORD=any_password
  ```

## Discord Bot Setup

For Discord testing, you'll need:

1. **Discord Bot Token** - Create a bot in Discord Developer Portal
2. **Channel IDs** - Get channel IDs from Discord (Developer Mode required)
3. **User/Role IDs** - Get user and role IDs for mention testing

### Getting Discord IDs
1. Enable Developer Mode in Discord (User Settings → Advanced → Developer Mode)
2. Right-click on channels/users/roles to copy their IDs
3. Update environment variables with actual IDs

## Troubleshooting

### Empty or Corrupted JSON Files
If the JSON files appear empty:
1. Check file encoding (should be UTF-8)
2. Verify file permissions
3. Re-download or copy the content from the source
4. Try importing by copying JSON content directly into Postman

### Common API Issues

**500 Internal Server Error (Email)**
- Check email configuration in `.env` file
- Verify Gmail App Password is correct
- Ensure 2FA is enabled on Gmail account
- Check if MailHog is running for testing

**500 Internal Server Error (Discord)**
- Verify Discord bot token is valid
- Check if bot has proper permissions in the server
- Ensure channel IDs exist and bot has access
- Verify user/role IDs are correct

**Connection Refused**
- Ensure service is running on port 8090
- Check Docker containers: `docker-compose ps`
- Verify `base_url` environment variable

**Email Not Received (Gmail)**
- Check spam folder
- Verify recipient email address
- Use MailHog for testing instead
- Check application logs for errors

**Discord Message Not Sent**
- Verify bot is in the Discord server
- Check bot permissions (Send Messages, Mention Everyone, etc.)
- Ensure channel exists and bot has access
- Check Discord bot token validity

## Collection Features

### Email Testing
- Simple email sending with customizable recipient and message
- Error handling examples
- Integration with MailHog for safe testing

### Discord Testing
- Complete Discord bot functionality coverage
- Various mention types (user, role, everyone, here)
- Multiple user mentions
- Role mentions by name and ID
- Channel-specific messaging

### Request Examples
Each endpoint includes:
- Proper Content-Type headers
- Example request bodies with realistic data
- Expected response formats
- Error response examples

### Environment Variables
All requests use environment variables for:
- Easy switching between test and production
- Consistent test data across requests
- Quick updates of channel/user IDs

## Production Testing

For testing against production/staging environments:

1. Create a new environment in Postman
2. Update `base_url` to production URL
3. Use production Discord bot token and channel IDs
4. Configure production SMTP settings
5. **BE CAREFUL** with broadcast mentions (@everyone) in production
6. Test with small groups first before production deployment

## Security Considerations

- **Never commit** Discord bot tokens or email credentials
- Use environment-specific configurations
- Test with dedicated test Discord server
- Limit bot permissions to minimum required
- Monitor notification volumes in production
- Implement rate limiting for production use

