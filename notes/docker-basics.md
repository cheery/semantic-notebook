# Docker Basics

Docker containers package applications with their dependencies for consistent deployment.

Essential commands:
- `docker build -t myapp .` — build an image
- `docker run -p 8080:80 myapp` — run a container
- `docker compose up` — start multi-container apps

Dockerfile best practices: use multi-stage builds, minimize layers, don't run as root.
