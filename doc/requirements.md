# fplaces - Product Requirements Document (PRD)

fplaces is a real-time, venue-scoped social platform designed for sports fans, event attendees, and venue visitors. Users within the same stadium or venue can share a live feed tied to physical sections, post comments, upvote, flag posts, chat around specific map locations, and view crowd-sourced section heatmaps.

---

## 1. Core Objectives

- **Hyper-Local Engagement**: Restrict and focus social interactions to physical venues, down to individual map locations.
- **Real-Time Delivery**: Enable instant feed updates, chat, notifications, and interaction stats over WebSockets.
- **Frictionless Entry**: Let visitors try the app as a guest (no account) before committing to registration.
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
  - Authenticate using email and password, or via Google OAuth (`id_token`) — an unrecognized Google email is auto-registered and auto-verified.
  - Return a JWT token pair (Access token and Refresh token). Access tokens expire after 30 minutes; refresh tokens after 14 days and rotate/blacklist on use.
  - Support logout by blacklisting the refresh token.
- **Guest Access**:
  - Let a visitor obtain a short-lived, scoped guest JWT using only an `ip_address` and `device_fingerprint` — no account required.
  - Track a per-device trial window (valid for the calendar day of first use); once expired, guests are prompted to register.
  - Bundle Mappedin map credentials into the same guest response so a guest can view the venue map immediately.
  - Guest tokens are rejected by every endpoint that requires a full user account (they carry no resolvable `user_id`).
- **Onboarding Profile**:
  - Require users to select a unique `pseudo_name` via `PATCH /api/users/me/` before allowing them to post or interact in a venue.
  - Let users optionally select `interests` (an array of names) from a curated, backend-served catalog, shown as picker tags on their profile.
- **Password Reset & Change**:
  - Request a password reset email containing a link with token parameters (`uid` and `token`).
  - Confirm password reset using the token link to set a new password.
  - Let a logged-in user change their password directly (`old_password` + `new_password`) without an email round-trip.

### 2.2 User Profile & Interests

- **Interests Catalog**:
  - Expose a public, backend-served catalog of interests (curated tags such as "Stats and scores", "Photography") so the picker is never hardcoded on the frontend.
  - Admins manage the catalog (create/update/retire); users select from it when setting their `interests`.
- **Profile Stats**:
  - A user's own profile response includes an aggregate `stat` object: `posts_count` (posts authored), `upvotes_count` (upvotes received across those posts), and `venues_count` (distinct venues posted in).
  - The profile also includes `recent_posts`: the user's 5 most recently created posts, for a "Recent Posts" section on the profile screen.

### 2.3 Venue, Section & Map Management

- **Venues**:
  - Represent physical locations (e.g., arenas, stadiums) with a name, location, latitude, longitude, an associated Mappedin map id, and optional notes.
- **Sections**:
  - Represent a small, admin-curated set of physical zones within a venue (e.g., "North Stand", "VIP Box"), used for onboarding, optionally tagging posts, and the section heatmap.
  - Distinct from map locations (below): Sections are hand-picked by admins and stay small in number; they are never auto-created.
- **Interactive Map (Mappedin)**:
  - Authenticated users and guests can fetch a short-lived Mappedin token to render the venue's interactive 2D/AR map and browse its many individual map locations/pins.

### 2.4 Live Feed (Posts)

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

### 2.5 Comments

- Users can leave a flat (1-level) comment thread on any post.
- Creating a comment broadcasts a `new_comment` event to the post's venue websocket room (not a separate socket), and notifies the post's author (unless they're commenting on their own post).
- Only a comment's own author or staff may edit or soft-delete it.

### 2.6 Section Heatmaps

- **Post-based Heatmap**:
  - Tracks crowd activity by counting the number of visible (non-hidden, non-archived) posts in each admin-curated Section.
  - Updates are broadcasted in real-time when a post is created or hidden.

### 2.7 Moderation & Hiding

- **Flagging**:
  - Users can flag posts for moderation with an optional reason.
  - Toggling/flagging is idempotent per user per post.
  - Flag counts are tracked on the post.
- **Moderator Actions**:
  - Staff members can hide posts (`status=hidden`), which removes them from all non-staff feeds.
  - Staff can un-hide/show posts (`status=visible`).
  - Hiding a post broadcasts a `post_hidden` event over the WebSocket, causing clients to immediately remove it from their UI.

### 2.8 Location (Map-Pin) Conversations

- Chat is scoped to a `(venue, location_id)` pair, where `location_id` is the opaque Mappedin location/place id a fan tapped on the map — **not** an admin Section.
- The client never creates a conversation id up front: the first message posted for a never-seen `location_id` at a venue finds-or-creates its conversation automatically. No admin seeding is required, and map locations are never turned into Sections.
- Listing a location's messages before anyone has posted returns an empty list, not an error.
- Only a message's own author or staff may edit or soft-delete it.
- New messages broadcast live to clients currently viewing that specific location's chat, without touching the venue-wide feed socket.

### 2.9 Real-Time WebSocket Events

- **Venue Room Socket (`ws/venues/<venue_id>/`)**:
  - Broadcasts the following events to all users connected to the venue room:
    - `new_post`: When a post is created.
    - `new_comment`: When a comment is added to any post in the venue.
    - `upvote_update`: When a post's upvote count changes.
    - `section_heat_update`: When a post is added/removed in a section, changing the activity heatmap.
    - `post_hidden`: When a post is hidden by staff.
- **Location Room Socket (`ws/venues/<venue_id>/locations/<location_id>/`)**:
  - Pushes `new_location_message` events to clients viewing that specific map location's chat only.
- **Notification Socket (`ws/notifications/`)**:
  - Pushes real-time user-specific notifications to connected clients.

### 2.10 In-App Notifications

- Create and push notifications to users for:
  - **Comments**: When someone comments on a user's post.
  - **Upvotes**: When someone upvotes a user's post.
  - **Moderation**: When a user's post is hidden/moderated by staff.
  - **Broadcast**: When an admin sends a targeted announcement (see 2.11).
- Users can fetch their notifications, check an unread count for a badge, mark them as read individually, or mark all as read.

### 2.11 Administrative Control & Dashboard APIs

- **Admin Stats Overview**:
  - Provide a dashboard stats endpoint fetching total registrations, verified users count, posts/comments metrics, and breakdowns of activity per venue and category.
- **User Administration**:
  - Administrators must be able to list all users, view details, soft-delete/archive users, restore archived users, and toggle staff privileges.
- **Content Moderation**:
  - Access a dedicated flagged posts queue sorted by flag count descending.
  - Clear flags on a post once resolved.
  - Soft-delete or restore posts.
- **Broadcast Notifications**:
  - Send a targeted email and/or in-app push notification to users matched by venue, section, category, or explicit user ids (a union of whichever filters are given).
  - Delivery is best-effort per user/channel; the response reports how many sends actually succeeded.
- **Documentation Access**:
  - Expose Swagger/Redoc endpoints to the public (`AllowAny`).
  - Integrate interactive documentation links directly in the Django Admin sidebar, alongside a frontend integration guide.

---

## 3. Non-Functional Requirements

- **Performance**: Heavy feed reads and real-time broadcasts should be optimized to support concurrent users during live events.
- **Security**: Access tokens must expire quickly (30 minutes), requiring refresh tokens to maintain sessions. Guest tokens are further scoped (no resolvable user identity, short lifetime, capped trial window). Cross-Origin Resource Sharing (CORS) and WebSockets must authenticate tokens properly.
- **Data Integrity**: Soft-delete ensures that even if users delete content, records remain available for safety audit compliance and moderation histories.
- **Opaque External Identifiers**: Third-party ids (e.g. Mappedin `location_id`) are treated as opaque strings — never slugified, normalized, or rewritten — since the frontend and Mappedin are the source of truth for their shape.
