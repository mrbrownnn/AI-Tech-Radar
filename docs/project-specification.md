# AI Tech Radar Project Specification

AI Tech Radar is an automated system that collects, ranks, and delivers a daily digest of important technology updates across AI, software engineering, open source, and research.

The system is designed to run without user interaction. It frequently refreshes selected data sources, upserts normalized data, removes duplicates, ranks items by importance, generates one daily digest, and sends the result through Telegram in the MVP.

Project documentation:

- [Technical Design](technical-design.md)
- [Database Design](database-design.md)
- [API Contract](api-contract.md)
- [Workflow Specification](workflows.md)

## Product Goals

AI Tech Radar helps engineers and founders reduce the time spent manually tracking technology news and trends across many fragmented sources.

Continuously, the system should:

1. Refresh data from configured sources.
2. Normalize data into a shared schema.
3. Upsert normalized items directly into the database.
4. Remove duplicate or highly similar entries.
5. Calculate and update importance scores.
6. Keep ranked items fresh for API and Telegram commands.
7. Generate one daily digest report.
8. Send the digest to Telegram.
9. Archive generated reports for historical review.

## Target Users

The initial version is built for a single user.

Primary users include:

- Software Engineers
- AI Engineers
- Backend Engineers
- Research Engineers
- Startup Founders

Future versions may support multiple users, personalized preferences, dashboard access, team workspaces, and SaaS-style multi-tenancy.

## MVP Scope

The MVP focuses on automated collection and Telegram delivery.

Included:

- GitHub repositories
- Hugging Face models, datasets, and spaces
- Telegram digest delivery
- PostgreSQL persistence
- Docker Compose deployment

First implementation priority:

- GitHub
- Hugging Face

Planned after the first MVP iteration:

- arXiv papers
- RSS sources

Excluded from MVP:

- Dashboard
- Multi-user support
- Authentication
- AI summarization
- Vector search
- Email delivery
- Personalized ranking

## Data Sources

### GitHub

GitHub data is used to detect fast-growing repositories, active open source projects, and emerging developer tools.

Collected fields:

- Repository name
- Description
- Stars
- Forks
- Topics
- Contributors
- Last commit timestamp

Sources:

- GitHub API
- GitHub Trending

### Hugging Face

Hugging Face data is used to track trending models, datasets, spaces, and AI tooling.

Collected entities:

- Models
- Datasets
- Spaces

Collected metadata:

- Downloads
- Likes
- Tags
- Task type

### arXiv

arXiv data is used to track new research papers in AI and machine learning.

Target categories:

- `cs.AI`
- `cs.LG`
- `cs.CL`
- `cs.CV`

Collected fields:

- Title
- Authors
- Abstract
- Publish date

### RSS Sources

RSS sources are planned for broader trend detection and release monitoring.

Target sources:

- Hacker News
- Product Hunt
- InfoQ
- Thoughtworks Radar
- OpenAI Blog
- Anthropic Blog
- DeepMind Blog

RSS collection can be added after the MVP source pipeline is stable.

## System Workflow

```mermaid
flowchart TD
    Scheduler[Scheduler] --> Crawlers[Crawlers]
    Crawlers --> Normalizer[Normalizer]
    Normalizer --> Deduplicator[Deduplication Engine]
    Deduplicator --> Ranking[Ranking Engine]
    Ranking --> Selector[Top N Selector]
    Selector --> Digest[Digest Generator]
    Digest --> Archive[Report Archive]
    Digest --> Telegram[Telegram Sender]
```

### 1. Scheduling

The system runs near-real-time refresh jobs on a configurable interval. Because GitHub and Hugging Face do not provide a single global push feed for this use case, realtime behavior is implemented as frequent polling.

The default refresh interval is 15 minutes. Digest generation runs once per day at 08:05 local time by default.

### 2. Crawling

Each crawler is responsible for one external source. Collector output is normalized and upserted directly into the `items` table; the system no longer stores raw source payloads.

### 3. Normalization

Different source types are converted into a common item schema. This allows a shared ranking and digest pipeline across repositories, models, papers, and articles.

### 4. Deduplication

The system removes duplicate entries before ranking. Deduplication should use stable source identifiers where possible and fallback similarity matching when identifiers are unavailable.

Examples:

- Same GitHub repository URL
- Same Hugging Face model ID
- Same arXiv paper ID
- Same canonical article URL
- Highly similar title and source combination

### 5. Ranking

Each normalized item receives a final score based on popularity, recency, activity, and relevance.

### 6. Digest Generation

The digest generator converts ranked items into a concise report grouped by category.

### 7. Delivery

The MVP sends the generated digest to Telegram. The digest should be split into multiple Telegram messages by section instead of sending one long message. Email delivery is planned for a later phase.

## Ranking Engine

The final ranking score is calculated using weighted sub-scores.

```text
Final Score =
  0.4 * Popularity Score +
  0.3 * Recency Score +
  0.2 * Activity Score +
  0.1 * Relevance Score
```

### Popularity Score

Measures public interest.

Example signals:

- GitHub stars
- GitHub forks
- Hugging Face downloads
- Hugging Face likes
- Hacker News points
- Product Hunt votes

### Recency Score

Measures how fresh an item is.

Example signals:

- Publish date
- Last commit date
- Release date
- First seen timestamp

### Activity Score

Measures whether the item is actively maintained or gaining momentum.

Example signals:

- Recent commits
- Contributor activity
- Recent downloads
- Recent discussion volume
- Update frequency

### Relevance Score

Measures how closely an item matches the desired domains.

The MVP should prioritize globally notable trends over narrow personal preferences.

Initial relevance topics:

- Artificial intelligence
- Machine learning
- Large language models
- Agents
- Developer tools
- Software engineering
- Open source infrastructure
- Research papers

## Digest Format

The daily digest should be short, scannable, and grouped by source type. The default digest language is English, and Vietnamese should be supported as a configurable option.

Recommended structure:

```text
Daily AI Tech Radar

1. Top GitHub Repositories
2. Top AI Models
3. Top Datasets and Spaces
4. Interesting Releases
```

Each item should include:

- Title
- Source
- Short description
- Key metrics
- Reason it was selected
- Link to the original source

Each section should include the top 5 items.

Telegram delivery should send separate messages for each section:

```text
Message 1: Daily AI Tech Radar overview
Message 2: Top 5 GitHub Repositories
Message 3: Top 5 AI Models
Message 4: Top 5 Datasets and Spaces
Message 5: Interesting Releases
```

Example item format:

```text
1. example/repo
   A short description of what the project does.
   Stars: 12,400 | Forks: 820 | Last Commit: 2026-06-01
   Why it matters: Rapidly growing open source AI developer tool.
   Link: https://github.com/example/repo
```

## Suggested Data Model

### Normalized Items

Stores source-independent item data used for ranking and digest generation.

| Field | Description |
| --- | --- |
| `id` | Internal ID |
| `source` | Source name |
| `source_id` | Source-specific stable ID |
| `type` | `repository`, `model`, `dataset`, `space`, `paper`, or `article` |
| `title` | Display title |
| `description` | Short description or abstract |
| `url` | Canonical URL |
| `authors` | Authors or owners |
| `tags` | Topics, categories, or labels |
| `published_at` | Publish timestamp |
| `last_activity_at` | Last known activity timestamp |
| `metrics` | Source-specific metrics as JSON |
| `created_at` | Internal creation timestamp |

### Ranked Items

Stores score calculations for reproducibility.

| Field | Description |
| --- | --- |
| `id` | Internal ID |
| `item_id` | Related normalized item |
| `popularity_score` | Popularity component |
| `recency_score` | Recency component |
| `activity_score` | Activity component |
| `relevance_score` | Relevance component |
| `final_score` | Weighted final score |
| `scored_at` | Score calculation timestamp |

### Reports

Stores generated digest reports.

| Field | Description |
| --- | --- |
| `id` | Internal ID |
| `report_date` | Digest date |
| `title` | Report title |
| `content_markdown` | Markdown digest content |
| `content_text` | Plain text digest content |
| `created_at` | Generation timestamp |
| `sent_at` | Delivery timestamp |

Reports should be stored in PostgreSQL and exported as Markdown when needed. Markdown output makes it easier to review reports manually and allows future agents or automation workflows to reuse the generated digest content.

## Non-Functional Requirements

| Requirement | Target |
| --- | --- |
| Availability | 99% |
| Maximum digest generation time | Less than 5 minutes |
| Maximum refresh time | Less than 30 minutes |
| Data retention | 12 months |
| Deployment | Docker Compose |
| Database | PostgreSQL |
| Programming language | Python |

## Deployment

The supported deployment target is Docker Compose.

Recommended services:

- `app`: Python application containing crawlers, ranking, digest generation, and delivery logic.
- `postgres`: PostgreSQL database.
- `scheduler`: Scheduled job runner, if separated from the main app.

## Running Locally

Create an environment file:

```bash
cp .env.example .env
```

Update `.env` with real credentials when available:

- `GITHUB_TOKEN`
- `HUGGINGFACE_TOKEN`
- `TELEGRAM_BOT_TOKEN`
- `TELEGRAM_CHAT_ID`

Run with Docker Compose:

```bash
docker compose up --build
```

The API will be available at:

```text
http://localhost:8000
```

Useful endpoints:

- `GET /health`
- `POST /refresh`
- `POST /crawl`
- `POST /digest`
- `POST /notify`
- `GET /items`
- `GET /digests/latest`

Run tests locally:

```bash
pip install -r requirements-dev.txt
python -m pytest -q src/tests
```

Recommended configuration:

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
DELIVERY_TIME_LOCAL=08:06
EXPORT_MARKDOWN_REPORTS=true
ENABLE_TELEGRAM_COMMANDS=true
```

## Telegram Commands

Telegram bot commands are enabled when `ENABLE_TELEGRAM_COMMANDS=true` and both `TELEGRAM_BOT_TOKEN` and `TELEGRAM_CHAT_ID` are configured.

Available commands:

- `/start` - confirm the bot is connected.
- `/help` - show available commands.
- `/status` - show service and database status.
- `/items` - show top ranked items.
- `/latest` - send the latest stored digest.
- `/refresh` - refresh data now.
- `/crawl` - refresh data now, kept as a compatibility alias.
- `/digest` - generate a digest from current ranked items.
- `/notify` - send the latest digest.
- `/run` - run refresh, digest, and notify.

## Roadmap

### Phase 1: MVP

- Implement GitHub crawler.
- Implement Hugging Face crawler.
- Store normalized data in PostgreSQL.
- Implement deduplication.
- Implement rule-based ranking and relevance scoring.
- Generate daily digest.
- Send digest to Telegram.
- Archive reports.
- Export reports as Markdown.

### Phase 2

- Implement arXiv crawler.
- Add AI summarization.
- Add personalized ranking.
- Add email digest.
- Add more RSS sources.

### Phase 3

- Add dashboard.
- Add user preferences.
- Add search.

### Phase 4

- Add multi-tenant support.
- Add team workspaces.
- Add SaaS billing and account model.

## Success Metrics

The project is successful when:

- A digest is generated every day.
- Refresh success rate is greater than 95%.
- Duplicate rate is less than 5%.
- Data processing time is less than 5 minutes.
- The user accepts the top trending results as useful and relevant.

## Confirmed MVP Decisions

These decisions are fixed for the MVP:

1. Digest delivery runs once per day.
2. Near-real-time data updates are implemented through frequent polling.
3. Default refresh interval is 15 minutes.
4. Default digest generation time is 08:05 local time.
5. Default digest language is English.
6. Vietnamese digest output should be supported as a configurable option.
7. Each digest section includes the top 5 items.
8. Each digest item must include a source link.
9. Telegram delivery should use multiple messages split by section.
10. The MVP uses GitHub and Hugging Face first.
11. GitHub Trending should be included.
12. Ranking should prioritize globally notable trends.
13. Relevance scoring should be rule-based in the MVP.
14. Reports should be stored in PostgreSQL.
15. Reports should also support Markdown export for future extension.
