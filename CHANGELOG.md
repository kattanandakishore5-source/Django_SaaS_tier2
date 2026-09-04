# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2026-09-04

### Added
- **Core:** Custom user model (email-based), authentication, and RBAC roles (Owner, Manager, Viewer).
- **Security:** Immutable audit logging middleware.
- **Authentication:** Passwordless magic-link authentication with secure, single-use, time-limited tokens.
- **Security:** Two-Factor Authentication (2FA) via TOTP using pyotp and enforced via Pending2FAMiddleware.
- **Billing:** Stripe SaaS billing integration with webhooks, subscriptions, and pricing tiers.
- **Access Control:** Centralized entitlement layer (@require_feature, HasFeatureAccess) to enforce subscription access policies.
- **DevOps:** Docker production readiness with multi-container orchestration (Gunicorn, Postgres, Redis, Celery).
- **CI/CD:** Automated GitHub Actions pipeline with security scanning, testing, and Docker build validation.
