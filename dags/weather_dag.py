"""
weather_dag.py

DAG Airflow qui orchestre le pipeline ETL météo :
extract (API) -> transform (nettoyage) -> load (MySQL)

Remplace scheduler.py : Airflow gère maintenant la planification,
les retries par tâche, et l'historique des exécutions via son UI.
"""
from datetime import datetime, timedelta

from airflow import DAG
from airflow.operators.python import PythonOperator

from extract import get_weather
from transform import transform_weather_data
from db import save_to_db

CITIES = [
    "Tunis", "Rome", "Paris", "London", "New York",
    "Tokyo", "Sydney", "Moscow", "Beijing", "Rio de Janeiro",
]

# Paramètres par défaut appliqués à toutes les tâches du DAG
default_args = {
    "owner": "myriam",
    "retries": 2,                       # si une tâche échoue, réessaie 2 fois
    "retry_delay": timedelta(minutes=5),  # attend 5 min entre chaque essai
}


def extract_all(**context):
    """Récupère les données brutes pour toutes les villes.

    Transmet le résultat à la tâche suivante via XCom (ti = task instance).
    """
    raw_results = {}
    for city in CITIES:
        raw_results[city] = get_weather(city)
    context["ti"].xcom_push(key="raw_data", value=raw_results)


def transform_all(**context):
    """Récupère les données brutes de la tâche précédente et les nettoie."""
    raw_results = context["ti"].xcom_pull(
        key="raw_data", task_ids="extract"
    )
    cleaned_results = {}
    for city, raw_data in raw_results.items():
        cleaned_results[city] = transform_weather_data(raw_data)
    context["ti"].xcom_push(key="cleaned_data", value=cleaned_results)


def load_all(**context):
    """Récupère les données nettoyées et les insère en base."""
    cleaned_results = context["ti"].xcom_pull(
        key="cleaned_data", task_ids="transform"
    )
    success_count = 0
    failure_count = 0
    for city, data in cleaned_results.items():
        if save_to_db(data):
            success_count += 1
        else:
            failure_count += 1
    print(f"Pipeline terminé : {success_count} succès, {failure_count} échec(s)")


with DAG(
    dag_id="weather_etl_pipeline",
    description="Pipeline ETL météo : extract -> transform -> load",
    default_args=default_args,
    schedule_interval="*/45 * * * *",   # toutes les 45 minutes, syntaxe cron
    start_date=datetime(2026, 1, 1),
    catchup=False,                       # ne pas rattraper les runs passés
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

    # Définit l'ordre d'exécution : extract -> transform -> load
    extract_task >> transform_task >> load_task