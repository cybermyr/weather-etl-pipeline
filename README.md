# Weather ETL Pipeline

An ETL pipeline that extracts current weather data for multiple cities, cleans it, stores it in a historized MySQL database, and exposes it through an interactive dashboard. Orchestration is handled by Apache Airflow, and the whole stack is containerized with Docker.

## Overview

The pipeline collects current weather conditions for 10 cities (Tunis, Rome, Paris, London, New York, Tokyo, Sydney, Moscow, Beijing, Rio de Janeiro) via WeatherAPI, normalizes each response into a consistent schema, and inserts it into MySQL — every run adds a new reading per city (historized model), which makes it possible to track how the data evolves over time. A Streamlit dashboard reads from this database to display both the current state and the historical trend for each city.

## Architecture

```
WeatherAPI ──▶ extract.py ──▶ transform.py ──▶ db.py ──▶ MySQL
                                                            │
                                              dashboard.py ◀┘ (Streamlit)

Apache Airflow orchestrates the extract → transform → load cycle
every 45 minutes (DAG: weather_etl_pipeline)
```

The pipeline follows a standard ETL structure, with a strict separation of responsibilities between each stage:

| Stage      | Module           | Responsibility                                                  |
|----------- |------------------|-------------------------------------------------------------------|
| Extract    | `extract.py`     | Calls WeatherAPI for each city, handles timeouts/HTTP errors      |
| Transform  | `transform.py`   | Cleans and restructures the raw response into a stable schema     |
| Load       | `db.py`          | Writes to MySQL, connection handled via a context manager         |

This separation makes each stage independently testable, maintainable, and debuggable.

## Orchestration with Apache Airflow

The pipeline was originally driven by a homemade scheduler (a `while True` loop with the `schedule` library). It has been replaced with **Apache Airflow**, which brings:

- **Automatic per-task retries**: if `extract` fails (e.g. an API timeout), Airflow automatically retries (2 attempts, 5-minute delay) before giving up.
- **Full execution history**, browsable in the web UI (status, duration, logs for every run).
- **Per-task granularity**: `extract`, `transform` and `load` are separate Airflow tasks (communicating via XCom) — a failed task can be retried on its own, without re-running the whole pipeline.
- **Visibility**: anyone can check the pipeline's health through the UI, without digging through raw logs.

The DAG (`dags/weather_dag.py`) is scheduled every 45 minutes (`*/45 * * * *`) and can also be triggered manually from the UI.

## Error handling and reliability

Every stage of the pipeline handles its own errors gracefully, without bringing down the whole run:

- **`extract.py`**: 10s timeout on every HTTP request, differentiated error handling (timeout / HTTP / network), returns `None` on failure instead of raising.
- **`transform.py`**: handles the case where `raw_data is None` (an upstream extraction failure) without crashing.
- **`db.py`**: database connections are managed via a context manager (`@contextmanager`), guaranteeing the connection is closed even on error; conditional SSL support for a future managed cloud database.
- **Structured logging** (the `logging` module, no `print()`) across the whole pipeline, with levels (INFO/WARNING/ERROR) and timestamps.
- A failure on one city does not stop the others from being processed.

## Data model: historization

Unlike an earlier version that overwrote each reading (`ON DUPLICATE KEY UPDATE`), the current schema **historizes** the data: every pipeline run adds a new row per city instead of overwriting the previous one. This enables:
- visualizing how the weather evolves over time on the dashboard,
- building a usable historical dataset for a future forecasting model.

## Project structure

```
.
├── dags/
│   └── weather_dag.py    Airflow orchestration (extract → transform → load)
├── extract.py             fetches data from WeatherAPI
├── transform.py           cleans and structures the raw data
├── db.py                  database connection, read/write operations
├── db.sql                 schema definition (historized model)
├── dashboard.py            Streamlit dashboard
├── Dockerfile              image shared by the dashboard service
├── docker-compose.yml      service orchestration (MySQL, Airflow, dashboard)
├── requirements.txt        Python dependencies
└── README.md
```

## Prerequisites

- Docker Desktop (with virtualization enabled in the BIOS/UEFI, and WSL2 on Windows)
- A WeatherAPI key (free tier available at weatherapi.com)

## Configuration

Create a `.env` file at the project root:

```env
API_KEY=your_weatherapi_key
DB_PASSWORD=your_db_password
DB_NAME=weather_db
```

## Running with Docker

```bash
docker compose up --build
```

This starts the following services:

| Service              | Role                                                          |
|----------------------|-----------------------------------------------------------------|
| `mysql`               | Database, with data persisted in a named volume                 |
| `airflow-db`           | Airflow's internal metadata database (Postgres)                   |
| `airflow-init`         | Initializes Airflow (tables + admin user), then exits             |
| `airflow-webserver`    | Airflow web UI                                                    |
| `airflow-scheduler`    | Triggers the DAG according to its schedule                        |
| `dashboard`             | Streamlit application                                             |

> Note: if a port conflicts with something already running locally (a local MySQL install, Oracle, etc.), adjust the exposed ports in `docker-compose.yml` (e.g. `3307:3306`, `8081:8080`).

## Accessing the interfaces

- **Dashboard**: http://localhost:8501
- **Airflow UI**: http://localhost:8081 (user `admin` / password `admin`)

## Tech stack

| Component         | Technology                 |
|-------------------|------------------------------|
| Language           | Python                       |
| Data source         | WeatherAPI                   |
| Database             | MySQL                        |
| Orchestration          | Apache Airflow                |
| Visualization           | Streamlit, Plotly              |
| Containerization          | Docker, Docker Compose          |

