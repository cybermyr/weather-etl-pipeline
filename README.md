# Weather ETL Pipeline

An ETL pipeline that extracts weather data for multiple cities, transforms it, stores it in a MySQL database, and exposes it through a visualization dashboard. The pipeline runs on a fixed schedule and is fully containerized with Docker.

## Overview

The pipeline collects current weather conditions for 10 cities (Tunis, Rome, Paris, London, New York, Tokyo, Sydney, Moscow, Beijing, Rio de Janeiro) via the WeatherAPI, normalizes the response into a consistent schema, and persists it to MySQL. A Streamlit dashboard reads from the same database to display the latest readings.

## Architecture

```
WeatherAPI ──▶ extract.py ──▶ transform.py ──▶ db.py ──▶ MySQL
                                                            │
                                              dashboard.py ◀┘ (Streamlit)

scheduler.py runs main.py (extract → transform → load) every 45 minutes
```

The pipeline follows a standard ETL structure:

| Stage      | Module           | Responsibility                                    |
|----------- |------------------|---------------------------------------------------|
| Extract    | `extract.py`     | Calls the WeatherAPI for each city                |
| Transform  | `transform.py`   | Cleans and restructures the raw API response      |
| Load       | `db.py`          | Writes to MySQL, with upsert on duplicate entries |

Orchestration is handled by `main.py` (single execution) and `scheduler.py` (recurring execution).

## Project structure

```
.
├── extract.py            extracts data from the WeatherAPI
├── transform.py          cleans and structures the raw data
├── db.py                 database connection, read/write operations
├── db.sql                schema definition
├── main.py               runs one full ETL cycle
├── scheduler.py          runs the pipeline on a 45-minute interval
├── dashboard.py          Streamlit dashboard
├── Dockerfile            image definition, shared by both runtime services
├── docker-compose.yml    service orchestration (database, scheduler, dashboard)
├── requirements.txt      Python dependencies
└── README.md
```

## Prerequisites

- Docker and Docker Compose
- A WeatherAPI key (free tier available at weatherapi.com)

Python 3.9+ is required only for running the project without Docker.

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

This starts three services:

| Service     | Role                                                    |
|-------------|---------------------------------------------------------|
| `mysql`     | Database, with data persisted in a named volume         |
| `scheduler` | Runs the ETL pipeline every 45 minutes                  | 
| `dashboard` | Streamlit app, served at `http://localhost:8501`        |

The `scheduler` and `dashboard` services share the same image; only the startup command differs, set in `docker-compose.yml`.

## Running without Docker

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

Set `DB_HOST=localhost` in `.env`, then initialize the database:

```bash
mysql -u root -p < db.sql
```

Run a single pipeline execution:

```bash
python main.py
```

Run on a schedule:

```bash
python scheduler.py
```

Launch the dashboard:

```bash
streamlit run dashboard.py
```

## Tech stack

| Component         | Technology                 |
|-------------------|----------------------------|
| Language          | Python                     |
| Data source       | WeatherAPI                 |
| Database          | MySQL                      |
| Visualization     | Streamlit, Plotly          |
| Scheduling        | `schedule`                 |
| Containerization  | Docker, Docker Compose     |

## Planned improvements

- Cloud deployment (Azure)
- Machine learning model for temperature forecasting
- Error handling and structured logging