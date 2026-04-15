# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 🏗️ Architecture Overview

The project is a web application with a clear, modern, and modular structure built around the **FastHTML** framework.

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

## 💡 FastHTML Idioms and Patterns (Reference: zref/fastht-22.md)

When writing new routes or components, please adhere to the following patterns:

### Routing & HTTP Methods
*   **Decorators:** Use the `@rt()` decorator (or `app.route`) to define routes.
*   **Async:** Most routes involving I/O (database, network, file system) must be defined as `async def` functions.
*   **HTTP Verbs:** Use specialized handlers like `@rt("/path")` for GET, `@rt("/path")` for POST, etc., when the method is critical.

### Data Handling
*   **Form Submission:** Use `Form(hx_post="/path", ...)` in the form definition, and ensure the handler uses `request.form()` to validate and retrieve data.
*   **Database Interaction:** Use the MiniDataAPI pattern (`db.create(Model, pk='field')`) for defining models and interacting with the database.
*   **State/Context:** The `session` and `request` objects are primary tools for accessing user context and request metadata.

### Component Building
*   **FT Components:** Use the `fasthtml.common` components (e.g., `Div`, `H1`, `P`, `Form`) to build the page structure.
*   **Custom Components:** For reusable groups of tags, define a Python function and use `@dataclass` (if stateful) or simply return the `FT` object.

### Advanced Patterns
*   **Async & I/O:** Use `async/await` for all network-related operations.
*   **HTMX/SSE:** For dynamic partial updates, leverage `hx-` attributes. For streaming data, use `EventStream` and `AsyncGenerator`.
*   **Error Handling:** Always define `exception_handlers` (e.g., `{404: my_404_handler}`).
*   **Background Tasks:** Use `BackgroundTasks` (or `BackgroundMiddleware` if appropriate) for tasks that should run after the response is sent, but do not block the user.

## 📚 Local Documentation
*   The primary documentation source is managed by MkDocs, utilizing files in the `docs/` directory and configured by `mkdocs.yml`.
*   The root `README.md` provides a link to the live documentation site: `https://s66erge.github.io/entan-mkdocs/`.
