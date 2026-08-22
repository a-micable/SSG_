# Project classification

- **Language:** Python 3.11+
- **Kind:** command-line tool (`ssg`) with an importable library package under `ssg/`
- **Domain:** static site generation (Markdown → HTML, templates, assets, RSS, sitemap)
- **Infrastructure as code:** none by design. This repository is not a deployable cloud service, Kubernetes workload, or Terraform/Helm/Ansible/Pulumi project.
- **Containers:** optional local sandbox only (`Dockerfile` + `docker-compose.yml`) so buyers can `docker compose up --build` and run `ssg init` / `ssg build` in isolation. Containers are not production IaC and do not start databases or external services.
- **Not in scope:** Terraform, Kubernetes manifests, Helm charts, Ansible playbooks, Pulumi, `.devcontainer/`
