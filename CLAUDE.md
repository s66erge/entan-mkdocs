# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 🏗️ Architecture Overview

The project is a web application with a clear, modern, and modular structure.

*   **Web Framework:** The application uses **fasthtml** for its web backend, providing type-safe and robust handling of web requests.
*   **Client Interactivity:** Frontend partial updates and dynamic interactions are managed using **htmx**, allowing for a highly reactive Single Page Application (SPA) feel without writing complex JavaScript.
*   **Cloud Storage:** File storage is handled via **MinIO S3 compatibility**, meaning any code interacting with file uploads/retrieval must use patterns compatible with S3 SDKs (e.g., `boto3` or dedicated MinIO libraries).
*   **Core Libraries:** The `libs/` directory is the primary location for reusable modules and core business logic.
*   **Entry Point:** The main execution logic is housed in `main.py`. Scripts like `upload_demo.py` and `countoken.py` provide functional examples or specific service integrations.
*   **Data:** The `data/` directory holds necessary static data, configuration datasets, or examples required by the application.
*   **Documentation:** Documentation is managed via `mkdocs.yml` and lives in the `docs/` directory, suggesting content written there should be reviewed for technical accuracy before publication.

## 🛠️ Development Workflow & Commands

### 1. Running the Application
The application is web-service oriented and containerized.
*   **Development Environment:** Use `docker-compose.dev.yml` to bring up all necessary services for local development.
*   **Running Code Locally:** For quick runs or testing specific scripts, the entry points (`main.py`, `upload_demo.py`) can be run directly.

### 2. Testing
The repository uses `pytest` for testing.
*   **Run All Tests:** Execute all tests located in the `tests/` directory using `pytest`.
*   **Run Single Test:** To focus on a specific test file or class, pass the path to the test file/class to the `pytest` command.

### 3. Linting and Formatting
*   Linting and formatting are usually managed by the development environment defined in `docker-compose.dev.yml` or by utilizing associated pre-commit hooks. If manual linting is required, investigate setup scripts related to `pyproject.toml`.

## 📚 Local Documentation
*   The primary documentation source is managed by MkDocs, utilizing files in the `docs/` directory and configured by `mkdocs.yml`.
*   The root `README.md` provides a link to the live documentation site: `https://s66erge.github.io/entan-mkdocs/`.