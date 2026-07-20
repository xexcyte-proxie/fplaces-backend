# fplaces - Implementation & User Flow Document

This document outlines the workflows and sequences of interactions between users, the REST API, the WebSocket server, and backend services.

---

## 1. Onboarding and Verification Flow

The onboarding flow ensures that users verify their email addresses via a One-Time Password (OTP) before they are allowed to complete their profile setup and fully interact on the platform.

```mermaid
sequenceDiagram
    autonumber
    actor User as Fan / User
    participant Client as Frontend / Client
    participant API as Django REST API
    participant DB as Database
    participant EmailService as Resend Email Service

    User->>Client: Enters email and password
    Client->>API: POST /api/users/register/
    Note over API: Create User (is_email_verified=False)
    Note over API: Generate 6-digit OTP
    API->>DB: Save EmailVerificationOTP record
    API->>EmailService: Send verify_email template
    EmailService-->>User: Receives 6-digit OTP code in email
    API-->>Client: Returns 201 Created & User details
    Client->>User: Prompts for OTP code
    User->>Client: Enters OTP code
    Client->>API: POST /api/users/verify-email/ (email + otp)
    Note over API: Check if user exists & is unverified
    Note over API: Match OTP code & check if expired (< 15 mins)
    API->>DB: Set is_email_verified=True
    API->>DB: Delete verification OTP record
    API-->>Client: Returns 200 OK & Verified User details
    Client->>User: Prompts to set profile pseudo_name
    User->>Client: Enters pseudo_name
    Client->>API: PATCH /api/users/me/ (pseudo_name)
    API->>DB: Update User record
    API-->>Client: Returns 200 OK
```

---

## 2. Real-Time Venue Discussion Feed Flow

Once onboarding is completed, users join a venue room to receive live posts, comments, upvote updates, and heatmaps.

```mermaid
sequenceDiagram
    autonumber
    actor User as Active Fan
    participant Client as Client Application
    participant API as REST API
    participant WS as WebSocket (Daphne)
    participant Redis as Redis (Channel Layer)

    Client->>API: GET /api/forum/venues/ (List venues)
    API-->>Client: Returns venues list with coordinates
    User->>Client: Selects Venue
    Client->>API: GET /api/forum/posts/?venue={id} (Load history)
    API-->>Client: Returns initial paginated feed
    Client->>WS: Establish Connection to ws/venues/{id}/?token={JWT}
    Note over WS: Authenticates JWT token
    WS-->>Client: WebSocket Connection Accepted
    Note over Client: Subscribed to venue_{id} Channel Group

    User->>Client: Submits a new post
    Client->>API: POST /api/forum/posts/
    API->>Redis: group_send("venue_{id}", "new_post", data)
    Redis->>WS: Forward event
    WS-->>Client: Pushes 'new_post' event payload (All connected users in venue)
```

---

## 3. Post Interaction Flow (Upvoting & Flagging)

### 3.1 Upvoting (Idempotent Toggle)

- User requests to upvote a post.
- If a `PostVote` record for `(post, user)` does not exist:
  - Create it.
  - Increment the post's `upvotes_count` by 1.
  - Broadcast an `upvote_update` event (`upvoted=True`) to the venue's WebSocket group.
- If the `PostVote` record already exists and is active:
  - Soft-archive it (`is_archived=True`).
  - Decrement the post's `upvotes_count` by 1.
  - Broadcast an `upvote_update` event (`upvoted=False`) to the WebSocket group.
- If the `PostVote` record exists but is soft-archived:
  - Restore it (`is_archived=False`).
  - Increment the post's `upvotes_count` by 1.
  - Broadcast an `upvote_update` event (`upvoted=True`).

### 3.2 Flagging (Moderation Request)

- User flags a post for moderation with a `reason`.
- Database atomically creates or restores the `PostFlag` record for `(post, user)`.
- If new or restored, the post's `flags_count` is incremented.
- Flags are moderator-facing only; no WebSocket event is broadcast to the public feed.

---

## 4. Moderation & Post Hiding Flow

```mermaid
sequenceDiagram
    autonumber
    actor Admin as Staff / Moderator
    participant Client as Admin Panel
    participant API as REST API
    participant DB as Database
    participant Redis as Redis (Channel Layer)
    participant WS as WebSocket Room
    participant Fan as Active Fans

    Admin->>Client: Selects post to hide
    Client->>API: POST /api/forum/posts/{id}/hide/ (Staff only)
    API->>DB: Set status='hidden' on Post
    API->>Redis: group_send("venue_{id}", "post_hidden", {post_id})
    Redis->>WS: Forward event
    WS-->>Fan: Pushes 'post_hidden' payload
    Note over Fan: Removes post from UI list
    API-->>Client: Returns 200 OK
```

---

## 5. In-App Notifications Flow

Notifications are created synchronously and dispatched immediately over the user's personal WebSocket.

1. **Trigger Action**: User A comments on User B's post.
2. **Persistence**:
   - Check if User A (actor) is not User B (recipient).
   - Create a `Notification` record in the database (`recipient=User B`, `actor=User A`, `verb='comment'`).
3. **Real-time Push**:
   - Call `broadcast("user_UserB_id", "new_notification", notification_data)`.
   - Connected WebSockets of User B receive the payload and increment their unread notification badge count in real-time.

---

## 6. Admin Control Flows

Dedicated administrative actions permit complete dashboard customization and system moderation.

### 6.1 Admin Stats Check

- Admin opens Dashboard -> Client hits `GET /api/admin/stats/`.
- Backend aggregates metrics across Users, Posts, Comments, and active Venues, querying specific post counts per category and venue.
- Returns dashboard statistics package to Admin.

### 6.2 Flagged Content Moderation

- Admin retrieves the moderation queue via `GET /api/admin/posts/flagged/` (sorted by flag count descending).
- Admin reviews a flagged post and clicks **Clear Flags**.
- Client calls `POST /api/admin/posts/{id}/clear-flags/`.
- Backend resets `flags_count` to `0` and soft-archives all related `PostFlag` records.
