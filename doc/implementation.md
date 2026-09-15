# fplaces - Implementation Document

This document details the internal technical structure, database design, and key components of the fplaces application.

---

## 1. System Architecture & Tech Stack

fplaces is a decoupled real-time backend platform built using the following stack:

- **Programming Language**: Python 3.12+
- **Web & API Framework**: Django 6.0+ & Django REST Framework (DRF) 3.17+
- **Asynchronous & WebSocket Layer**: Django Channels 4.3+ & Daphne ASGI Server
- **Authentication**: `djangorestframework-simplejwt` (JSON Web Tokens), plus Google OAuth login and a short-lived, account-less guest JWT flow
- **Database**: PostgreSQL (production/staging) and SQLite3 (local development); the test suite always runs against an in-memory SQLite database regardless of the configured backend, so it never touches the shared Postgres instance
- **Email Delivery**: Resend SDK (`resend` 2.32+)
- **Interactive Venue Map**: Mappedin (2D/AR map + individual location pins), proxied through a thin `map` app
- **API Documentation**: OpenAPI 3.0 via `drf-spectacular`, plus a standalone `doc/frontend_integration_guide.html` served at `/api/guide.html` for WebSocket contracts OpenAPI can't express
- **Dashboard Interface**: Django Admin customized with template overrides for API controls
- **Deployment**: Docker image built and deployed to AWS Fargate (ECS/ECR) via a GitHub Actions pipeline (`.github/workflows/deploy.yml`); infrastructure defined in Terraform (`terraform/`)

---

## 2. Django Project App Structure

The codebase is divided into modular Django apps:

### 2.1 `core`

Provides base classes, utilities, and middleware shared across all apps:

- `BaseModel`: Abstract model providing `created_at`, `updated_at`, and soft-delete (`is_archived`) fields.
- `BaseManager` / `BaseQuerySet`: Automatically filters out soft-deleted/archived records by default.
- `custom_exception_handler`: Standardizes all API error responses into a consistent envelope structure.
- `LogRequest` & `UpdateLastLoginMiddleware`: Tracks request activity and updates user login times.
- `consumers.py` & `realtime.py`: Implements base WebSocket consumer logic, channel-group naming (including hashing opaque ids like a Mappedin `location_id` into a valid, bounded-length group name), and channels broadcast wrappers.

### 2.2 `users`

Manages users, authentication, onboarding, guest access, and admin dashboards:

- `User`: Custom user model inheriting from `AbstractBaseUser` and `PermissionsMixin`. Uses `email` as the primary identifier instead of a username. Also carries `pseudo_name`, `first_name`, `last_name`, `bio`, `avatar_url`, `user_type` (`regular_user`/`admin`), and a free-form `interests` list.
- `EmailVerificationOTP`: Model holding a 6-digit verification code associated with a user, with an expiry field. Registered in the Django admin panel (`users/admin.py`).
- `GuestSession`: Tracks a per-`device_fingerprint` trial window (start/expiry, IP, feature-tried flags) backing the account-less guest access flow. Not a `User` row — guest JWTs carry `token_type=guest` and a synthetic `sub`, not a resolvable `user_id`.
- `UserManager`: Custom manager handling user creation and exclusion of archived profiles.
- `views/auth.py`: Implements Registration, OTP Verification, Standard + Google Login, Logout, Token Refresh, and Password Reset/Change.
- `views/guest.py`: Issues short-lived guest JWTs bundled with Mappedin credentials, and lets a guest update tracked preference flags.
- `views/profile.py`: `MeView` (get/update/delete the authenticated user's own profile, including `interests`, aggregate `stat`, and `recent_posts`) and `ChangePasswordView`.
- `serializers/auth.py`: Contains validation rules, password constraints, and JWT data formatting.
- `serializers/admin.py`: Serializer for detailed admin user info and the unified dashboard stats structure.
- `views/admin.py`:
  - `AdminStatsView`: Unified API for dashboard analytics.
  - `AdminUserViewSet`: Restricted API viewset for user administration (archival, restoration, and staff privilege toggling).

### 2.3 `forum`

Implements the core location-based discussion board and map-pin chat:

- `Venue`: Physical locations (stadiums/arenas) where posts are scoped, including an associated Mappedin `mappedin_map_id`.
- `Section`: A small, admin-curated set of physical subsections of a venue (e.g. "North Stand", "VIP") used for onboarding, optional post tagging, and the heatmap.
- `Category`: Categories for grouping posts ("Lines and Crowds", "Food and Drinks", "Fan Vibe", "Help").
- `Interest`: Curated catalog of profile interest tags (e.g. "Stats and scores", "Photography"), served publicly for the frontend's interest picker.
- `Post`: 140-character user submissions, containing counts for upvotes and flags. Can be marked as `hidden`.
- `Comment`: Flat, 1-level user comments on specific posts; broadcast over the parent post's venue room.
- `PostVote`: Tracks user upvotes on posts.
- `PostFlag`: Tracks user flags on posts.
- `LocationConversation`: The chat "channel" for a single `(venue, location_id)` pair, where `location_id` is an opaque, client-supplied Mappedin location id — not a `Section`. Unique per `(venue, location_id)`; created lazily on the first message.
- `LocationMessage`: An individual chat message on a `LocationConversation`.
- `views/`: Viewsets using DRF's `ModelViewSet` pattern with custom actions for upvoting, flagging, hiding, and showing posts, plus a find-or-create `create()` override on the location-conversation viewset.
- `consumers.py`: `VenueConsumer` (venue-wide feed/heatmap room) and `LocationConsumer` (one room per `(venue, location_id)` chat).
- `serializers/admin.py`: Admin post serializer displaying full internal details of posts.
- `views/admin.py`:
  - `AdminPostViewSet`: Viewset for post moderation, including hide/show actions, flagged posts filter, flag-clearing, and soft-delete/restoration.

### 2.4 `notifications`

Handles notification persistence and delivery:

- `Notification`: Stores actions (`comment`, `upvote`, `moderation`, `broadcast`) by an `actor` towards a `recipient`.
- `services/mail.py`: Directs outbound email via the Resend API. Supports redirecting all messages to a single `SEND_TO_EMAIL` address during testing.
- `services/notify.py`: Creates a `Notification` row and pushes it live over the recipient's personal WebSocket.
- `consumers.py`: Real-time WebSocket connection to push notifications to active users.
- `views/admin.py`: `AdminNotificationViewSet` — lets staff broadcast an email and/or push notification to users matched by venue, section, category, or explicit user ids.

### 2.5 `map`

Thin proxy around the Mappedin API:

- `services/mappedin.py`: Fetches a short-lived Mappedin access token using server-held API credentials.
- `views.py`: `GET /api/maps/token/` — authenticated endpoint returning that token so the client can render the venue's interactive 2D/AR map. Guests instead receive an equivalent token bundled directly into their guest-access response.

### 2.6 `payments`

Scaffolded for future use; contains no models or endpoints yet.

---

## 3. Database Schema Design (Entity-Relationship)

### 3.1 `users.User`

- `id` (int, PK)
- `email` (varchar, unique)
- `password` (varchar)
- `pseudo_name` (varchar, unique, nullable)
- `first_name` (varchar, blank)
- `last_name` (varchar, blank)
- `bio` (text, blank)
- `avatar_url` (varchar, nullable)
- `user_type` (varchar: `regular_user` / `admin`)
- `interests` (JSON array of strings, nullable) — free-form, matched against `forum.Interest` names by the frontend
- `is_email_verified` (boolean, default=False)
- `is_staff` (boolean, default=False)
- `is_active` (boolean, default=True)
- `is_archived` (boolean, default=False)
- `created_at` (datetime)
- `updated_at` (datetime)

### 3.2 `users.EmailVerificationOTP`

- `id` (int, PK)
- `user_id` (int, FK to User, unique)
- `otp_code` (varchar)
- `expires_at` (datetime)
- `is_archived` (boolean, default=False)
- `created_at` (datetime)
- `updated_at` (datetime)

### 3.3 `users.GuestSession`

- `id` (int, PK)
- `device_fingerprint` (varchar, unique)
- `ip_address` (varchar)
- `trial_started_at` (datetime)
- `trial_expires_at` (datetime)
- `has_tried_ar_view` (boolean, default=False)
- `has_tried_2d_view` (boolean, default=False)
- `last_seen_at` (datetime)
- `is_archived` (boolean, default=False)
- `created_at` (datetime)
- `updated_at` (datetime)

### 3.4 `forum.Venue`

- `id` (int, PK)
- `name` (varchar, unique)
- `location` (varchar)
- `latitude` (decimal, nullable)
- `longitude` (decimal, nullable)
- `mappedin_map_id` (varchar, nullable)
- `notes` (text)
- `is_archived` (boolean)

### 3.5 `forum.Section`

- `id` (int, PK)
- `venue_id` (int, FK to Venue)
- `name` (varchar)
- `code` (varchar)
- `is_active` (boolean)
- `is_archived` (boolean)
- unique together: `(venue_id, name)`

### 3.6 `forum.Category`

- `id` (int, PK)
- `name` (varchar, unique)
- `slug` (varchar, unique)
- `description` (varchar)
- `disclaimer` (varchar)
- `order` (int)
- `is_active` (boolean)
- `is_archived` (boolean)

### 3.7 `forum.Interest`

- `id` (int, PK)
- `name` (varchar, unique)
- `slug` (varchar, unique)
- `order` (int)
- `is_active` (boolean)
- `is_archived` (boolean)
- `created_at` (datetime)
- `updated_at` (datetime)

### 3.8 `forum.Post`

- `id` (int, PK)
- `user_id` (int, FK to User)
- `venue_id` (int, FK to Venue)
- `section_id` (int, FK to Section, nullable)
- `category_id` (int, FK to Category)
- `content` (varchar)
- `upvotes_count` (int)
- `flags_count` (int)
- `status` (varchar: `visible` / `hidden`)
- `is_archived` (boolean)
- `created_at` (datetime)
- `updated_at` (datetime)

### 3.9 `forum.Comment`

- `id` (int, PK)
- `post_id` (int, FK to Post)
- `user_id` (int, FK to User)
- `content` (text)
- `is_archived` (boolean)
- `created_at` (datetime)
- `updated_at` (datetime)

### 3.10 `forum.PostVote`

- `id` (int, PK)
- `post_id` (int, FK to Post)
- `user_id` (int, FK to User)
- `is_archived` (boolean) — an inactive (soft-archived) vote represents a removed upvote, not a deleted row, so the idempotent toggle can restore it
- `created_at` (datetime)
- `updated_at` (datetime)
- unique together: `(post_id, user_id)`

### 3.11 `forum.PostFlag`

- `id` (int, PK)
- `post_id` (int, FK to Post)
- `user_id` (int, FK to User)
- `reason` (varchar, blank)
- `is_archived` (boolean)
- `created_at` (datetime)
- `updated_at` (datetime)

### 3.12 `forum.LocationConversation`

- `id` (int, PK)
- `venue_id` (int, FK to Venue)
- `location_id` (varchar, max 255) — opaque Mappedin location/place id, exact match, never rewritten
- `location_name` (varchar, blank) — display name, set on create or backfilled later if blank
- `is_archived` (boolean)
- `created_at` (datetime)
- `updated_at` (datetime)
- unique together: `(venue_id, location_id)` — this pair is the channel's identity; found-or-created atomically on first message

### 3.13 `forum.LocationMessage`

- `id` (int, PK)
- `conversation_id` (int, FK to LocationConversation)
- `user_id` (int, FK to User)
- `content` (text, max 500)
- `is_archived` (boolean)
- `created_at` (datetime)
- `updated_at` (datetime)

### 3.14 `notifications.Notification`

- `id` (int, PK)
- `recipient_id` (int, FK to User)
- `actor_id` (int, FK to User, nullable)
- `verb` (varchar: `comment`, `upvote`, `moderation`, `broadcast`)
- `post_id` (int, FK to Post, nullable)
- `comment_id` (int, FK to Comment, nullable)
- `message` (varchar)
- `is_read` (boolean, default=False)
- `is_archived` (boolean)
- `created_at` (datetime)
- `updated_at` (datetime)
