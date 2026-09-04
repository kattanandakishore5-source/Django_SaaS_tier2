# Operational Runbook

## Observability & Logging
Logs are printed to standard out/error and captured by Docker.
- **View all logs:** docker compose logs -f
- **View Django logs:** docker compose logs -f web
- **View Celery logs:** docker compose logs -f celery

*Note: Secrets (like passwords, 2FA codes, Stripe keys) are strictly redacted and never logged.*

## Health Checks
- **Liveness & Readiness:** Handled internally via Docker health checks (pg_isready, edis-cli ping).
- **Application Health:** A lightweight GET /health/ endpoint is available to verify the Django web server is responsive.

## Handling Dependency Failures
### PostgreSQL (Database)
- **If DB goes down:** Django will gracefully return a standard 500 error page without leaking credentials or stack traces.
- **To restart DB:** docker compose restart db
- **Recovery:** Django will automatically reconnect to the database upon the next request.

### Redis (Cache & Celery Broker)
- **If Redis goes down:** Celery workers will pause, and new tasks will fail to queue. Django cache operations will degrade safely.
- **To restart Redis:** docker compose restart redis
- **Recovery:** Celery automatically reconnects to the broker.

### Celery (Background Workers)
- **If Worker crashes:** Unfinished tasks remain in the Redis queue.
- **To restart Celery:** docker compose restart celery
- **Recovery:** Upon restart, the worker will consume the backlog. Tasks use utoretry_for with exponential backoff on failure.

### Stripe Webhooks
- Webhook processing is idempotent and wrapped in a database transaction (	ransaction.atomic()).
- Unverified, malformed, or duplicate webhooks are safely ignored and logged at WARNING or ERROR levels without exposing sensitive tracebacks to Stripe.
