# SBNote - Scrap Binding Notebook

A self-hosted, database-less note-taking web app that utilises a flat folder of markdown files for storage. SBNote is a fork of [flatnote](https://github.com/Dullage/flatnote) with enhanced features for organizing content through tags and scraps.

## Table of Contents

- [Features](#features)
- [File Structure](#file-structure)
- [Design Principle](#design-principle)
- [Getting Started](#getting-started)
- [Configuration](#configuration)
- [Development](#development)
- [Deployment](#deployment)
- [Acknowledgments](#acknowledgments)

## Features

### Enhanced Features

Building upon flatnote's foundation, SBNote introduces a unique organizational system inspired by Japanese illustrator Noritake's "SBN - Super Binding Notebook" concept:

* **Tag-based Scrap Organization**: Tags serve as a way to group scraps (fragments) of content, which can then be bound together to form notebooks.
* **Scrap-to-Notebook Workflow**: Create individual scraps with tags, then organize them into cohesive notebooks based on your tagging system.
* **Flexible Content Addition**: Like the physical SBN where you can add any paper by folding it in half, SBNote allows you to freely add and organize content without rigid rules.

## File Structure

SBNote organizes files in the following structure within the `SBNOTE_PATH` directory:
- `notes/` - Contains all markdown files
- `files/` - Contains uploaded attachments
- `index/` - Contains search index files

## Design Principle

SBNote is designed to be a distraction-free note-taking app that emphasizes content organization through a unique scrap-based workflow. This means:

* A clean and simple user interface that focuses on content creation and organization.
* A flexible system where you can create individual scraps (fragments) of content and organize them through tags.
* Tags serve as the primary organizational tool, allowing you to group related scraps and bind them into cohesive notebooks.
* Quick access to a full-text search from anywhere in the app (keyboard shortcut "/").

Another key design principle is not to take your notes hostage. Your notes are just markdown files. There's no database, proprietary formatting, complicated folder structures or anything like that. You're free at any point to just move the files elsewhere and use another app.

Equally, the only thing SBNote caches is the search index and that's incrementally synced on every search (and when SBNote first starts). This means that you're free to add, edit & delete the markdown files outside of SBNote even whilst SBNote is running.

## Getting Started

### Prerequisites

- Docker and Docker Compose installed
- Git (for deployment)

### Quick Start

1. **Clone the repository**
   ```bash
   git clone https://github.com/your-username/sbnote.git
   cd sbnote
   ```

2. **Create environment file**
   ```bash
   cp .env.example .env
   # Edit .env with your settings
   ```

3. **Start the application**
   ```bash
   docker-compose up -d
   ```

4. **Access the application**
   Open http://localhost:50010 in your browser

## Configuration

### Environment Variables

Create a `.env` file in your project directory by copying the example:

```bash
cp .env.example .env
```

Then edit the `.env` file with your settings:

```bash
# Authentication
SBNOTE_AUTH_TYPE=password
SBNOTE_USERNAME=admin
SBNOTE_PASSWORD=your-secure-password
SBNOTE_SECRET_KEY=your-secret-key

# Application Settings
SBNOTE_PORT=3000
SBNOTE_SESSION_EXPIRY_DAYS=30
SBNOTE_QUICK_ACCESS_HIDE=false
SBNOTE_QUICK_ACCESS_LIMIT=12
```

### Authentication Types

- `none`: No authentication required
- `read_only`: Read-only mode, no authentication
- `password`: Username/password authentication
- `totp`: Two-factor authentication (requires additional setup)

## Development

### Development Environment Setup

For development, the project includes a `docker-compose.override.yml` file that automatically applies development-specific settings:

- **Port**: 3000 (instead of 50010)
- **Session expiry**: 7 days (instead of 30)
- **Quick access**: Enabled with 12 items

### Development Workflow

1. **Setup development environment**
   ```bash
   cp .env.example .env
   # Edit .env with development settings
   ```

2. **Start development server**
   ```bash
   docker-compose up -d
   # Application will be available at http://localhost:3000
   ```

3. **View logs**
   ```bash
   docker-compose logs -f
   ```

4. **Stop development server**
   ```bash
   docker-compose down
   ```

### Environment File Priority

Docker Compose loads environment variables in this order:
1. System environment variables
2. `.env` file (in project root)
3. `docker-compose.override.yml` (development overrides)

## Deployment

### Docker Compose (Recommended)

```yaml
services:
  sbnote:
    container_name: sbnote
    image: yamnor/sbnote:latest
    platform: linux/amd64
    environment:
      PUID: 1000
      PGID: 1000
      SBNOTE_AUTH_TYPE: ${SBNOTE_AUTH_TYPE}
      SBNOTE_USERNAME: ${SBNOTE_USERNAME}
      SBNOTE_PASSWORD: ${SBNOTE_PASSWORD}
      SBNOTE_SECRET_KEY: ${SBNOTE_SECRET_KEY}
    volumes:
      - "./data:/data"
    ports:
      - "${SBNOTE_PORT:-50010}:8080"
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8080/health"]
      interval: 30s
      timeout: 10s
      retries: 3
```

### Docker Run Command

```shell
docker run -d \
  --env-file .env \
  -e "PUID=1000" \
  -e "PGID=1000" \
  -v "$(pwd)/data:/data" \
  -p "50010:8080" \
  yamnor/sbnote:latest
```

### Automated Deployment with GitHub Actions

This project includes automated deployment using GitHub Actions. When you push to the `main` branch, it will:

1. Build a Docker image for linux/amd64 platform
2. Push the image to Docker Hub
3. Deploy to your remote server
4. Perform health checks

#### Required GitHub Secrets

Set up the following secrets in your GitHub repository:

- `SSH_PRIVATE_KEY`: SSH private key for server access
- `DOCKERHUB_USERNAME`: Your Docker Hub username
- `DOCKERHUB_TOKEN`: Your Docker Hub access token
- `SBNOTE_USERNAME`: Application username
- `SBNOTE_PASSWORD`: Application password
- `SBNOTE_SECRET_KEY`: JWT secret key

## Acknowledgments

SBNote is a fork of [flatnote](https://github.com/Dullage/flatnote) by Dullage. The enhanced tag-based organization system is inspired by Japanese illustrator Noritake's "SBN - Super Binding Notebook" concept - a simple yet powerful idea of binding papers together to create notebooks without rigid rules, allowing for flexible content organization.

## Thanks

A special thanks to the fantastic open-source projects that make SBNote possible.

* [flatnote](https://github.com/Dullage/flatnote) - The original note-taking app that SBNote is based on.
* [Whoosh](https://whoosh.readthedocs.io/en/latest/intro.html) - A fast, pure Python search engine library.
* [TOAST UI Editor](https://ui.toast.com/tui-editor) - A GFM Markdown and WYSIWYG editor for the browser.
