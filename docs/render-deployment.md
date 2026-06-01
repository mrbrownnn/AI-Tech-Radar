# Render Deployment

AI Tech Radar can be deployed on Render with the Blueprint in `render.yaml`.

## Resources

The Blueprint creates:

- Web service: `ai-tech-radar`
- PostgreSQL database: `ai-tech-radar-db`

## Required Secrets

Render prompts for these values during Blueprint setup:

```env
GITHUB_TOKEN=
HUGGINGFACE_TOKEN=
TELEGRAM_BOT_TOKEN=
TELEGRAM_CHAT_ID=
```

Do not hardcode these secrets in `render.yaml`.

## Runtime Behavior

The app runs as a Docker web service. It starts FastAPI and the in-process scheduler.

Enabled jobs:

- Realtime refresh every 15 minutes.
- Daily digest generation at `08:05` Asia/Bangkok time.
- Daily delivery at `08:06` Asia/Bangkok time.
- Telegram command long polling.

## Database URL

Render Postgres provides `DATABASE_URL` as a `postgresql://...` connection string. The application normalizes this to `postgresql+psycopg://...` for SQLAlchemy.

If the app fails with:

```text
psycopg.OperationalError: [Errno -2] Name or service not known
```

check the Render service environment variables. `DATABASE_URL` must not point to Docker Compose host `postgres`.

Correct Render options:

- Deploy with the Blueprint so `DATABASE_URL` is injected from `ai-tech-radar-db`.
- Or manually set `DATABASE_URL` to the Render Postgres **Internal Database URL**.

Incorrect on Render:

```env
DATABASE_URL=postgresql+psycopg://ai_tech_radar:ai_tech_radar@postgres:5432/ai_tech_radar
```

That URL only works inside local Docker Compose.

## Deploy Steps

1. Open Render Dashboard.
2. Select **New +**.
3. Select **Blueprint**.
4. Connect the GitHub repository.
5. Confirm the detected `render.yaml`.
6. Enter the required secret values.
7. Apply the Blueprint.

If you created the web service manually instead of using the Blueprint, also create a Render Postgres database and set the web service `DATABASE_URL` to that database's internal connection string.

## Smoke Test

After deployment, open:

```text
https://<your-render-service>.onrender.com/health
```

Expected response:

```json
{"status":"ok"}
```

Then test Telegram:

```text
/status
/items
/run
```
