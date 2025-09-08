# FAF Cab Management Platform - Communication Contract

This document outlines the communication contracts for the microservices within the FAF Cab Management Platform. All services that require user authentication or user-specific information will validate requests using a **JWT (JSON Web Token)** provided in the `Authorization` header.

---
## Overview

The FAF Cab Management Platform is designed to improve the organization and operational efficiency of FAF Cab, with modular microservices for user management, communication, booking, consumable tracking, fundraising, and more. Each microservice encapsulates a specific domain to ensure modularity, independence, and maintainability.

Microservices are implemented using multiple technologies to optimize performance and leverage language-specific strengths:

* **Java/Spring Boot:** User Management, Notification, Budgeting, Fundraising, Sharing
* **Elixir:** Communication Service, Tea Management, Lost & Found, Budgeting
* **JavaScript/Node.js:** Cab Booking, Check-in

---
# Technologies & Communication Patterns
---

| Team             | Services                          | Language & Framework        | Database       | Communication Patterns                   | Motivation & Trade-offs                                                                                                                                                                                                                                                                                                      |
|------------------|---------------------------------|----------------------------|----------------|-----------------------------------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| Vieru Mihai      | Lost & Found, Budgeting          | Elixir          | PostgreSQL     | REST, Asynchronous notifications, WebSocket (Phoenix Channels) | Elixir’s ability to handle high concurrency and fault tolerance is ideal for budget and lost & found services that require reliable multi-user interaction and asynchronous notifications.            |
| Polisciuc Vlad   | Tea Management Service, Communication Service | Elixir        |      | REST, Async notifications                | Elixir excels at real-time, low-latency systems. Its lightweight processes and OTP supervision enhance fault tolerance, perfect for consumable tracking and live chat. Cowboy's native WebSocket support enables efficient bi-directional communication, crucial for the communication service's real-time messaging and moderation features.                      |
| Ungureanu Vlad   | Cab Booking, Check-in            | Node.js, Express           | PostgreSQL     | REST, Async loops, External API integration (Google Calendar)   | Node.js is exceptionally well-suited for applications like booking systems due to its event-driven, non-blocking I/O model. When the system needs to perform an action that relies on an external service, such as fetching data from the Google Calendar API, it sends the request and immediately proceeds to handle other tasks without waiting for a response. This asynchronous capability means the application doesn't get stuck, allowing its lightweight runtime to efficiently manage many simultaneous user requests.                      |
| Tapu Pavel       | Fundraising, Sharing             | Java, Spring Boot          | PostgreSQL     | REST with JWT auth, Async notification queues | Java and Spring Boot provide a mature, secure, and scalable framework for handling critical business workflows like fundraising and item sharing. Strong security features (JWT auth) and stable async processing suit admin-controlled services requiring transactional integrity and complex business logic.                         |
| Copta Adrian     | User Management, Notification    | Java, Spring Boot          | PostgreSQL     | REST, Async event-driven updates        | The Spring ecosystem offers robust authentication (including JWT), authorization, and notification capabilities critical for user and notification management. Because of high developer productivity and strong integration with databases and enterprise security standards, it makes ideal for core identity and communication services.       |

# Architectural Diagram of Microservices operation

![microserv](https://github.com/user-attachments/assets/2c87e83c-0a08-4641-9613-bbea49de16f1)

The diagram above illustrates the microservices architecture designed for the FAFCab system. It highlights how different services, such as Notification Service, Communication Service, Budgeting Service, Fund Raising Service, Tea Management Service, and User Management Service, interact with each other through the API Gateway and Service Registry. Each service is responsible for a specific function, ranging from financial tracking and consumable management to user check-ins, booking, and lost-and-found operations. The modular design ensures that responsibilities are clearly separated, making the system scalable, maintainable, and easier to extend with new features as needed.
## **1. User Management Service**

Handles user registration, authentication, and synchronization with the FAF Community Discord server.

### **Responsibilities**

- Register new users via Discord OAuth.
- Sync user roles (student, teacher, admin) from the FAF Discord server.
- Issue JWTs upon successful login for use with other services.

### **Endpoints**

**Login and Create User**

- `POST /api/auth/login`
  - **Description:** Authenticates a user with their Discord token, creates a user profile if one doesn't exist, and returns a JWT.
  - **Payload:**
    ```json
    {
      "discord_token": "<user_discord_oauth_token>"
    }
    ```
  - **Success Response (200 OK):**
    ```json
    {
      "jwt": "<jwt_token>",
      "user_id": "user-uuid-123",
      "roles": ["student", "FAF_NGO_Member"]
    }
    ```

**Get User Information**

- `GET /api/users/{user_id}`

  - **Description:** Retrieves public information for a specific user.
  - **Headers:** `Authorization: Bearer <jwt>`
  - **Success Response (200 OK):**
    ```json
    {
      "user_id": "user-uuid-123",
      "nickname": "faf_user",
      "group": "FAF-211",
      "roles": ["student", "FAF_NGO_Member"]
    }
    ```

- `GET /api/users?limit=1000`

  - **Description:** Provides a list of all users.
  - **Headers:** `Authorization: Bearer <jwt>`

- `GET /api/users/admins?limit=1000`

  - **Description:** Returns a list of all users with the 'admin' role.
  - **Headers:** `Authorization: Bearer <jwt>`

- `GET /api/users/teachers?limit=1000`
  - **Description:** Returns a list of all users with the 'teacher' role.
  - **Headers:** `Authorization: Bearer <jwt>`

---

## **2. Notification Service**

Responsible for sending notifications to users and groups via Discord.

### **Responsibilities**

- Send targeted messages to individual users or groups (e.g., admins).
- Manage Discord channel creation for direct messages.

### **Endpoints**

**Send Notification**

- `POST /api/notifications`
  - **Description:** Sends a message to specified users or groups. The service handles the logic of finding or creating the correct Discord channels.
  - **Headers:** `Authorization: Bearer <jwt>`
  - **Payload:**
    ```json
    {
      "users": ["user-uuid-123", "user-uuid-456"],
      "groups": ["admins"],
      "message": "Heads up: The tea supply is running low!"
    }
    ```
  - **Success Response (202 Accepted):**
    ```json
    {
      "status": "Notification request queued successfully."
    }
    ```

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

- `subscribe_post`: `{"type":"subscribe_post", "post_id":"p123"}`
- `post_message`: `{"type":"post_message", "post_id":"p123", "content":"Damn bro thats crazy", "client_ts":"..."}`

**Server → Client Events (WebSocket)**

- `post_message`: `{"type":"post_message", "post_id":"p123", "message_id":"m1", "user_id":"uX", "content":"...", "ts":"..."}`
- `post_updated`: `{"type":"post_updated", "post_id":"p123", "status":"resolved"}`
- `moderation_warning`: `{"type":"moderation_warning", "user_id":"u789", "reason":"banned_word", "count":1}`
- `moderation_ban`: `{"type":"moderation_ban", "user_id":"u789", "reason":"exceeded_infractions"}`

---

## **8. Budgeting Service**

Tracks FAF Cab finances, including donations, expenses, and user debts.

### **Responsibilities**

- Maintain a transparent log of all financial transactions.
- Manage a debt book for users who damage property.
- Provide financial reports.

### **Endpoints**

**Get Budget Logs**

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

- `GET /api/budget/debt/{responsable_id}`
  - **Description:** Retrieves the debt for a specific user. Accessible by admins or the user themselves.
  - **Headers:** `Authorization: Bearer <jwt>` (Admin or the user themselves)

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
| Prefix | Purpose | Example |
|--------|---------|---------|
| `feature/` | New functionality | `feature/user-authentication-23` |
| `bugfix/` | Bug fixes | `bugfix/header-alignment-15` |
| `hotfix/` | Critical production fixes | `hotfix/server-crash-18` |
| `refactor/` | Code restructuring | `refactor/database-optimization-45` |
| `docs/` | Documentation updates | `docs/api-documentation-12` |
| `chore/` | Maintenance tasks | `chore/dependency-updates-8` |

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
