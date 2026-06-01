# Technical Design

This document describes the technical architecture for AI Tech Radar. It is aligned with the MVP decisions in the main README:

- Active MVP sources: GitHub and Hugging Face.
- Active MVP notification channel: Telegram.
- Default digest language: English.
- Realtime updates: implemented through frequent polling.
- Default refresh interval: 15 minutes, configurable by the user.
- Default digest generation time: 08:05 local time, configurable by the user.
- Digest output: Top 5 items per section, with source links.
- Ranking priority: globally notable trends.
- Relevance scoring: rule-based in MVP.
- Report storage: PostgreSQL, with optional Markdown export.

arXiv, RSS feeds, and email are included in the architecture as extension points, but they do not need to be fully implemented in the first MVP iteration.

## 1. System Architecture

### High-Level Flow

```text
Scheduler
  -> Data Collectors
  -> Normalization Pipeline
  -> Deduplication Engine
  -> Ranking Engine
  -> Digest Generator
  -> Notification Service
```

### Architecture Diagram

```mermaid
flowchart TD
    Scheduler[APScheduler] --> RefreshJob[Realtime Refresh Job]
    Scheduler --> DigestJob[Daily Digest Job]
    Scheduler --> DeliveryJob[Delivery Job]

    RefreshJob --> Collectors[Data Collectors]
    Collectors --> Normalizer[Normalization Service]
    Normalizer --> NormalizedStorage[(Normalized Items)]
    NormalizedStorage --> Deduplicator[Deduplication Service]
    Deduplicator --> Ranking[Ranking Service]
    Ranking --> Scores[(Scores)]
    Scores --> DigestGenerator[Digest Generator]
    DigestGenerator --> Reports[(Reports)]
    DigestGenerator --> Markdown[Markdown Export]
    Reports --> Notification[Notification Service]
    Notification --> Telegram[Telegram]
    Notification -.future.-> Email[Email]
```

## 2. Components

### Scheduler

The scheduler is responsible for triggering background jobs.

Technology:

- APScheduler

Jobs:

- Realtime refresh job: runs every 15 minutes by default.
- Digest job: runs daily at 08:05 local time by default.
- Delivery job: sends the generated digest to notification channels.

The refresh interval and daily workflow times should be configurable through environment variables or application settings.

### Data Collector Service

The data collector service fetches data from external sources and returns source payloads for immediate normalization.

MVP collectors:

- GitHub collector
- Hugging Face collector

Designed extension collectors:

- arXiv collector
- RSS collector

Output:

- Source-specific collected payloads

Responsibilities:

- Fetch source data.
- Attach source name, source ID, and fetch timestamp.
- Handle API pagination and rate limits.
- Fail independently per source so one broken source does not stop the whole refresh.

### Normalization Service

The normalization service converts source-specific data into a shared schema.

Output:

- `NormalizedItem`

Fields:

| Field | Description |
| --- | --- |
| `id` | Internal item ID |
| `source` | Source name, for example `github` or `huggingface` |
| `type` | Item type, for example `repository`, `model`, `dataset`, `space`, `paper`, or `article` |
| `title` | Human-readable title |
| `description` | Short description, abstract, or summary |
| `url` | Canonical source URL |
| `tags` | Topics, labels, categories, or task types |
| `published_at` | Publish or creation timestamp |
| `metadata` | Source-specific metrics and extra fields |

Examples of metadata:

- GitHub: stars, forks, topics, contributors, last commit timestamp.
- Hugging Face: downloads, likes, tags, task type.
- arXiv: authors, category, abstract, publish date.
- RSS: feed name, author, published date.

### Deduplication Service

The deduplication service removes duplicate or near-duplicate content before ranking and digest generation.

Deduplication rules:

1. Same canonical URL.
2. Same repository name.
3. Similar title above 90%.

Winner selection:

- Retain the item with the highest ranking score.
- If scores are not available yet, retain the item with better source metrics.
- If metrics are equal, retain the most recently fetched item.

Implementation note:

- URL and repository matching should be deterministic.
- Title similarity can use normalized lowercase text with punctuation removed, then compare using a string similarity algorithm such as Levenshtein ratio or token set ratio.

### Ranking Service

The ranking service calculates a final trend score for each normalized item.

Inputs:

- Popularity
- Recency
- Activity
- Relevance

Output:

- `Score`

Formula:

```text
Final Score =
  0.4 * Popularity Score +
  0.3 * Recency Score +
  0.2 * Activity Score +
  0.1 * Relevance Score
```

MVP relevance scoring should be rule-based. Rules should prioritize globally notable AI, software engineering, open source, model, and research trends.

### Digest Generator

The digest generator creates a Markdown report from ranked items.

Output:

- `Digest`

Responsibilities:

- Select Top 5 items per section.
- Include source links for every item.
- Generate English output by default.
- Support Vietnamese output as a configurable option.
- Save digest content to PostgreSQL.
- Export Markdown when enabled.

Recommended sections for MVP:

1. Top GitHub Repositories
2. Top AI Models
3. Top Datasets and Spaces
4. Interesting Releases

### Notification Service

The notification service sends generated digests to configured channels.

MVP channel:

- Telegram

Future channel:

- Email

Telegram behavior:

- Send multiple messages instead of one long message.
- Send one overview message.
- Send one message per digest section.
- Include source links in each item.

Email behavior is part of a future phase and should remain behind an interface or stub until needed.

## 3. Folder Structure

Recommended Python project layout:

```text
src/
├── main.py
├── config/
│   ├── settings.py
│   └── sources.yaml
├── scheduler/
│   └── jobs.py
├── collectors/
│   ├── github.py
│   ├── huggingface.py
│   ├── arxiv.py
│   └── rss.py
├── pipeline/
│   ├── normalize.py
│   ├── deduplicate.py
│   ├── ranking.py
│   └── digest.py
├── notification/
│   ├── telegram.py
│   └── email.py
├── repositories/
│   ├── item_repository.py
│   └── digest_repository.py
├── models/
│   ├── item.py
│   ├── digest.py
│   └── score.py
└── tests/
```

### Directory Responsibilities

| Path | Responsibility |
| --- | --- |
| `src/main.py` | Application entry point |
| `src/config/` | Settings, environment parsing, source configuration |
| `src/scheduler/` | APScheduler setup and job definitions |
| `src/collectors/` | External data source clients |
| `src/pipeline/` | Normalization, deduplication, ranking, digest generation |
| `src/notification/` | Telegram and email delivery |
| `src/repositories/` | Database access layer |
| `src/models/` | Domain models and schemas |
| `src/tests/` | Unit and integration tests |

## 4. Data Models

### NormalizedItem

Stores source-independent data used by the pipeline.

```text
NormalizedItem
- id
- source
- source_id
- type
- title
- description
- url
- tags
- published_at
- metadata
- created_at
```

### Score

Stores score components and the final ranking score.

```text
Score
- id
- item_id
- popularity_score
- recency_score
- activity_score
- relevance_score
- final_score
- scored_at
```

### Digest

Stores generated report content.

```text
Digest
- id
- report_date
- title
- content_markdown
- content_text
- language
- created_at
- sent_at
```

## 5. Job Execution

### Realtime Refresh Job

Frequency:

- Every 15 minutes by default.

Steps:

1. Load enabled sources from configuration.
2. Run each source collector.
3. Normalize collected payloads.
4. Deduplicate normalized items.
5. Upsert normalized items.
6. Recalculate scores.
7. Log source-level success or failure.

### Daily Digest Job

Frequency:

- Once per day at 08:05 local time by default.

Steps:

1. Load normalized items for the reporting window.
2. Deduplicate items.
3. Calculate ranking scores.
4. Select Top 5 items per section.
5. Generate Markdown digest.
6. Store digest in PostgreSQL.
7. Export Markdown if enabled.

### Delivery Job

Steps:

1. Load latest unsent digest.
2. Split digest by Telegram section.
3. Send overview message.
4. Send section messages.
5. Mark digest as sent.

## 6. Configuration

Environment variables:

```env
DATABASE_URL=postgresql://user:password@postgres:5432/ai_tech_radar
GITHUB_TOKEN=
HUGGINGFACE_TOKEN=
TELEGRAM_BOT_TOKEN=
TELEGRAM_CHAT_ID=
TOP_N_ITEMS=5
DIGEST_LANGUAGE=en
ENABLE_REALTIME_UPDATES=true
REALTIME_REFRESH_INTERVAL_MINUTES=15
DIGEST_TIME_LOCAL=08:05
EXPORT_MARKDOWN_REPORTS=true
```

Source configuration should live in `src/config/sources.yaml`.

Example:

```yaml
github:
  enabled: true
  trending_enabled: true
  api_enabled: true

huggingface:
  enabled: true
  models_enabled: true
  datasets_enabled: true
  spaces_enabled: true

arxiv:
  enabled: false
  categories:
    - cs.AI
    - cs.LG
    - cs.CL
    - cs.CV

rss:
  enabled: false
  feeds: []
```

## 7. Deployment Architecture

Supported deployment:

- Docker Compose

Deployment target:

- Linux VPS

Services:

- `app`: Python application, scheduler, collectors, pipeline, and notification services.
- `postgres`: PostgreSQL database.

Optional future service:

- `redis`: cache, queue, or distributed lock store if needed.

Network:

- Internal Docker network.

Volumes:

- `postgres_data`
- Optional Markdown report export volume.

Recommended Compose services:

```text
app
postgres
```

## 8. Reliability and Error Handling

Source failures should be isolated. A GitHub failure should not prevent Hugging Face data from being collected, and a notification failure should not delete or lose the generated digest.

Recommended handling:

- Retry transient HTTP failures.
- Store refresh errors with source name and timestamp.
- Respect API rate limits.
- Use timeouts for external requests.
- Mark reports as sent only after successful delivery.
- Preserve existing normalized items when a refresh source fails.

## 9. Testing Strategy

Recommended test coverage:

- Collector response parsing.
- Normalization from each source format.
- Deduplication rules.
- Ranking formula and score boundaries.
- Digest formatting.
- Telegram message splitting.
- Repository persistence.

MVP tests should focus on deterministic pipeline behavior before broad integration coverage.

## 10. Related Documents

- [Database Design](database-design.md)
- [API Contract](api-contract.md)
- [Workflow Specification](workflows.md)
