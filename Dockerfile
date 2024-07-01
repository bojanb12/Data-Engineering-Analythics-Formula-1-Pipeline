FROM apache/airflow:latest

RUN airflow db init

RUN pip install apache-airflow-providers-docker

RUN pip install kafka-python-ng

RUN airflow connections add sourcedb_connection \
    --conn-type postgres \
    --conn-host sourcedb \
    --conn-schema airflow \
    --conn-login airflow \
    --conn-password airflow \
    --conn-port 5432

CMD ["airflow", "webserver"]
