# Architecture

`ssg` is a **Python CLI / library** static site generator. There is no production control plane and no IaC.

## Pipeline

```
Markdown + YAML frontmatter → parser → Jinja2 renderer → builder → dist/
                              ↘ assets (fingerprint) ↗
                              ↘ RSS feed + sitemap ↗
```

## logging_framework

- Module: `ssg/logging_config.py`
- Named constant: `LOGGING_FRAMEWORK = "ssg-structured"`
- Levels: DEBUG, INFO, WARNING, ERROR, CRITICAL
- Env: `SSG_LOG_LEVEL`, `SSG_LOG_FORMAT` (see `.env.example`)
- Default sink: stderr JSON lines (`StructuredFormatter`)

## error_tracking and metrics

- `ssg/error_tracking.py` — `ERROR_TRACKING_BACKEND = "ssg-inprocess"`
- `ssg/runtime_metrics.py` — `METRICS_BACKEND = "ssg-counters"`
- `ssg health` prints JSON combining health, logging_framework, error_tracking, and metrics

## input_validation / schema_validation

- `input_validation_argv`, `input_validation_port` in `ssg/validation.py`
- `schema_validation_config` used from `ConfigLoader.load`
- Failed validation is tracked and surfaces as CLI abort / `ConfigError`

## Modules

| Module | Role |
| --- | --- |
| `ssg.cli` | Click entrypoint (`build`, `init`, `serve`, `analyze`, `health`) |
| `ssg.config` | YAML load + getenv `SSG_OUTPUT_DIR` |
| `ssg.parser` | Markdown + frontmatter |
| `ssg.renderer` | Jinja2 |
| `ssg.builder` | Orchestration, pagination |
| `ssg.assets` | Copy + fingerprint |
| `ssg.feed` / `ssg.sitemap` | RSS 2.0 and XML sitemap |
| `ssg.watcher` | Dev rebuilds |
| `ssg.analyzer` | Optional local repo scan |

## Tests

Canonical suite: `make test` (pytest). Behavioral CLI tests live in `tests/test_build_roundtrip.py` and `tests/test_filter_diff.py`.
