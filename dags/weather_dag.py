
from datetime import datetime, timedelta, timezone

from airflow import DAG
from airflow.operators.python import PythonOperator

from db import save_to_db
from extract import get_weather
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
        cleaned_results[city] = transform_weather_data(raw_data)
    context["ti"].xcom_push(key="cleaned_data", value=cleaned_results)


def load_all(**context):
    
    cleaned_results = context["ti"].xcom_pull(
        key="cleaned_data", task_ids="transform"
    )
    success_count = 0
    failure_count = 0
    for data in cleaned_results.values():
        if save_to_db(data):
            success_count += 1
        else:
            failure_count += 1
    print(f"Pipeline terminé : {success_count} succès, {failure_count} échec(s)")


with DAG(
    dag_id="weather_etl_pipeline",
    description="Pipeline ETL météo : extract -> transform -> load",
    default_args=default_args,
    schedule_interval="*/45 * * * *",   
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