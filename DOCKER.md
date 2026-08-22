# Docker sandbox

This repository is a **CLI**. Use Compose only to run `ssg` in isolation:

```bash
docker compose up --build
```

No Postgres, Redis, or other backing services. See docs/DEPLOYMENT.md.
