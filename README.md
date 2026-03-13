# Healthcare Newsletter

Healthcare Newsletter is an automated research and publishing pipeline for payer and healthcare innovation news. It collects articles from selected sources, filters for signal, generates a structured summary, and prepares a repeatable weekly briefing.

## What it does

- Scrapes healthcare and payer-focused sources
- Filters content by relevance and topic
- Uses an LLM to draft concise newsletter sections
- Saves newsletter output and supporting metadata
- Supports manual runs and scheduled delivery

## Intended use

- Internal weekly market intelligence
- Payer strategy and innovation briefings
- Lightweight newsletter operations without a full editorial stack

## Workflow

1. Scrape configured sources.
2. Score and filter the articles.
3. Draft the newsletter with AI assistance.
4. Save the generated issue locally.
5. Optionally email the result to subscribers.

## Quick start

### Prerequisites

- Python 3.8+
- `pip`
- A local virtual environment

### Install

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -U pip
pip install -r requirements.txt
cp .env.example .env
```

### Configure

Edit `.env` with the credentials you need.

```bash
OPENAI_API_KEY=replace-me
EMAIL_FROM=replace-me
EMAIL_PASSWORD=replace-me
EMAIL_TO=person@example.com
NEWSLETTER_NAME=Healthcare Weekly
ORGANIZATION_NAME=Your Team
```

Adjust source and keyword behavior in `config.json`.

### Run locally

Test without sending:

```bash
python scheduler.py --test
```

Generate a manual issue:

```bash
python scheduler.py --manual
```

Run the recurring scheduler:

```bash
python scheduler.py --schedule
```

## Repository layout

- `newsletter_generator.py`: newsletter assembly logic
- `website_scrapers.py`: source-specific scraping
- `scheduler.py`: scheduling and orchestration
- `config.json`: keywords, scheduling, and configuration
- `tests/`: automated coverage for the core newsletter flow

## Output

- Markdown newsletter files
- Generation statistics and logs
- Optional outbound email delivery

## Product notes

- This repo is most useful when it shows a concrete sample issue and a stable source list.
- If you keep it public, update the README whenever the source mix or output format changes.
- The strongest positioning is "repeatable healthcare intelligence pipeline," not "generic scraper."

## Status

Current status: active workflow prototype with local automation support.

## License

MIT
