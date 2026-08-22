# SSG — Python static site generator CLI

`ssg` is a **command-line tool** (importable library package `ssg/`) that builds static sites from Markdown and Jinja2 templates. It is not an infrastructure or deployment product.

## Repository Classification

- **PROJECT_TYPE:** `cli-tool` (see root `PROJECT_TYPE` and [docs/PROJECT_CLASSIFICATION.md](docs/PROJECT_CLASSIFICATION.md))
- **Language:** Python 3.11+
- **IaC:** none by design (no Terraform, Kubernetes, Helm, Ansible, or Pulumi)
- **Containers:** optional local sandbox only; `docker compose up --build` runs the CLI in isolation with **no databases**

## Clone → install toolchain → test

```bash
git clone https://github.com/a-micable/SSG_.git
cd SSG_
python3.11 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install -e .
make test
```

Expected pass line (pytest): all tests collected **passed**, for example `XX passed in Ys`. `make test` exits 0 only if the full suite is green. CI jobs `test`, `lint`, `typecheck`, and `coverage` run the same entrypoints (`make test`, `pytest -q`, `ruff`, `mypy`, coverage fail-under 70).

## One-command sandbox (self-contained)

```bash
docker compose up --build
```

Builds the image, runs `ssg health`, `ssg init`, and `ssg build`, and checks that HTML, RSS, and sitemap files exist. Details: [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md).

## Install / run

```bash
ssg init mysite --name "My Site" --url http://localhost:8000
ssg build --config mysite/config.yml
ssg serve --config mysite/config.yml --no-watch
ssg health
ssg analyze --path . --format json
```

Visit http://localhost:8000 when using `serve`.

### Commands

- `ssg build` — parse Markdown, render templates, fingerprint assets, write RSS + sitemap
- `ssg init PATH` — scaffold `config.yml`, content, templates, assets
- `ssg serve` — local HTTP server (optional `--watch`)
- `ssg health` — JSON health, `logging_framework`, error_tracking, metrics
- `ssg analyze` — optional local-only repo scan (no network)

## Environment

Copy `.env.example`. Values are read with `getenv`:

| Variable | Used by |
| --- | --- |
| `SSG_LOG_LEVEL` | `ssg/logging_config.py` |
| `SSG_LOG_FORMAT` | `ssg/logging_config.py` |
| `SSG_OUTPUT_DIR` | `ssg/config.py` |
| `SSG_SERVE_PORT` | `ssg/cli.py` `serve` |

## Architecture

See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md). Pipeline: Markdown → parser → renderer → builder → `dist/`.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md). Changes go through review on a pull request; `main` is protected by CI (`test`, `lint`, `typecheck`, `coverage`). Land one feature or fix plus its tests and a `CHANGELOG.md` bullet in the same commit.

## Changelog

See [CHANGELOG.md](CHANGELOG.md).
