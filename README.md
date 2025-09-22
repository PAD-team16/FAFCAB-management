# FAF Cab Management Platform - Communication Contract

This document outlines the communication contracts for the microservices within the FAF Cab Management Platform. All services that require user authentication or user-specific information will validate requests using a **JWT (JSON Web Token)** provided in the `Authorization` header.

---

## Overview

The FAF Cab Management Platform is designed to improve the organization and operational efficiency of FAF Cab, with modular microservices for user management, communication, booking, consumable tracking, fundraising, and more. Each microservice encapsulates a specific domain to ensure modularity, independence, and maintainability.

Microservices are implemented using multiple technologies to optimize performance and leverage language-specific strengths:

- **Java/Spring Boot:** User Management, Notification, Budgeting, Fundraising, Sharing
- **Elixir:** Communication Service, Tea Management, Lost & Found, Budgeting
- **JavaScript/Node.js:** Cab Booking, Check-in

---

# Technologies & Communication Patterns

---

| Team           | Services                                      | Language & Framework | Database   | Communication Patterns                                         | Motivation & Trade-offs                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                          |
| -------------- | --------------------------------------------- | -------------------- | ---------- | -------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Vieru Mihai    | Lost & Found, Budgeting                       | Elixir               | PostgreSQL | REST, Asynchronous notifications, WebSocket (Phoenix Channels) | Elixir’s ability to handle high concurrency and fault tolerance is ideal for budget and lost & found services that require reliable multi-user interaction and asynchronous notifications.                                                                                                                                                                                                                                                                                                                                       |
| Polisciuc Vlad | Tea Management Service, Communication Service | Elixir               |            | REST, Async notifications                                      | Elixir excels at real-time, low-latency systems. Its lightweight processes and OTP supervision enhance fault tolerance, perfect for consumable tracking and live chat. Cowboy's native WebSocket support enables efficient bi-directional communication, crucial for the communication service's real-time messaging and moderation features.                                                                                                                                                                                    |
| Ungureanu Vlad | Cab Booking, Check-in                         | Node.js, Express     | PostgreSQL | REST, Async loops, External API integration (Google Calendar)  | Node.js is exceptionally well-suited for applications like booking systems due to its event-driven, non-blocking I/O model. When the system needs to perform an action that relies on an external service, such as fetching data from the Google Calendar API, it sends the request and immediately proceeds to handle other tasks without waiting for a response. This asynchronous capability means the application doesn't get stuck, allowing its lightweight runtime to efficiently manage many simultaneous user requests. |
| Tapu Pavel     | Fundraising, Sharing                          | Java, Spring Boot    | PostgreSQL | REST with JWT auth, Async notification queues                  | Java and Spring Boot provide a mature, secure, and scalable framework for handling critical business workflows like fundraising and item sharing. Strong security features (JWT auth) and stable async processing suit admin-controlled services requiring transactional integrity and complex business logic.                                                                                                                                                                                                                   |
| Copta Adrian   | User Management, Notification                 | Java, Spring Boot    | PostgreSQL | REST, Async event-driven updates                               | The Spring ecosystem offers robust authentication (including JWT), authorization, and notification capabilities critical for user and notification management. Because of high developer productivity and strong integration with databases and enterprise security standards, it makes ideal for core identity and communication services.                                                                                                                                                                                      |

# Architectural Diagram of Microservices operation

![microserv](https://github.com/user-attachments/assets/2c87e83c-0a08-4641-9613-bbea49de16f1)

The diagram above illustrates the microservices architecture designed for the FAFCab system. It highlights how different services, such as Notification Service, Communication Service, Budgeting Service, Fund Raising Service, Tea Management Service, and User Management Service, interact with each other through the API Gateway and Service Registry. Each service is responsible for a specific function, ranging from financial tracking and consumable management to user check-ins, booking, and lost-and-found operations. The modular design ensures that responsibilities are clearly separated, making the system scalable, maintainable, and easier to extend with new features as needed.

## **1. User Management Service**

A Spring Boot microservice for user authentication and management as part of the **FAFCAB Cabinet Management Platform**.

## Tech Stack

- **Java 21** with Spring Boot 3.x
- **PostgreSQL** for data persistence
- **JWT** for authentication tokens
- **Docker** for containerization
- **Swagger/OpenAPI** for API documentation

## Responsibilities

- User authentication and JWT token generation
- User profile management (CRUD operations)
- Role-based user filtering and queries
- Integration with other platform microservices

## API Endpoints

### Authentication

**User Login**
- `POST /api/auth/login`
  - **Description:** Authenticates a user with username and returns a JWT token.
  - **Payload:**
    ```json
    {
      "username": "john_doe"
    }
    ```
  - **Success Response (200 OK):**
    ```json
    {
      "jwt": "<jwt_token>",
      "userId": "123e4567-e89b-12d3-a456-426614174000",
      "roles": ["student", "FAF_NGO_Member"]
    }
    ```
  - **Error Response (404 Not Found):** User not found

### User Management

**Get All Users**
- `GET /api/users?limit=1000`
  - **Description:** Retrieves a paginated list of all users.
  - **Headers:** `Authorization: Bearer <jwt>`
  - **Query Parameters:**
    - `limit` (optional): Maximum number of users to return (default: 1000)

**Get User by ID**
- `GET /api/users/{userId}`
  - **Description:** Retrieves a specific user by their UUID.
  - **Headers:** `Authorization: Bearer <jwt>`
  - **Success Response (200 OK):**
    ```json
    {
      "id": "123e4567-e89b-12d3-a456-426614174000",
      "username": "john_doe",
      "email": "john.doe@example.com",
      "roles": ["student", "FAF_NGO_Member"]
    }
    ```

**Create User**
- `POST /api/users`
  - **Description:** Creates a new user in the system.
  - **Headers:** `Authorization: Bearer <jwt>`
  - **Payload:**
    ```json
    {
      "username": "new_user",
      "email": "new.user@example.com",
      "roles": ["student"]
    }
    ```

**Delete User**
- `DELETE /api/users/{userId}`
  - **Description:** Deletes a user from the system.
  - **Headers:** `Authorization: Bearer <jwt>`
  - **Success Response:** 204 No Content

**Get Users by Role**
- `GET /api/users/role/{role}?limit=1000`
  - **Description:** Retrieves all users with a specific role.
  - **Headers:** `Authorization: Bearer <jwt>`
  - **Path Parameters:**
    - `role`: Role name (e.g., "admin", "teacher", "student")
  - **Query Parameters:**
    - `limit` (optional): Maximum number of users to return (default: 1000)

## Development Setup

### Prerequisites
- Java 21
- Docker and Docker Compose
- Maven

### Local Development

1. **Clone the repository**
2. **Start the database:**
   ```bash
   docker-compose up postgres
   ```

3. **Run the application:**
   ```bash
   ./mvnw spring-boot:run
   ```

### Docker Deployment

**Build and run with Docker Compose:**
```bash
docker-compose up --build
```

The service will be available at `http://localhost:8080`

## API Documentation

- **Swagger UI:** `http://localhost:8080/swagger-ui.html`
- **OpenAPI Docs:** `http://localhost:8080/api-docs`

## Configuration

Key configuration properties (see `application.yml`):

- **Database:** PostgreSQL connection settings
- **JWT:** Secret key and token expiration
- **API:** Base path configuration (`/api`)
- **Server:** Port 8080

Environment variables for Docker:
- `JWT_SECRET`: JWT signing secret
- `JWT_EXPIRATION`: Token expiration time in milliseconds

## Database Schema

The service uses PostgreSQL with the following main entities:
- **users**: Main user table with UUID primary key
- **user_roles**: Role assignments for users

## Integration

This microservice integrates with other FAFCAB Cabinet Management Platform services through:
- JWT token validation for inter-service communication
- Shared user identification via UUID
- Role-based authorization for platform features

---

## **2. Notification Service**

A Spring Boot microservice for sending email and Discord notifications as part of the **FAFCAB Cabinet Management Platform**.

## Tech Stack

- **Java 21** with Spring Boot 3.x
- **Spring Mail** for email integration
- **JavaMail API** for SMTP email sending
- **Docker** for containerization
- **MailHog** for email testing
- **Swagger/OpenAPI** for API documentation

## Responsibilities

- Sending email notifications via SMTP
- Managing Discord bot interactions and message sending
- Handling message templating and formatting
- Providing a consistent API for various notification channels
- Error handling for failed notification attempts

## API Endpoints

### Email Notifications

**Send Email**
- `POST /api/email/send`
  - **Description:** Sends an email notification to a specified recipient.
  - **Payload:**
    ```json
    {
      "to": "recipient@example.com",
      "message": "Your notification message here"
    }
    ```
  - **Success Response (200 OK):** "Email sent successfully"
  - **Error Response (500 Internal Server Error):** "Failed to send email: [error message]"

### Discord Notifications

**Send Message to General Channel**
- `POST /api/discord/send`
  - **Description:** Sends a message to the configured general Discord channel.
  - **Payload:**
    ```json
    {
      "message": "Your notification message here"
    }
    ```
  - **Success Response (200 OK):** "Message sent successfully!"

**Send Message to Specific Channel**
- `POST /api/discord/send/{channelId}`
  - **Description:** Sends a message to a specific Discord channel.
  - **Path Parameters:**
    - `channelId`: Discord channel ID (e.g., "123456789012345678")
  - **Payload:**
    ```json
    {
      "message": "Your notification message here"
    }
    ```
  - **Success Response (200 OK):** "Message sent to channel successfully!"

**Mention a Discord Role**
- `POST /api/discord/send/mention-role`
  - **Description:** Sends a message with a role mention in a specific Discord channel.
  - **Payload:**
    ```json
    {
      "channelId": "123456789012345678",
      "roleId": "123456789012345678",
      "message": "Your notification message here"
    }
    ```
  - **Success Response (200 OK):** "Role mentioned!"

**Mention a Discord User**
- `POST /api/discord/send/mention-user`
  - **Description:** Sends a message with a user mention in a specific Discord channel.
  - **Payload:**
    ```json
    {
      "channelId": "123456789012345678",
      "userId": "123456789012345678",
      "message": "Your notification message here"
    }
    ```
  - **Success Response (200 OK):** "User mentioned!"

**Mention Everyone**
- `POST /api/discord/send/mention-everyone`
  - **Description:** Sends a message with @everyone mention in a specific Discord channel.
  - **Payload:**
    ```json
    {
      "channelId": "123456789012345678",
      "message": "Your notification message here"
    }
    ```
  - **Success Response (200 OK):** "Everyone mentioned!"

**Mention Here**
- `POST /api/discord/send/mention-here`
  - **Description:** Sends a message with @here mention in a specific Discord channel.
  - **Payload:**
    ```json
    {
      "channelId": "123456789012345678",
      "message": "Your notification message here"
    }
    ```
  - **Success Response (200 OK):** "Here mentioned!"

**Mention Multiple Users**
- `POST /api/discord/send/mention-multiple-users`
  - **Description:** Sends a message with multiple user mentions in a specific Discord channel.
  - **Payload:**
    ```json
    {
      "channelId": "123456789012345678",
      "userIds": ["123456789012345678", "987654321098765432"],
      "message": "Your notification message here"
    }
    ```
  - **Success Response (200 OK):** "Multiple users mentioned!"

**Mention Role by Name**
- `POST /api/discord/send/mention-role-by-name`
  - **Description:** Sends a message with a role mention using role name in a specific Discord channel.
  - **Payload:**
    ```json
    {
      "channelId": "123456789012345678",
      "roleName": "admin",
      "message": "Your notification message here"
    }
    ```
  - **Success Response (200 OK):** "Role mentioned by name!"

## Development Setup

### Prerequisites

- Java 21
- Maven 3.6+
- Docker & Docker Compose
- Gmail account with App Password (for production SMTP)

### Local Development

1. **Clone the repository**

2. **Set up environment variables:**
   
   Create a `.env` file in the project root:
   ```env
   EMAIL_USERNAME=your_email@gmail.com
   EMAIL_PASSWORD=your_app_password
   DISCORD_BOT_TOKEN=your_discord_bot_token
   DISCORD_GENERAL_CHANNEL_ID=your_discord_general_channel_id
   ```

3. **Run the application:**
   ```bash
   mvn spring-boot:run
   ```

### Docker Deployment

**Option 1: Using Docker Compose (Recommended for Team Development)**

```bash
docker-compose up --build
```

This will start:
- **Notification Service** on `http://localhost:8090`
- **MailHog** (Email testing tool) on `http://localhost:8025`

**Option 2: Manual Docker Build**

```bash
# Build the image
docker build -t notification-service .

# Run the container
docker run -p 8090:8090 \
  -e EMAIL_USERNAME=your_email@gmail.com \
  -e EMAIL_PASSWORD=your_app_password \
  -e DISCORD_BOT_TOKEN=your_discord_bot_token \
  -e DISCORD_GENERAL_CHANNEL_ID=your_discord_general_channel_id \
  notification-service
```

## API Documentation

- **Swagger UI:** `http://localhost:8090/swagger-ui.html`
- **OpenAPI Docs:** `http://localhost:8090/api-docs`

## Configuration

### Email Configuration

The application uses the following SMTP configuration:

- **Host**: smtp.gmail.com (configurable via `SPRING_MAIL_HOST`)
- **Port**: 587 (configurable via `SPRING_MAIL_PORT`)
- **Authentication**: Enabled
- **STARTTLS**: Enabled
- **Connection timeout**: 5000ms
- **Read/Write timeout**: 5000ms

### Discord Configuration

- **Bot Token**: Set via `DISCORD_BOT_TOKEN` environment variable
- **General Channel ID**: Set via `DISCORD_GENERAL_CHANNEL_ID` environment variable

### Environment Variables

**Required:**
```bash
EMAIL_USERNAME=your_email@gmail.com
EMAIL_PASSWORD=your_app_password
```

**For Discord functionality:**
```bash
DISCORD_BOT_TOKEN=your_discord_bot_token
DISCORD_GENERAL_CHANNEL_ID=your_discord_general_channel_id
```

**Optional:**
```bash
SPRING_MAIL_HOST=smtp.gmail.com  # Default: smtp.gmail.com
SPRING_MAIL_PORT=587             # Default: 587
```

#### Windows Setup:

**Option 1: .env file (recommended for development)**

Create a `.env` file in the project root:
```env
EMAIL_USERNAME=your_email@gmail.com
EMAIL_PASSWORD=your_app_password
DISCORD_BOT_TOKEN=your_discord_bot_token
DISCORD_GENERAL_CHANNEL_ID=your_discord_general_channel_id
```

**Option 2: Command Prompt (temporary)**
```cmd
set EMAIL_USERNAME=your_email@gmail.com
set EMAIL_PASSWORD=your_app_password
```

**Option 3: PowerShell (temporary)**
```powershell
$env:EMAIL_USERNAME="your_email@gmail.com"
$env:EMAIL_PASSWORD="your_app_password"
```

**Option 4: Permanent**
```cmd
setx EMAIL_USERNAME "your_email@gmail.com"
setx EMAIL_PASSWORD "your_app_password"
```
*Note: Restart your IDE/terminal after setting permanent variables*

### Gmail App Password Setup

1. Enable 2-Factor Authentication on your Gmail account
2. Go to Google Account settings → Security → App passwords
3. Generate a new app password for "Mail"
4. Use this app password (not your regular password) as `EMAIL_PASSWORD`

## Testing with MailHog

MailHog is included for testing email functionality without sending real emails:

- **Web UI:** `http://localhost:8025`
- **SMTP Server:** `localhost:1025`

To use MailHog instead of Gmail, modify your `.env`:
```env
EMAIL_USERNAME=test@example.com
EMAIL_PASSWORD=any_password
SPRING_MAIL_HOST=mailhog
SPRING_MAIL_PORT=1025
```

## Team Development Workflow

### For Team Members Using This Service

1. **Start the notification service:**
   ```bash
   cd notification-service
   docker-compose up -d
   ```

2. **Use the service in your microservice:**
   ```bash
   # Send a test email
   curl -X POST http://localhost:8090/api/email/send \
     -H "Content-Type: application/json" \
     -d '{"to": "test@example.com", "message": "Test from my service"}'
   ```

3. **Check sent emails:**
   - Open `http://localhost:8025` to see all sent emails
   - No real emails are sent when using MailHog

### For Production Deployment

Replace MailHog configuration with real SMTP settings in your deployment environment.

## Project Structure

```
notification-service/
├── src/
│   └── main/
│       ├── java/faf/cmp/notification_service/
│       │   ├── controller/
│       │   │   ├── EmailController.java       # Email API endpoints
│       │   │   └── DiscordController.java     # Discord API endpoints
│       │   ├── service/
│       │   │   ├── EmailService.java          # Email sending logic
│       │   │   └── DiscordService.java        # Discord interaction logic
│       │   ├── request/
│       │   │   ├── SendEmailRequest.java      # Email request DTOs
│       │   │   ├── MessageRequest.java        # Discord message request
│       │   │   ├── MentionRequest.java        # Discord mention request
│       │   │   └── MultipleUsersRequest.java  # Discord multiple users request
│       │   ├── dto/
│       │   │   ├── ErrorResponse.java         # Error response DTO
│       │   │   └── SuccessResponse.java       # Success response DTO
│       │   └── NotificationServiceApplication.java
│       └── resources/
│           └── application.yml                # Application configuration
├── docker-compose.yml                         # Docker services
├── Dockerfile                                 # Container build
├── .env                                       # Environment variables
└── README.md
```

## Error Handling

The service includes comprehensive error handling:

- Invalid email addresses
- SMTP connection failures
- Authentication errors
- Network timeouts
- Discord API errors
- Channel/user/role not found errors

All errors are logged and returned as HTTP responses with descriptive messages.

## Integration

This microservice integrates with other FAFCAB Cabinet Management Platform services by:

- Providing a consistent API for triggering notifications
- Supporting various notification channels (email, Discord)
- Handling the communication with external services (SMTP, Discord API)
- Isolating notification logic from other business logic
- Offering reliable delivery with proper error handling
---

## **3. Tea Management Service**

Tracks the inventory of consumable items in the FAF Cab.

### **Responsibilities**

- Log consumption and restocking of items like tea, sugar, and paper cups.
- Automatically notify admins when supplies run low.

### **Endpoints**

**Add a New Consumable**

- `POST /api/consumables`
  - **Description:** Adds a new consumable item to the inventory.
  - **Headers:** `Authorization: Bearer <jwt>` (Admin only)
  - **Payload:**
    ```json
    {
      "consumable": "tea",
      "count": 10,
      "responsable": "user-uuid-123"
    }
    ```
  - **Success Response (201 Created):**
    ```json
    {
      "consumable_id": "tea-01",
      "name": "tea",
      "count": 10,
      "responsable": "user-uuid-123"
    }
    ```

**Get Consumables List**

- `GET /api/consumables`
  - **Description:** Returns a list of all consumables and their current count.
  - **Success Response (200 OK):**
    ```json
    [
      {
        "consumable_id": "tea-01",
        "name": "tea",
        "count": 15
      }
    ]
    ```

**Get Consumable by ID**

- `GET /api/consumables/{consumable_id}`
  - **Description:** Returns the count of a specific consumable.
  - **Success Response (200 OK):**
    ```json
    {
      "count": 14
    }
    ```

**Update Consumable Count**

- `PATCH /api/consumables/{consumable_id}`
  - **Description:** Updates the count of a consumable. If the count falls below a predefined threshold, this service automatically calls the **Notification Service** to alert admins.
  - **Headers:** `Authorization: Bearer <jwt>`
  - **Payload:**
    ```json
    {
      "count": 5
    }
    ```
  - **Success Response (200 OK):**
    ```json
    {
      "consumable_id": "tea-01",
      "name": "tea",
      "count": 5
    }
    ```

**Set Consumable Threshold**

- `POST /api/consumables/{consumable_id}?threshold=2`
  - **Description:** Sets a low-supply threshold for a consumable. This endpoint is only accessible to admins.
  - **Headers:** `Authorization: Bearer <jwt>` (Admin only)

---

## **4. Communication Service**

Manages public and private chat channels, including content moderation.

### **Responsibilities**

- Facilitate real-time messaging in different channels.
- Filter messages for banned words and manage user infractions.

### **Endpoints**

**Search for Channels**

- `GET /api/communications/search?query=<name>`
  - **Description:** Searches for a channel by name or ID.

**Create a Channel**

- `POST /api/communications/channels`
  - **Description:** Creates a new chat channel.
  - **Headers:** `Authorization: Bearer <jwt>`
  - **Payload:**
    ```json
    {
      "name": "PAD Project Group",
      "participants": ["user-uuid-456", "user-uuid-789"],
      "isPrivate": true
    }
    ```

**Add User to Channel**

- `PATCH /api/communications/channels/{channel_id}`
  - **Description:** Adds one or more new users to an existing channel.
  - **Headers:** `Authorization: Bearer <jwt>`
  - **Payload:**
    ```json
    {
      "participants": ["new-user-uuid"]
    }
    ```
  - **Success Response (200 OK):**
    ```json
    {
      "status": "Users added successfully."
    }
    ```
  - **Error Response (403 Forbidden):**
    ```json
    {
      "error": "You do not have permission to add users to this channel."
    }
    ```

**WebSocket Connection**

- `wss://api.faf/ws/communications/channels/{channel_id}?token=<JWT>`
  - **Description:** Establishes a WebSocket connection for real-time chat. The JWT is used for authentication.

**Client → Server Events (WebSocket)**

- `join_channel`: `{"type":"join_channel", "channel_id":"c123"}`
- `leave_channel`: `{"type":"leave_channel", "channel_id":"c123"}`
- `message_create`: `{"type":"message_create", "channel_id":"c123", "content":"hello", "client_ts":"2025-09-07T19:00:00Z"}`
- `message_edit`: `{"type":"message_edit", "channel_id":"c123", "message_id":"m456", "content":"edited"}`
- `typing`: `{"type":"typing", "channel_id":"c123"}`

**Server → Client Events (WebSocket)**

- `message`: `{"type":"message", "message_id":"m456", "channel_id":"c123", "user_id":"u789", "content":"...", "ts":"..."}`
- `message_deleted`: `{"type":"message_deleted", "message_id":"m456", "channel_id":"c123"}`
- `moderation_warning`: `{"type":"moderation_warning", "user_id":"u789", "reason":"banned_word", "count":1}`
- `moderation_ban`: `{"type":"moderation_ban", "user_id":"u789", "reason":"exceeded_infractions"}`

---

## **5. Cab Booking Service**

Manages room bookings for the FAF Cab main room and kitchen.

### **Responsibilities**

- Schedule meetings and events.
- Integrate with Google Calendar to prevent booking conflicts.

### **Endpoints**

**Create a Booking**

- `POST /api/bookings`
  - **Description:** Creates a new booking for the FAF Cab main room or kitchen.
  - **Headers:** `Authorization: Bearer <jwt>`
  - **Payload:**
    ```json
    {
      "place": "mainroom",
      "user_id": "user-uuid-123",
      "time_slot": "9:00-9:30",
      "description": "We will be playing catan"
    }
    ```
  - **Success Response (201 Created):** The created booking object.
  - **Error Response (409 Conflict):**
    ```json
    {
      "error": "Booking conflict detected. The requested time slot is unavailable."
    }
    ```

---

## **6. Check-in Service**

Tracks who is currently inside FAF Cab, including temporary guests.

### **Responsibilities**

- Log user entry and exit.
- Allow users to register one-time guests.
- Notify admins if an unrecognized person is detected.

### **Endpoints**

**Register a Guest**

- `POST /api/checkins`
  - **Description:** Allows a user to register a temporary guest.
  - **Headers:** `Authorization: Bearer <jwt>`
  - **Payload:**
    ```json
    {
      "temp_user": "John Doe",
      "user_id": "user-uuid-123",
      "time_slot": "9:00-9:30",
      "description": "I will be studying with my friend"
    }
    ```

**Check for Occupants**

- `GET /api/checkins/{user_id}`
  - **Description:** Simulates a CCTV check. Verifies occupants against the User Management Service and temporary guest list. If an unknown person is found, it calls the **Notification Service** to alert admins.
  - **Headers:** `Authorization: Bearer <jwt>`

---

## **7. Lost & Found Service**

A digital bulletin board for items lost or found in the university.

### **Docker**

To set up the environment, create a `.env` file in the **same directory** as your `docker-compose.yml` with the following contents:

```env
POSTGRES_USER=<POSTGRES_USER>
POSTGRES_PASSWORD=<POSTGRES_PASSWORD>
POSTGRES_DB=<POSTGRES_DB>
POSTGRES_HOST=<POSTGRES_HOST>
JWT_SECRET=<JWT_SECRET>

PHOENIX_HOST=<PHOENIX_HOST>
SECRET_KEY_BASE=<SECRET_KEY_BASE>
PHX_SERVER=true
```

This file will provide all the necessary environment variables for the Docker containers.

And this is a example for `docker-compose`

```yaml
budget:
  build: .
  restart: always
  ports:
    - "4000:4000"
  environment:
    DATABASE_URL: ecto://${POSTGRES_USER}:${POSTGRES_PASSWORD}@${POSTGRES_HOST}/${POSTGRES_DB}
    PHOENIX_HOST: ${PHOENIX_HOST}
    SECRET_KEY_BASE: ${SECRET_KEY_BASE}
    JWT_SECRET: ${JWT_SECRET}
    PHX_SERVER: true
  depends_on:
    - db
```

---

### **Docker Hub**

The service is available on Docker Hub:
[https://hub.docker.com/r/vmmmmv/lostnfound](https://hub.docker.com/r/vmmmmv/lostnfound)

### **Responsibilities**

- Allow users to create, update, and comment on posts.
- Mark posts as "resolved."

### **Endpoints**

**Create a Post**

- `POST /api/lostnfound`
  - **Description:** Creates a new post for a lost or found item.
  - **Headers:** `Authorization: Bearer <jwt>`
  - **Payload:**
    ```json
    {
      "user_id": "user-uuid-123",
      "status": "unresolved",
      "description": "I lost my will to live in faf cab. Would very grateful if somebody finds it"
    }
    ```

**Update Post Status**

- `PATCH /api/lostnfound/{post_id}`
  - **Description:** Updates the status of a post. Only the creator or an admin can update it.
  - **Headers:** `Authorization: Bearer <jwt>`
  - **Payload:**
    ```json
    {
      "status": "resolved"
    }
    ```

**WebSocket Connection**

- `wss://api.faf/ws/lostnfound/{post_id}?token=<JWT>`
  - **Description:** Establishes a WebSocket connection for real-time updates and comments on a specific post.

**Client → Server Events (WebSocket)**
***General Message Format (all events):***
    
   ```json
   {
     "topic": "lostnfound:<post_id>",
     "event": "<event_name>",
     "payload": { },
     "ref": "1"
   }
   ```
    
   -   `topic` → always `lostnfound:<post_id>`
       
   -   `event` → the action (`phx_join`, `post_message`, `list_messages`, …)
       
   -   `payload` → data sent with the event
       
   -   `ref` → client reference number (starts at `"1"`, increments per message)
   
**Join a Post Channel**

-   **Event:** `phx_join`
    
-   **Payload:**
    
    ```json
    {
      "topic": "lostnfound:1",
      "event": "phx_join",
      "payload": {},
      "ref": "1"
    }
    ```
    

**Post a Message**

-   **Event:** `post_message`
    
-   **Payload:**
    
    ```json
    {
      "topic": "lostnfound:1",
      "event": "post_message",
      "payload": {"content": "Test message"},
      "ref": "2"
    }
    ```
    

**List Messages**

-   **Event:** `list_messages`
    
-   **Payload:**
    
    ```json
    {
      "topic": "lostnfound:1",
      "event": "list_messages",
      "payload": {},
      "ref": "3"
    }
    ```
    

----------

### **Server → Client Broadcasts (WebSocket)**

**Message Posted**

-   **Event:** `post_message`
    
-   **Broadcast Payload:**
    
    ```json
    {
      "type": "post_message",
      "post_id": "1",
      "message_id": "msg-uuid-123",
      "user_id": "user-uuid-456",
      "content": "Test message",
      "ts": "2025-09-22T00:00:00Z"
    }
    ```
    

**Message List Response**

-   **Reply to `list_messages`:**
    
    ```json
    {
      "messages": [
        {
          "message_id": "msg-uuid-123",
          "post_id": "1",
          "user_id": "user-uuid-456",
          "content": "First message",
          "ts": "2025-09-22T00:00:00Z"
        },
        {
          "message_id": "msg-uuid-124",
          "post_id": "1",
          "user_id": "user-uuid-789",
          "content": "Second message",
          "ts": "2025-09-22T00:05:00Z"
        }
      ]
    }
    ```

---

## **8. Budgeting Service**

Tracks FAF Cab finances, including donations, expenses, and user debts.

### **Docker**

To set up the environment, create a `.env` file in the **same directory** as your `docker-compose.yml` with the following contents:

```env
POSTGRES_USER=<POSTGRES_USER>
POSTGRES_PASSWORD=<POSTGRES_PASSWORD>
POSTGRES_DB=<POSTGRES_DB>
POSTGRES_HOST=<POSTGRES_HOST>
JWT_SECRET=<JWT_SECRET>

PHOENIX_HOST=<PHOENIX_HOST>
SECRET_KEY_BASE=<SECRET_KEY_BASE>
```

This file will provide all the necessary environment variables for the Docker containers.

And this is a example for `docker-compose`

```yaml
budget:
  build: .
  restart: always
  ports:
    - "4000:4000"
  environment:
    DATABASE_URL: ecto://${POSTGRES_USER}:${POSTGRES_PASSWORD}@${POSTGRES_HOST}/${POSTGRES_DB}
    PHOENIX_HOST: ${PHOENIX_HOST}
    SECRET_KEY_BASE: ${SECRET_KEY_BASE}
    JWT_SECRET: ${JWT_SECRET}
    PHX_SERVER: true
  depends_on:
    - db
```

---

### **Docker Hub**

The service is available on Docker Hub:
[https://hub.docker.com/r/vmmmmv/budget](https://hub.docker.com/r/vmmmmv/budget)

### **Responsibilities**

- Maintain a transparent log of all financial transactions.
- Manage a debt book for users who damage property.
- Provide financial reports.

### **Endpoints**

**Get Budget Logs**

- `GET /api/budget`

  - **Description:** Returns the current budget.

- `GET /api/budget/logs`

  - **Description:** Returns all budget logs.

- `GET /api/budget/logs?csv=true`

  - **Description:** Returns a CSV report of budget logs. This endpoint is only accessible to admins.

**Record a Transaction**

- `POST /api/budget`

  - **Description:** Adds a new financial transaction to the budget. This endpoint is only accessible to admins.
  - **Payload:**

    ```json
    {
      "entity": "user_id or partner name",
      "affiliation": "FAF/Partner",
      "amount": -100
    }
    ```

**Add to Debt Book**

- `POST /api/budget/debt`

  - **Description:** Adds a new debt entry for a user. This endpoint is only accessible to admins.
  - **Payload:**

    ```json
    {
      "responsable_id": "user-uuid-123",
      "creator_id": "admin-uuid-001",
      "amount": 100
    }
    ```

**Get User Debt**

- `GET /api/budget/debt`

  - **Description:** Retrieves the total debt
  - **Headers:** `Authorization: Bearer <jwt>` (Admin)

- `GET /api/budget/debt?responsable_id={id}`

  - **Description:** Retrieves the debt for a specific user. Accessible by admins or the user themselves.
  - **Headers:** `Authorization: Bearer <jwt>` (Admin or the user themselves)

**Get Debt Logs**

- `GET /api/budget/debt/logs`

  - **Description:** Returns all debt logs. Accessible only by admins.

- `GET /api/budget/debt/logs?responsable_id={id}`

  - **Description:** Returns debt logs for a specific user. Accessible by admins or the user themselves.

---

## **9. Fundraising Service**

Allows admins to create fundraising campaigns for specific items.

### **Responsibilities**

- Manage fundraising campaigns, tracking goals and deadlines.
- Process user donations.
- Automatically add purchased items to the relevant service upon campaign completion.

### **Endpoints**

**Create a Campaign**

- `POST /api/fundraising`
  - **Description:** Creates a new fundraising campaign. This endpoint is only accessible to admins.
  - **Payload:**
    ```json
    {
      "user_id": "admin-uuid-001",
      "object": "New Projector",
      "object_description": "object description",
      "description": "fundraise desription",
      "goal": 750.0,
      "time_dedicated": "2 days",
      "distribute_to": "sharing"
    }
    ```

**Make a Donation**

- `PUT /api/fundraising/{fundraising}`
  - **Description:** Allows a user to make a donation to a specific fundraising campaign.
  - **Headers:** `Authorization: Bearer <jwt>`
  - **Payload:**
    ```json
    {
      "user_id": "user-uuid-123",
      "amount": 20.0
    }
    ```

**Get Campaign Status**

- `GET /api/fundraising/{fundraising_id}`
  - **Description:** Returns the current amount raised for a specific campaign.

---

## **10. Sharing Service**

Keeps track of shared, reusable items like board games, chargers, and books.

### **Responsibilities**

- Manage the inventory of shared items.
- Track who is currently using an item.
- Log the condition of items and notify owners/admins of damage.

### **Endpoints**

**Get All Items**

- `GET /api/items`
  - **Description:** Returns a list of all available items.
  - **Success Response (200 OK):**
    ```json
    [
      {
        "item_id": "game-01",
        "status": "taken",
        "name": "catan",
        "responsable": "user-uuid-456",
        "rent_period": "1 day",
        "owner": "faf cab",
        "description": "this is the game catan",
        "state": "Lmao we lost the board, oops, my bad"
      }
    ]
    ```

**Add a New Item**

- `POST /api/items`
  - **Description:** Adds a new item to the sharing inventory.
  - **Headers:** `Authorization: Bearer <jwt>`
  - **Payload:**
    ```json
    {
      "status": "available",
      "name": "new catan",
      "responsable": "",
      "rent_period": null,
      "owner": "faf cab",
      "description": "this is the new game catan",
      "state": "Not lost"
    }
    ```

**Update an Item's State**

- `PATCH /api/items/{item_id}`
  - **Description:** Updates an item's state. If the state indicates damage or loss, the service will notify the item's owner or admins.
  - **Headers:** `Authorization: Bearer <jwt>`
  - **Payload:**
    ```json
    {
      "state": "We lost the game"
    }
    ```

## Branch Structure

### Main Branches

- **`main`** - Production-ready code, always deployable
- **`development`** - Integration branch for features, staging environment

### Branch Protection Rules

- **Approvals Required**: 1 reviewers minimum
- **Dismiss Stale Reviews**: Enabled (reviews are dismissed when new commits are pushed)
- **Branch must be up to date**: Required before merging

## Branch Naming Convention

We follow a standardized naming pattern for all feature branches:

```
type/short-description-issueID
```

### Branch Types

| Prefix      | Purpose                   | Example                             |
| ----------- | ------------------------- | ----------------------------------- |
| `feature/`  | New functionality         | `feature/user-authentication-23`    |
| `bugfix/`   | Bug fixes                 | `bugfix/header-alignment-15`        |
| `hotfix/`   | Critical production fixes | `hotfix/server-crash-18`            |
| `refactor/` | Code restructuring        | `refactor/database-optimization-45` |
| `docs/`     | Documentation updates     | `docs/api-documentation-12`         |
| `chore/`    | Maintenance tasks         | `chore/dependency-updates-8`        |

### Naming Guidelines

- Use lowercase letters and hyphens
- Keep descriptions concise but descriptive
- Always include the related issue number
- Use present tense for actions

## Merging Strategy

**Strategy**: Squash and Merge

### Benefits

- Clean, linear commit history
- Combines all commits from a feature branch into a single commit
- Easier to track features and revert if necessary
- Reduces noise in the main branch history

### Process

1. Create feature branch from `development`
2. Make commits with clear, descriptive messages
3. Open Pull Request to `development`
4. After approval, squash and merge
5. Delete feature branch after merge

## Pull Request Requirements

Every Pull Request must include:

### Required Information

- **Clear description** of what changed and why
- **Issue reference** (e.g., "Closes #42", "Fixes #18")
- **List of specific changes** made
- **Testing instructions** or results
- **Screenshots** for UI changes
- **Breaking changes** (if any)

### PR Template

We use the following template (located at `.github/PULL_REQUEST_TEMPLATE.md`):

```markdown
## What does this PR do?

Brief description of the change and its purpose.

## Related Issue

Closes #XX

## Changes Made

- [ ] Added login functionality
- [ ] Fixed header spacing issue
- [ ] Updated user authentication tests
- [ ] Improved error handling

## Type of Change

- [ ] Bug fix (non-breaking change that fixes an issue)
- [ ] New feature (non-breaking change that adds functionality)
- [ ] Breaking change (fix or feature that would cause existing functionality to not work as expected)
- [ ] Documentation update

## How to Test

1. Pull this branch: `git checkout feature/branch-name`
2. Install dependencies: `npm install`
3. Run the application: `npm start`
4. Navigate to [specific page/feature]
5. Verify [specific functionality]

## Screenshots (if applicable)

[Attach images for UI changes]

## Checklist

- [ ] My code follows the team's coding standards
- [ ] I have performed a self-review of my code
- [ ] I have commented my code, particularly in hard-to-understand areas
- [ ] I have made corresponding changes to the documentation
- [ ] My changes generate no new warnings
- [ ] I have added tests that prove my fix is effective or that my feature works
- [ ] New and existing unit tests pass locally with my changes
```

## Testing Standards

### Current Requirements

- All new functions should have corresponding tests
- Run existing tests before submitting PR: `npm test`
- Manual testing steps must be documented in PR
- Critical features require integration testing

### Future Automation

- GitHub Actions will be configured for automatic testing
- All PRs must pass automated tests before merging
- Code coverage reports will be generated

## Versioning Strategy

We follow **Semantic Versioning (SemVer)**: `MAJOR.MINOR.PATCH`

### Version Types

- **MAJOR** (e.g., 1.0.0 → 2.0.0): Breaking changes that require user action
- **MINOR** (e.g., 1.0.0 → 1.1.0): New features that are backward compatible
- **PATCH** (e.g., 1.0.0 → 1.0.1): Bug fixes and small improvements

### Release Process

1. Update version in `package.json`
2. Create release notes documenting changes
3. Tag release in GitHub: `git tag v1.0.0`
4. Create GitHub Release with changelog
5. Deploy to production

### Release Notes Format

```markdown
## [1.2.0] - 2024-03-15

### Added

- User authentication system
- Dashboard analytics

### Changed

- Improved login flow UX
- Updated API endpoints

### Fixed

- Header alignment on mobile devices
- Memory leak in data processing

### Security

- Updated dependencies with security patches
```

## Code Review Guidelines

### For Reviewers

- Check code quality and adherence to standards
- Verify functionality matches requirements
- Test the changes locally when possible
- Provide constructive feedback
- Approve only when confident in the changes

### For Authors

- Respond to feedback promptly and professionally
- Make requested changes in separate commits
- Re-request review after addressing feedback
- Keep PRs focused and reasonably sized

## Workflow Summary

1. **Create Issue**: Document the feature/bug with clear requirements
2. **Create Branch**: Use proper naming convention from `development`
3. **Develop**: Make commits with clear, descriptive messages
4. **Test**: Verify functionality and run existing tests
5. **Create PR**: Follow template and provide complete information
6. **Review**: Address feedback and get required approvals
7. **Merge**: Squash and merge to `development`
8. **Deploy**: Regular releases from `development` to `main`

## Tools & Resources

- **GitHub Desktop**: For GUI-based Git operations
- **VS Code**: Recommended IDE with Git integration
- **GitHub CLI**: For command-line operations
- **Conventional Commits**: For consistent commit messages

## Team Responsibilities

- **All Team Members**: Follow branching strategy and PR requirements
- **Reviewers**: Provide timely, constructive feedback
- **Project Lead**: Manage releases and resolve conflicts
- **QA**: Test major features before production deployment

### Testing Requirements

- Unit test coverage minimum: 69 %

---
