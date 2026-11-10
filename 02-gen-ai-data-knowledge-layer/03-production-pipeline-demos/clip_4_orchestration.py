from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta
import logging

# Import your custom functions
from your_pipeline import fetch_documents, clean_and_chunk, generate_embeddings, index_vectors, cleanup

default_args = {
    'owner': 'data_team',
    'depends_on_past': False,
    'start_date': datetime(2024, 1, 1),
    'email_on_failure': True,
    'email_on_retry': False,
    'retries': 3,
    'retry_delay': timedelta(minutes=5),
}

dag = DAG(
    'embedding_pipeline',
    default_args=default_args,
    description='End-to-end embedding generation pipeline',
    schedule_interval='@hourly',
    catchup=False
)

fetch_task = PythonOperator(
    task_id='fetch_documents',
    python_callable=fetch_documents,
    dag=dag
)

chunk_task = PythonOperator(
    task_id='clean_and_chunk',
    python_callable=clean_and_chunk,
    dag=dag
)

embed_task = PythonOperator(
    task_id='generate_embeddings',
    python_callable=generate_embeddings,
    dag=dag
)

index_task = PythonOperator(
    task_id='index_vectors',
    python_callable=index_vectors,
    dag=dag
)

cleanup_task = PythonOperator(
    task_id='cleanup',
    python_callable=cleanup,
    dag=dag
)

# Set dependencies
fetch_task >> chunk_task >> embed_task >> index_task >> cleanup_task