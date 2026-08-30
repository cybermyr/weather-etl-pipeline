
from datetime import datetime, timedelta, timezone

from airflow import DAG
from airflow.operators.python import PythonOperator

from db import save_to_db
from extract import get_weather
from models import WeatherReading
from transform import transform_weather_data

CITIES = [
    "Tunis", "Rome", "Paris", "London", "New York",
    "Tokyo", "Sydney", "Moscow", "Beijing", "Rio de Janeiro",
]


default_args = {
    "owner": "myriam",
    "retries": 2,                      
    "retry_delay": timedelta(minutes=5),  
}


def extract_all(**context):
    
    raw_results = {}
    for city in CITIES:
        raw_results[city] = get_weather(city)
    context["ti"].xcom_push(key="raw_data", value=raw_results)


def transform_all(**context):
   
    raw_results = context["ti"].xcom_pull(
        key="raw_data", task_ids="extract"
    )
    cleaned_results = {}
    for city, raw_data in raw_results.items():
        reading = transform_weather_data(raw_data)
        cleaned_results[city] = reading.model_dump() if reading is not None else None
    context["ti"].xcom_push(key="cleaned_data", value=cleaned_results)


def load_all(**context):
  
    cleaned_results = context["ti"].xcom_pull(
        key="cleaned_data", task_ids="transform"
    )
    success_count = 0
    failure_count = 0
    for data_dict in cleaned_results.values():
        data = WeatherReading(**data_dict) if data_dict is not None else None
        if save_to_db(data):
            success_count += 1
        else:
            failure_count += 1
    print(f"Pipeline finished: {success_count} succeeded, {failure_count} failed")


with DAG(
    dag_id="weather_etl_pipeline",
    description="Weather ETL pipeline: extract -> transform -> load",
    default_args=default_args,
    schedule_interval="*/45 * * * *",   # every 45 minutes, cron syntax
    start_date=datetime(2026, 1, 1, tzinfo=timezone.utc),
    catchup=False,                       
    tags=["weather", "etl"],
) as dag:

    extract_task = PythonOperator(
        task_id="extract",
        python_callable=extract_all,
    )

    transform_task = PythonOperator(
        task_id="transform",
        python_callable=transform_all,
    )

    load_task = PythonOperator(
        task_id="load",
        python_callable=load_all,
    )


    extract_task >> transform_task >> load_task