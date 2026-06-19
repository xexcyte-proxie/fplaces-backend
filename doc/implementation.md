# fPlaces - Implementation Document

This document details the internal technical structure, database design, and key components of the fPlaces application.

---

## 1. System Architecture & Tech Stack
fPlaces is a decoupled real-time backend platform built using the following stack:
- **Programming Language**: Python 3.12+
- **Web & API Framework**: Django 6.0+ & Django REST Framework (DRF) 3.17+
- **Asynchronous & WebSocket Layer**: Django Channels 4.3+ & Daphne ASGI Server
- **Authentication**: `djangorestframework-simplejwt` (JSON Web Tokens)
- **Database**: PostgreSQL (production/staging) and SQLite3 (local development)
- **Email Delivery**: Resend SDK (`resend` 2.32+)
- **API Documentation**: OpenAPI 3.0 via `drf-spectacular`
- **Dashboard Interface**: Django Admin customized with template overrides for API controls

---

## 2. Django Project App Structure
The codebase is divided into modular Django apps:

### 2.1 `core`
Provides base classes, utilities, and middleware shared across all apps:
- `BaseModel`: Abstract model providing `created_at`, `updated_at`, and soft-delete (`is_archived`) fields.
- `BaseManager` / `BaseQuerySet`: Automatically filters out soft-deleted/archived records by default.
- `custom_exception_handler`: Standardizes all API error responses into a consistent envelope structure.
- `LogRequest` & `UpdateLastLoginMiddleware`: Tracks request activity and updates user login times.
- `consumers.py` & `realtime.py`: Implements base WebSocket consumer logic and channels broadcast wrappers.

### 2.2 `users`
Manages users, authentication, onboarding, and admin dashboards:
- `User`: Custom user model inheriting from `AbstractBaseUser` and `PermissionsMixin`. Uses `email` as the primary identifier instead of a username.
- `EmailVerificationOTP`: Model holding a 6-digit verification code associated with a user, with an expiry field. Registered in the Django admin panel (`users/admin.py`).
- `UserManager`: Custom manager handling user creation and exclusion of archived profiles.
- `views/auth.py`: Implements Registration, OTP Verification, Login, Logout, and Password Reset.
- `serializers/auth.py`: Contains validation rules, password constraints, and JWT data formatting.
- `serializers/admin.py`: Serializer for detailed admin user info and the unified dashboard stats structure.
- `views/admin.py`:
  - `AdminStatsView`: Unified API for dashboard analytics.
  - `AdminUserViewSet`: Restricted API viewset for user administration (suspension/archival, restoration, and staff privilege toggles).

### 2.3 `forum`
Implements the core location-based discussion board:
- `Venue`: Physical locations (stadiums/arenas) where posts are scoped.
- `Section`: Physical subsections of a venue (e.g. "Gate 4", "Family Stand").
- `Category`: Categories for grouping posts ("Lines and Crowds", "Food and Drinks", "Fan Vibe", "Help").
- `Post`: 140-character user submissions, containing counts for upvotes and flags. Can be marked as `hidden`.
- `Comment`: User comments on specific posts.
- `PostVote`: Tracks user upvotes on posts.
- `PostFlag`: Tracks user flags on posts.
- `views/`: Viewsets using DRF's `ModelViewSet` pattern with custom actions for upvoting, flagging, hiding, and showing posts.
- `serializers/admin.py`: Admin post serializer displaying full internal details of posts.
- `views/admin.py`:
  - `AdminPostViewSet`: Viewset for post moderation, including hide/show actions, flagged posts filter, flag-clearing, and soft-delete/restoration.

### 2.4 `notifications`
Handles notification persistence and delivery:
- `Notification`: Stores actions (`comment`, `upvote`, `moderation`) by an `actor` towards a `recipient`.
- `services/mail.py`: Directs outbound email via the Resend API. Supports redirecting all messages to a single `SEND_TO_EMAIL` address during testing.
- `consumers.py`: Real-time WebSocket connection to push notifications to active users.

---

## 3. Database Schema Design (Entity-Relationship)

### 3.1 `users.User`
- `id` (int, PK)
- `email` (varchar, unique)
- `password` (varchar)
- `pseudo_name` (varchar, unique, nullable)
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

### 3.3 `forum.Venue`
- `id` (int, PK)
- `name` (varchar, unique)
- `location` (varchar)
- `latitude` (decimal, nullable)
- `longitude` (decimal, nullable)
- `notes` (text)
- `is_archived` (boolean)

### 3.4 `forum.Section`
- `id` (int, PK)
- `venue_id` (int, FK to Venue)
- `name` (varchar)
- `code` (varchar)
- `is_active` (boolean)
- `is_archived` (boolean)

### 3.5 `forum.Category`
- `id` (int, PK)
- `name` (varchar, unique)
- `slug` (varchar, unique)
- `description` (varchar)
- `disclaimer` (varchar)
- `order` (int)
- `is_active` (boolean)
- `is_archived` (boolean)

### 3.6 `forum.Post`
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

### 3.7 `forum.Comment`
- `id` (int, PK)
- `post_id` (int, FK to Post)
- `user_id` (int, FK to User)
- `content` (text)
- `is_archived` (boolean)
- `created_at` (datetime)
- `updated_at` (datetime)

### 3.8 `notifications.Notification`
- `id` (int, PK)
- `recipient_id` (int, FK to User)
- `actor_id` (int, FK to User, nullable)
- `verb` (varchar: `comment`, `upvote`, `moderation`)
- `post_id` (int, FK to Post, nullable)
- `comment_id` (int, FK to Comment, nullable)
- `message` (varchar)
- `is_read` (boolean, default=False)
- `is_archived` (boolean)
- `created_at` (datetime)
- `updated_at` (datetime)
