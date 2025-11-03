# Repository Guidelines

## Project Structure & Module Organization
- `newsletter_generator.py` orchestrates scraping, filtering, summarizing, and email delivery; helper functions stay near the bottom for saving output.
- `website_scrapers.py` houses scraper classes and should be extended per source; keep imports lightweight to avoid blocking scheduler startup.
- `scheduler.py` exposes CLI flags for manual, test, and scheduled runs, writing status to `newsletter_scheduler.log`.
- `newsletters/` stores generated markdown and `stats_*.json` snapshots, while `logs/` captures operational traces. Shared security helpers live in `security_utils.py`; keep configuration in `config.json` and secrets in `.env`.

## Build, Test, and Development Commands
Install Python 3.10+ dependencies via `pip install -r requirements.txt`. Routine commands:
```bash
python security_test.py        # exercises validation and sandbox checks
python scheduler.py --test     # full dry run, saves test newsletter
python scheduler.py --manual   # generates and emails the live newsletter
python scheduler.py --schedule # launches persistent weekly scheduler
python email_test.py           # verifies SMTP credentials end-to-end
```
Run each command from the repository root so relative paths resolve.

## Coding Style & Naming Conventions
Follow PEP 8 with 4-space indentation and descriptive type-hinted function signatures. Use snake_case for modules, functions, and JSON keys; PascalCase for classes such as new scrapers. Reuse logging via `logging.getLogger(__name__)` and keep side effects behind `if __name__ == "__main__":`. Output files should follow `healthcare_newsletter_YYYYMMDD.md` or `stats_YYYYMMDD.json`.

## Testing Guidelines
Security hardening is enforced through `security_test.py`; extend it whenever you add validation logic. For new scraping features, pair unit coverage with a `python scheduler.py --test` run and confirm artifacts land in `newsletters/`. Use `.env.example` as the baseline for test credentials, and avoid committing modified `.env` files. Name ad-hoc checks `*_test.py` so they run cleanly from the project root.

## Commit & Pull Request Guidelines
Current history uses concise imperative subjects (e.g., “Initial commit: Healthcare Newsletter Generator”); keep subjects under 72 characters and expand details in the body. Reference related issues, note config or data migrations, and include sample output paths when relevant. Pull requests should describe scope, list validation commands, attach any generated newsletter snippets, and flag security-affecting changes explicitly.

## Security & Configuration Tips
Store secrets only in `.env`; copy from `.env.example` and never commit personalized credentials. Validate new source URLs with `SecurityValidator.validate_url` and document any required headers. If you introduce external writes, route them through `SecureFileHandler` so path traversal protections apply. Review `logs/` regularly and trim sensitive data before sharing diagnostic output.
