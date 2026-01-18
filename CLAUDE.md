# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

A Dash web application that visualizes Trump action approval poll data from FiveThirtyEight. The app displays polling trends over time with category filtering and color-coded net approval ratings.

## Development Commands

```bash
# Install dependencies
pip install -r requirements.txt

# Run locally (development mode with debug)
DEBUG=True python app.py

# Run with gunicorn (production-like)
gunicorn wsgi:wsgi_app --bind 0.0.0.0:8080

# Run with custom path prefix (for reverse proxy)
APP_PATH=polls python app.py
```

## Architecture

- **app.py**: Main Dash application containing all logic
  - Loads poll data from CSV hosted on GitHub
  - Parses date ranges and aggregates data by category
  - Two callbacks: `update_graph` (trend chart) and `update_questions_table` (detail table)
  - Uses `get_net_color()` for conditional cell coloring based on net approval
- **wsgi.py**: WSGI entry point exposing `app.server` for gunicorn
- **Dockerfile**: Python 3.13-slim container configured for Railway deployment

## Environment Variables

- `DEBUG`: Enables debug mode and serves Dash assets locally (default: False)
- `APP_PATH`: Optional URL path prefix for reverse proxy setups
- `PORT`: Used by gunicorn in Docker (set by Railway)
