# Docker Guide for SSG

## Dockerfile

The project includes a production-ready Dockerfile for containerized builds.

## Building the Image

```bash
docker build -t ssg:latest .
```

## Usage Examples

### 1. Build a Site

Mount your site directory and build:

```bash
docker run -v $(pwd)/mysite:/site ssg:latest
```

### 2. Interactive Mode

Run SSG commands interactively:

```bash
docker run -it -v $(pwd)/mysite:/site ssg:latest ssg build
```

### 3. Initialize a New Site

```bash
docker run -v $(pwd):/output ssg:latest sh -c "ssg init mysite && cp -r mysite /output/"
```

### 4. Development Server

Run the development server:

```bash
docker run -it -p 8000:8000 -v $(pwd)/mysite:/site ssg:latest ssg serve --port 8000
```

## Docker Compose

Create `docker-compose.yml`:

```yaml
version: '3.8'

services:
  ssg:
    build: .
    volumes:
      - ./mysite:/site
      - ./dist:/site/dist
    command: ssg build
    
  ssg-dev:
    build: .
    ports:
      - "8000:8000"
    volumes:
      - ./mysite:/site
    command: ssg serve --port 8000
```

Run with:
```bash
docker-compose up ssg        # Build site
docker-compose up ssg-dev    # Development server
```

## Image Details

- **Base**: python:3.11-slim
- **Size**: ~200MB
- **Python**: 3.11+
- **Working Directory**: /site
- **Default Command**: `ssg build`

## Environment Variables

Set custom config:
```bash
docker run -e SSG_CONFIG=/site/custom.yaml -v $(pwd)/mysite:/site ssg:latest
```

## Multi-Stage Build (Optional)

For smaller production images, use multi-stage:

```dockerfile
FROM python:3.11-slim as builder
WORKDIR /app
COPY . .
RUN pip install --no-cache-dir -e .

FROM python:3.11-slim
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin/ssg /usr/local/bin/ssg
WORKDIR /site
CMD ["ssg", "build"]
```

## Troubleshooting

### Permission Issues

Run as current user:
```bash
docker run -u $(id -u):$(id -g) -v $(pwd)/mysite:/site ssg:latest
```

### Volume Mounting

Ensure absolute paths:
```bash
docker run -v /absolute/path/to/site:/site ssg:latest
```

## CI/CD Integration

### GitHub Actions

```yaml
- name: Build with Docker
  run: |
    docker build -t ssg .
    docker run -v ${{ github.workspace }}/site:/site ssg
```

### GitLab CI

```yaml
build:
  image: docker:latest
  services:
    - docker:dind
  script:
    - docker build -t ssg .
    - docker run -v $(pwd)/site:/site ssg
```

## Production Deployment

Build and deploy:
```bash
# Build image
docker build -t myregistry/ssg:1.0 .

# Push to registry
docker push myregistry/ssg:1.0

# Deploy
docker run -v /var/www/site:/site myregistry/ssg:1.0
```

## Verified and Production-Ready ✅

The Dockerfile is tested and ready for use!
