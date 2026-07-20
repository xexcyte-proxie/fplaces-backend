# fplaces - Product Requirements Document (PRD)

fplaces is a real-time, venue-scoped social platform designed for sports fans, event attendees, and venue visitors. Users within the same stadium or venue can share a live feed tied to physical sections, post comments, upvote, flag posts, and view crowd-sourced section heatmaps.

---

## 1. Core Objectives

- **Hyper-Local Engagement**: Restrict and focus social interactions to physical venues.
- **Real-Time Delivery**: Enable instant feed updates, notifications, and interaction stats over WebSockets.
- **Safety and Moderation**: Incorporate crowd-sourced flagging and staff-controlled post hiding to keep feeds clean.
- **Privacy First**: Allow users to interact under a custom pseudo-name without revealing their real name or email address.

---

## 2. Functional Requirements

### 2.1 User Management & Authentication

- **Registration**:
  - Sign up using email and password.
  - Require verification via a 6-digit One-Time Password (OTP) sent to the user's email.
  - Accounts remain unverified (`is_email_verified=False`) until OTP verification is completed.
- **Login**:
  - Authenticate using email and password.
  - Return a JWT token pair (Access token and Refresh token).
- **Onboarding Profile**:
  - Require users to select a unique `pseudo_name` via `PATCH /api/users/me/` before allowing them to post or interact in a venue.
- **Password Reset**:
  - Request password reset email containing a link with token parameters (`uid` and `token`).
  - Confirm password reset using the token link to set a new password.

### 2.2 Venue & Section Management

- **Venues**:
  - Represent physical locations (e.g., arenas, stadiums) with a name, location, latitude, longitude, and optional notes.
- **Sections**:
  - Represent physical divisions within a venue (e.g., "North Stand", "Section 104", "VIP Box").
  - Tied to a specific venue. Used for posts and section heatmaps.

### 2.3 Live Feed (Posts)

- **Post Creation**:
  - Users can publish posts (max 140 characters).
  - Posts are linked to a specific venue and category, and optionally a section.
  - Creating a post immediately broadcasts it to the venue's websocket room.
- **Categories**:
  - Posts must belong to a predefined set of categories:
    - _Lines and Crowds_
    - _Food and Drinks_
    - _Fan Vibe_
    - _Help_
- **Upvotes**:
  - Idempotent upvoting: clicking upvote once upvotes the post; clicking it again removes the upvote.
  - Enforce one vote per user per post.
- **Soft Delete**:
  - Deleting a post sets `is_archived=True`. The database record is preserved, but excluded from regular feeds.
  - Support restoring archived posts.

### 2.4 Section Heatmaps

- **Post-based Heatmap**:
  - Tracks crowd activity by counting the number of visible (non-hidden, non-archived) posts in each section.
  - Updates are broadcasted in real-time when a post is created or hidden.

### 2.5 Moderation & Hiding

- **Flagging**:
  - Users can flag posts for moderation with an optional reason.
  - Toggling/flagging is idempotent per user per post.
  - Flag counts are tracked on the post.
- **Moderator Actions**:
  - Staff members can hide posts (`status=hidden`), which removes them from all non-staff feeds.
  - Staff can un-hide/show posts (`status=visible`).
  - Hiding a post broadcasts a `post_hidden` event over the WebSocket, causing clients to immediately remove it from their UI.

### 2.6 Real-Time WebSocket Events

- **Venue Room Socket (`ws/venues/<venue_id>/`)**:
  - Broadcasts the following events to all users connected to the venue room:
    - `new_post`: When a post is created.
    - `new_comment`: When a comment is added.
    - `upvote_update`: When a post's upvote count changes.
    - `section_heat_update`: When a post is added/removed in a section, changing the activity heatmap.
    - `post_hidden`: When a post is hidden by staff.
- **Notification Socket (`ws/notifications/`)**:
  - Pushes real-time user-specific notifications to connected clients.

### 2.7 In-App Notifications

- Create and push notifications to users for:
  - **Comments**: When someone comments on a user's post.
  - **Upvotes**: When someone upvotes a user's post.
  - **Moderation**: When a user's post is hidden/moderated by staff.
- Users can fetch their notifications, mark them as read individually, or mark all as read.

### 2.8 Administrative Control & Dashboard APIs

- **Admin Stats Overview**:
  - Provide a dashboard stats endpoint fetching total registrations, verified users count, posts/comments metrics, and breakdowns of activity per venue and category.
- **User Administration**:
  - Administrators must be able to list all users, view details, soft-delete/archive users, restore archived users, and promote/demote accounts to staff.
- **Content Moderation**:
  - Access a dedicated flagged posts queue sorted by flag count descending.
  - Clear flags on a post once resolved.
  - Soft-delete or restore posts.
- **Documentation Access**:
  - Expose Swagger/Redoc endpoints to the public (`AllowAny`).
  - Integrate interactive documentation links directly in the Django Admin sidebar.

---

## 3. Non-Functional Requirements

- **Performance**: Heavy feed reads and real-time broadcasts should be optimized to support concurrent users during live events.
- **Security**: Access tokens must expire quickly (30 minutes), requiring refresh tokens to maintain sessions. Cross-Origin Resource Sharing (CORS) and WebSockets must authenticate tokens properly.
- **Data Integrity**: Soft-delete ensures that even if users delete content, records remain available for safety audit compliance and moderation histories.
