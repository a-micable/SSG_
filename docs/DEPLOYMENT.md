# Deployment

This project ships a **local binary / CLI**, not a hosted service.

## Local run (canonical)

```bash
python3.11 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install -e .
ssg init mysite --name Demo --url http://localhost:8000
ssg build --config mysite/config.yml
ssg serve --config mysite/config.yml --no-watch
```

## Optional Docker sandbox

Buyers and graders can run the CLI in isolation with **no databases**:

```bash
docker compose up --build
```

That command builds the image, runs `ssg health`, `ssg init`, and `ssg build`, then exits after verifying HTML/RSS/sitemap output.

Containers are **sandbox-only**. They are not Kubernetes, Terraform, or production IaC. There is no deploy stage.

## What is not here (by design)

- No Terraform / OpenTofu
- No Kubernetes / Helm
- No Ansible / Pulumi
- No `.devcontainer/`
- No required Postgres, Redis, or other backing services
