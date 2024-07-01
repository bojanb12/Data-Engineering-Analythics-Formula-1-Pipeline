from airflow import DAG
from airflow.decorators import task
from airflow.providers.postgres.hooks.postgres import PostgresHook
from airflow.sensors.external_task_sensor import ExternalTaskSensor
from datetime import datetime, timedelta

default_args = {
    
    'start_date': datetime(2024, 5, 27),
    'retries': 3,
    'retry_delay': timedelta(minutes=5),
}

with DAG(

    'f1_data_create_database_views',
    default_args=default_args,
    schedule_interval='@weekly',
    description='A DAG to create views in the database.',
    catchup=False

) as dag:

    # task for kafka consume and load DAG dependancy
    # we have to make sure that the database is already created and filled in order to create and update views 
    wait_for_kafka_consumeAndLoad_dag = ExternalTaskSensor(
        
        task_id='wait_for_kafka_consumeAndLoad_dag',
        external_dag_id='f1_data_pipeline_kafka_consumeAndLoad',
        external_task_id='consume_and_load_raceResultsFact',
        start_date=datetime(2024, 5, 27),
        mode='poke',
        poke_interval=30,  # interval between each poke
        timeout=24 * 60 * 60  # timeout in seconds (set to 24 hours here)
    )

    @task
    def read_sql_file():
    
        sql_path = '/opt/airflow/sql/DB_views.sql'
        
        with open(sql_path, 'r') as file:
        
            sql_script = file.read()
        
        return sql_script

    @task 
    def execute_sql(sql_script: str):

        hook = PostgresHook(postgres_conn_id='sourcedb_connection')
        hook.run(sql_script)



    sql_script = read_sql_file()

    execute_sql_task = execute_sql(sql_script)

    #sql_script >> execute_sql_task

    wait_for_kafka_consumeAndLoad_dag >> sql_script >> execute_sql_task