from airflow import DAG
from airflow.providers.postgres.hooks.postgres import PostgresHook
from airflow.sensors.external_task_sensor import ExternalTaskSensor
from airflow.hooks.base_hook import BaseHook
from airflow.operators.python import task

from sqlalchemy import create_engine, MetaData, Table, select, func, and_
from sqlalchemy.orm import sessionmaker

import pandas as pd
from datetime import datetime
import json
from collections import deque

from kafka import KafkaConsumer
import time

# conection ID, for postgreSQL database connection      
postgres_conn_id = 'sourcedb_connection' 

# localhost server via which kafka borkers are available
kafka_bootstrap_servers = 'kafka:9092'

# -- Kafka topics --
kafka_topic_driver = 'f1_data_topic_driver'
kafka_topic_circuit = 'f1_data_topic_circuit'
kafka_topic_constructor = 'f1_data_topic_constructor'
kafka_topic_race = 'f1_data_topic_race'
kafka_topic_freePractice = 'f1_data_topic_race'
kafka_topic_laps = 'f1_data_topic_laps'
kafka_topic_pitStops = 'f1_data_topic_pitStops'
kafka_topic_raceStatus = 'f1_data_topic_raceStatus'
kafka_topic_driverStandings = 'f1_data_topic_driverStandings'
kafka_topic_constructorStandings = 'f1_data_topic_constructorStandings'
kafka_topic_raceResults = 'your_kafka_topic_raceResults'

# function for postgresql engine
def get_db_engine():
    connection = BaseHook.get_connection(postgres_conn_id)
    engine = create_engine(f'postgresql://{connection.login}:{connection.password}@{connection.host}:{connection.port}/{connection.schema}')
    return engine

with DAG(
    
    'f1_data_pipeline_kafka_consumeAndLoad',
    start_date=datetime(2024, 5, 27),
    schedule_interval='@weekly',
    catchup=False,
    
) as dag:

    # task for kafka fetch and publish DAG dependancy
    wait_for_publish_dag = ExternalTaskSensor(
        
        task_id='wait_for_publish_dag',
        external_dag_id='f1_data_pipeline_kafka_fetchAndPublish',
        external_task_id='fetch_and_publish_laps',
        start_date=datetime(2024, 5, 27),
        mode='poke',
        poke_interval=30,  
        timeout=10000
    )
    
    @task
    def consume_and_load_driverDim(table_name):
        
        # Kafka consumer to get the messages from the driver topic
        consumer = KafkaConsumer(kafka_topic_driver, bootstrap_servers=kafka_bootstrap_servers, auto_offset_reset='earliest', enable_auto_commit=True, group_id=None, value_deserializer=lambda x: json.loads(x.decode('utf-8')))
    
        postgres_hook = PostgresHook(postgres_conn_id=postgres_conn_id)
        engine = postgres_hook.get_sqlalchemy_engine()

        timeout = 10  
        last_message_time = time.time()
        
        total_drivers_loaded = 0

        while True:
            # Checking to see if there are new messages
            messages = consumer.poll(timeout_ms=1000)
            if not messages:
                # If there are no new messages, we wait awhile
                if time.time() - last_message_time > timeout:
                    break
                continue

            last_message_time = time.time()

            for topic_partition, msgs in messages.items():
                for message in msgs:
                
                    data = message.value

                    # Table structure from JSON response
                    drivers = data['MRData']['DriverTable']['Drivers']

                    # Because the response is a list we must convert it to dataframe
                    df = pd.DataFrame(drivers)
                    df.drop_duplicates(subset=['driverId'], inplace=True)
                    df['dob'] = pd.to_datetime(df['dateOfBirth']).dt.date

                    # Renaming everything to be aligned with our database schema
                    df.rename(columns={
                        'driverId': 'driverRef',
                        'givenName': 'forename',
                        'familyName': 'surname',
                        'permanentNumber': 'number'
                    }, inplace=True)

                    df['driverId'] = None  # placeholder for the primary key

                
                    with engine.connect() as connection:
                        for index, row in df.iterrows():
                        
                            if pd.isna(row['driverRef']):
                                result = None
                            else:
                                # we check if the driver is already in the database by comparing driverRef
                                result = connection.execute(f'SELECT "driverId" FROM "{table_name}" WHERE "driverRef" = %s', (row['driverRef'],)).fetchone()
                        
                            if result:
                                # if the driver exists, there is no need to update -> skip
                                continue
                            else:
                                # if the driver is new, we have to create a new driverId 
                                result = connection.execute(f'SELECT COALESCE(MAX("driverId"), 0) + 1 FROM "{table_name}"').fetchone()
                                row['driverId'] = result[0]
                        
                            # insert or update through sqlalchemy connection into the database
                                connection.execute(f"""
                                    INSERT INTO "{table_name}" ("driverId", "driverRef", "forename", "surname", "dob", "nationality", "code", "number", "url")
                                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                                """, (row['driverId'], row['driverRef'], row['forename'], row['surname'], row['dob'], row['nationality'], row['code'], row['number'], row['url']))
                                
                                total_drivers_loaded += 1

        consumer.close()
        
        print(f'Total number of new drivers added into the database: {total_drivers_loaded}')  # Log

    @task
    def consume_and_load_circuitDim(table_name):
        
        # Kafka consumer to get the messages from the driver topic
        consumer = KafkaConsumer(kafka_topic_circuit, bootstrap_servers=kafka_bootstrap_servers, auto_offset_reset='earliest', enable_auto_commit=True, group_id=None, value_deserializer=lambda x: json.loads(x.decode('utf-8')))

        # connction to the postgresql server by conn_id, the server starts from docker service
        postgres_hook = PostgresHook(postgres_conn_id=postgres_conn_id)
        engine = postgres_hook.get_sqlalchemy_engine()

        timeout = 10  
        last_message_time = time.time()
        
        total_circuits_loaded = 0

        while True:
            # Check for new Kafka messages
            messages = consumer.poll(timeout_ms=1000)
            if not messages:
                # If no messages, wait
                if time.time() - last_message_time > timeout:
                    break
                continue

            last_message_time = time.time()

            for topic_partition, msgs in messages.items():
                for message in msgs:
                    data = message.value

                    # Extract circuits from the API response
                    circuits = data['MRData']['CircuitTable']['Circuits']

                    # Process each circuit
                    for circuit in circuits:
                        circuit_ref = circuit['circuitId']  # Using circuitId as circuitRef in the database, this ensures consistency
                        circuit_name = circuit['circuitName']
                        url = circuit['url']
                        
                        # Extract location details because they are a sub object in the JSON response from the API
                        location = circuit.get('Location', {})
                        country = location.get('country')
                        locality = location.get('locality')
                        lat = float(location.get('lat', None)) if location.get('lat') else None
                        lng = float(location.get('long', None)) if location.get('long') else None
                        alt = None  # The value is missing in the API but it's available in the dataset, it can stay NULL because it is not of crucial importance

                        # Skip circuit if essential fields are missing
                        if not country or not locality:
                            continue

                        # Check if circuitRef (circuitId from API) already exists in the database
                        with engine.connect() as connection:
                            result = connection.execute(f'SELECT "circuitId" FROM "{table_name}" WHERE "circuitRef" = %s', (circuit_ref,)).fetchone()

                            if result:
                                continue  # If circuit exists, we skip it

                            # We insert new circuit into the database
                            result = connection.execute(f'SELECT COALESCE(MAX("circuitId"), 0) + 1 FROM "{table_name}"').fetchone()
                            new_circuit_id = result[0]

                            connection.execute(f"""
                                INSERT INTO "{table_name}" ("circuitId", "name_y", "circuitRef", "location", "country", "lat", "lng", "alt", "url_y")
                                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                            """, (new_circuit_id, circuit_name, circuit_ref, locality, country, lat, lng, alt, url))
                            
                            total_circuits_loaded += 1 #update load counter

        consumer.close()
        
        print(f'Total number of new circuits added into the database: {total_circuits_loaded}')  # Log
    
    @task
    def consume_and_load_constructorDim(table_name):
        
        # Kafka consumer to get the messages from the driver topic
        consumer = KafkaConsumer(kafka_topic_constructor, bootstrap_servers=kafka_bootstrap_servers, auto_offset_reset='earliest', enable_auto_commit=True, group_id=None, value_deserializer=lambda x: json.loads(x.decode('utf-8')))

        postgres_hook = PostgresHook(postgres_conn_id=postgres_conn_id)
        engine = postgres_hook.get_sqlalchemy_engine()

        timeout = 10  
        last_message_time = time.time()
        
        total_constructors_loaded = 0 # log counter

        while True:
            # Checking to see if there are new messages
            messages = consumer.poll(timeout_ms=1000)
            if not messages:
                # If there are no new messages, we wait
                if time.time() - last_message_time > timeout:
                    break
                continue

            last_message_time = time.time()

            for topic_partition, msgs in messages.items():
                for message in msgs:
                
                    data = message.value

                    # Table structure from JSON response
                    constructors = data['MRData']['ConstructorTable']['Constructors']

                    # Because the response is a list we must convert it to dataframe
                    df = pd.DataFrame(constructors)
                    df.drop_duplicates(subset=['constructorId'], inplace=True)
            
                    # Renaming everything to be aligned with our database schema
                    df.rename(columns={
                        'url': 'url_constructors',
                        'nationality': 'nationality_constructors',
                        'constructorId': 'constructorRef'
                    }, inplace=True)

                    df['constructorId'] = None  # placeholder for the primary key

                    with engine.connect() as connection:
                        for index, row in df.iterrows():
                        
                            if pd.isna(row['constructorRef']):
                                result = None
                            else:
                                # we check if the consturcor is already in the database by comparing driverRef
                                result = connection.execute(f'SELECT "constructorId" FROM "{table_name}" WHERE "constructorRef" = %s', (row['constructorRef'],)).fetchone()
                        
                            if result:
                                # if it already exists in our database, we skip; Maybe implement update here? Is that neccessary?
                                #row['constructorId'] = result[0]
                                continue
                            else:
                                # if it doesn't exist, we create a new primary key for that constructor (maximum existing key value + 1, to ensure integrity)
                                result = connection.execute(f'SELECT COALESCE(MAX("constructorId"), 0) + 1 FROM "{table_name}"').fetchone()
                                row['constructorId'] = result[0]
                        
                            # insert or update into the tabe via sqlachemy connection
                                connection.execute(f"""
                                    INSERT INTO "{table_name}" ("constructorId", "constructorRef", "name", "nationality_constructors", "url_constructors")
                                    VALUES (%s, %s, %s, %s, %s)
                                    ON CONFLICT ("constructorId") DO UPDATE SET
                                    "constructorRef" = EXCLUDED."constructorRef",
                                    "name" = EXCLUDED."name",
                                    "nationality_constructors" = EXCLUDED."nationality_constructors",
                                    "url_constructors" = EXCLUDED."url_constructors"
                                """, (row['constructorId'], row['constructorRef'], row['name'], row['nationality_constructors'], row['url_constructors']))
                                
                                total_constructors_loaded += 1 #update log counter

        consumer.close()
        
        print(f'Total number of new constructors added into the database: {total_constructors_loaded}')  # Log

    @task
    def consume_and_load_raceDim(table_name, dependant_table_name):
        
        consumer = KafkaConsumer(
        kafka_topic_race,
        bootstrap_servers=kafka_bootstrap_servers,
        auto_offset_reset='earliest',
        enable_auto_commit=True,
        group_id=None,
        value_deserializer=lambda x: json.loads(x.decode('utf-8'))
        )

        engine = get_db_engine()
        metadata = MetaData(bind=engine)
        session = sessionmaker(bind=engine)()

        # tables that are needed in order to ensure key integrity
        raceDim = Table(table_name, metadata, autoload_with=engine)
        circuitDim = Table(dependant_table_name, metadata, autoload_with=engine)
        

        timeout = 10  
        last_message_time = time.time()
        
        total_races_loaded = 0 # counter for log

        while True:
            # waiting for new kafka messages
            messages = consumer.poll(timeout_ms=1000)
            if not messages:
                if time.time() - last_message_time > timeout:
                    break
                continue

            last_message_time = time.time()

            for topic_partition, msgs in messages.items():
                for message in msgs:
                    data = message.value['MRData']['RaceTable']['Races']

                    for race in data:
                        race_date = race['date']
                        race_name = race['raceName']
                        circuit_ref = race['Circuit']['circuitId']

                        # Check if race already exists in the database
                        existing_race = session.execute(
                            select([raceDim.c.raceId]).where(raceDim.c.date == race_date)
                        ).fetchone()

                        if existing_race:
                            # If race exists, skip to next race
                            continue

                        # Fetch the circuit ID from the database
                        circuit_query = select([circuitDim.c.circuitId]).where(circuitDim.c.circuitRef == circuit_ref)
                        circuit_result = session.execute(circuit_query).fetchone()

                        if circuit_result:
                            circuit_id = circuit_result[0]
                        else:
                            # if the circuit is not in the database
                            continue

                        # create the new raceId
                        max_race_id_query = select([func.max(raceDim.c.raceId)])
                        max_race_id = session.execute(max_race_id_query).scalar() or 0
                        next_race_id = max_race_id + 1

                        # Insert new race into raceDim table
                        insert_stmt = raceDim.insert().values(
                            raceId=next_race_id,
                            circuitId=circuit_id,
                            name_x=race_name,
                            date=race_date,
                            year=race['season'],
                            round=race['round'],
                            time_races=race['time'] if 'time' in race else None,
                            url_x=race['url']
                        )

                        session.execute(insert_stmt)
                        session.commit()
                        total_races_loaded += 1 # update the log counter

        consumer.close()
        session.close()
        
        print(f'Total number of new races loaded into the database: {total_races_loaded}')  # Log
    
    @task
    def consume_and_load_freePracticeDim(table_name, dependant_table_name):
        
        consumer = KafkaConsumer(
            kafka_topic_freePractice,
            bootstrap_servers=kafka_bootstrap_servers,
            auto_offset_reset='earliest',
            enable_auto_commit=True,
            group_id=None,
            value_deserializer=lambda x: json.loads(x.decode('utf-8'))
        )

        engine = get_db_engine()
        metadata = MetaData(bind=engine)
        session = sessionmaker(bind=engine)()

        # tables that are needed in order to ensure key integrity
        freePracticeDim = Table(table_name, metadata, autoload_with=engine)
        raceDim = Table(dependant_table_name, metadata, autoload_with=engine)

        timeout = 10  
        last_message_time = time.time()
        total_freePractices_loaded = 0

        while True:
            # waiting for new kafka messages
            messages = consumer.poll(timeout_ms=1000)
            if not messages:
                if time.time() - last_message_time > timeout:
                    break
                continue

            last_message_time = time.time()

            for topic_partition, msgs in messages.items():
                for message in msgs:
                    data = message.value['MRData']['RaceTable']['Races']

                    for race in data:
                        race_date = race['date']

                        # Check if the race already exists in the database
                        existing_race = session.execute(
                            select([raceDim.c.raceId]).where(raceDim.c.date == race_date)
                        ).fetchone()

                        if not existing_race:
                            # If the race does not exist, skip to next race
                            continue

                        race_id = existing_race[0]

                        # Check if free practice data already exists in the database for this race
                        existing_free_practice = session.execute(
                            select([freePracticeDim.c.raceId]).where(freePracticeDim.c.raceId == race_id)
                        ).fetchone()

                        if existing_free_practice:
                            # If free practice data exists, skip to next race
                            continue

                        # Extract practice data if available
                        fp1_date = race['FirstPractice']['date'] if 'FirstPractice' in race else None
                        fp1_time = race['FirstPractice']['time'] if 'FirstPractice' in race else None
                        fp2_date = race['SecondPractice']['date'] if 'SecondPractice' in race else None
                        fp2_time = race['SecondPractice']['time'] if 'SecondPractice' in race else None
                        fp3_date = race['ThirdPractice']['date'] if 'ThirdPractice' in race else None
                        fp3_time = race['ThirdPractice']['time'] if 'ThirdPractice' in race else None

                        # Insert new free practice data into freePracticeDim table
                        insert_stmt = freePracticeDim.insert().values(
                            raceId=race_id,
                            fp1_date=fp1_date,
                            fp1_time=fp1_time,
                            fp2_date=fp2_date,
                            fp2_time=fp2_time,
                            fp3_date=fp3_date,
                            fp3_time=fp3_time
                        )

                        session.execute(insert_stmt)
                        session.commit()
                        total_freePractices_loaded += 1 # update the log counter

        consumer.close()
        session.close()
        
        print(f'Total number of free practices loaded into the database: {total_freePractices_loaded}')  # Log

    @task
    def consume_and_load_lapsDim(table_name, dependant_race_table, dependant_driver_table):
        
        consumer = KafkaConsumer(
            kafka_topic_laps,
            bootstrap_servers=kafka_bootstrap_servers,
            auto_offset_reset='earliest',
            enable_auto_commit=True,
            group_id=None,
            value_deserializer=lambda x: json.loads(x.decode('utf-8'))
        )

        engine = get_db_engine()
        metadata = MetaData(bind=engine)
        session = sessionmaker(bind=engine)()

        # Tables needed to ensure key integrity
        lapsDim = Table(table_name, metadata, autoload_with=engine)
        raceDim = Table(dependant_race_table, metadata, autoload_with=engine)
        driverDim = Table(dependant_driver_table, metadata, autoload_with=engine)

        timeout = 10
        last_message_time = time.time()
        
        total_laps_loaded = 0  # Initialize a counter for the number of laps loaded log

        while True:
            
            # Waiting for new Kafka messages
            messages = consumer.poll(timeout_ms=1000)
            if not messages:
                if time.time() - last_message_time > timeout:
                    break
                continue

            last_message_time = time.time()

            for topic_partition, msgs in messages.items():
                for message in msgs:
                    data = message.value['MRData']['RaceTable']['Races']

                    for race in data:
                        race_date = race['date']

                        # Fetch raceId from the database
                        race_query = select([raceDim.c.raceId]).where(raceDim.c.date == race_date)
                        race_result = session.execute(race_query).fetchone()

                        if not race_result:
                            # If the race is not in the database, skip
                            continue

                        race_id = race_result[0]

                        for lap in race['Laps']:
                            lap_number = lap['number']

                            for timing in lap['Timings']:
                                driver_ref = timing['driverId']

                                # Fetch driverId from the database, driverRef is the equivalent to driverId from the API
                                driver_query = select([driverDim.c.driverId]).where(driverDim.c.driverRef == driver_ref)
                                driver_result = session.execute(driver_query).fetchone()

                                if not driver_result:
                                    # we need the driver that made the lap, so if there is no driver with that ID -> skip
                                    continue

                                driver_id = driver_result[0]
                                lap_time = timing['time']
                                lap_position = timing['position']

                                # Check if the lap already exists in the database
                                lap_check_query = select([lapsDim.c.raceId]).where(and_(
                                    lapsDim.c.raceId == race_id,
                                    lapsDim.c.driverId == driver_id,
                                    lapsDim.c.lap == lap_number
                                ))
                                lap_check_result = session.execute(lap_check_query).fetchone()

                                if lap_check_result:
                                    # Lap already exists, skip
                                    continue

                                # Convert lap time to total milliseconds
                                minutes, seconds = lap_time.split(":")
                                total_milliseconds = int(minutes) * 60000 + int(float(seconds) * 1000)

                                # Insert new lap into lapsDim table
                                insert_stmt = lapsDim.insert().values(
                                    raceId=race_id,
                                    driverId=driver_id,
                                    lap=int(lap_number),
                                    time_laptimes=lap_time,
                                    milliseconds_laptimes=total_milliseconds,
                                    position_laptimes=int(lap_position)
                                )

                                session.execute(insert_stmt)
                                session.commit()
                                total_laps_loaded += 1 # update counter for log

        consumer.close()
        session.close()
        
        print(f'Total number of laps loaded into the database: {total_laps_loaded}')  # Log
    
    @task
    def consume_and_load_pitStopsDim(table_name, dependant_race_table, dependant_driver_table):
        
        consumer = KafkaConsumer(
            kafka_topic_pitStops,
            bootstrap_servers=kafka_bootstrap_servers,
            auto_offset_reset='earliest',
            enable_auto_commit=True,
            group_id=None,
            value_deserializer=lambda x: json.loads(x.decode('utf-8'))
        )

        engine = get_db_engine()
        metadata = MetaData(bind=engine)
        session = sessionmaker(bind=engine)()

        pitStopsDim = Table(table_name, metadata, autoload_with=engine)
        raceDim = Table(dependant_race_table, metadata, autoload_with=engine)
        driverDim = Table(dependant_driver_table, metadata, autoload_with=engine)

        timeout = 10
        last_message_time = time.time()
        
        total_pitStops_loaded = 0

        while True:
            messages = consumer.poll(timeout_ms=1000)
            if not messages:
                if time.time() - last_message_time > timeout:
                    break
                continue

            last_message_time = time.time()

            for topic_partition, msgs in messages.items():
                for message in msgs:
                    pit_stop_data = message.value
                    
                    print(f"Received Kafka message: {pit_stop_data}")

                    # Validate that all required keys are present
                    required_keys = ['season', 'round', 'driverId', 'stop', 'lap_pitstops', 'time_pitstops', 'duration']
                    if not all(key in pit_stop_data for key in required_keys):
                        # Log a warning and skip this message if keys are missing
                        print(f"Missing keys in message: {pit_stop_data}")
                        continue

                    season = pit_stop_data['season']
                    round_number = pit_stop_data['round']
                    driver_id = pit_stop_data['driverId']
                    stop_number = pit_stop_data['stop']
                    lap = pit_stop_data['lap_pitstops']
                    pit_stop_time = pit_stop_data['time_pitstops']
                    duration = pit_stop_data['duration']

                    # Fetch raceId from the database
                    race_query = select([raceDim.c.raceId]).where(and_(
                        raceDim.c.year == season,
                        raceDim.c.round == round_number
                    ))
                    race_result = session.execute(race_query).fetchone()

                    if not race_result:
                        # If the race is not in the database, skip
                        continue

                    race_id = race_result[0]

                    # Fetch driverId from the database
                    driver_query = select([driverDim.c.driverId]).where(driverDim.c.driverRef == driver_id)
                    driver_result = session.execute(driver_query).fetchone()

                    if not driver_result:
                        # If the driver is not in the database, skip
                        continue

                    driver_id = driver_result[0]

                    # Check if the pit stop already exists in the database
                    pit_stop_check_query = select([pitStopsDim.c.raceId]).where(and_(
                        pitStopsDim.c.raceId == race_id,
                        pitStopsDim.c.driverId == driver_id,
                        pitStopsDim.c.stop == stop_number
                    ))
                    pit_stop_check_result = session.execute(pit_stop_check_query).fetchone()

                    if pit_stop_check_result:
                        # Pit stop already exists, skip
                        continue

                    # Insert new pit stop into pitStopsDim table
                    insert_stmt = pitStopsDim.insert().values(
                        raceId=race_id,
                        driverId=driver_id,
                        stop=int(stop_number),
                        lap_pitstops=int(lap),
                        time_pitstops=pit_stop_time,
                        duration=duration
                    )

                    session.execute(insert_stmt)
                    session.commit()
                    total_pitStops_loaded += 1

        consumer.close()
        session.close()
        
        print(f'Total number of pit stops loaded into the database: {total_pitStops_loaded}')  # Log

    @task
    def consume_and_load_raceStatusDim(table_name):
        
        consumer = KafkaConsumer(
            kafka_topic_raceStatus,
            bootstrap_servers=kafka_bootstrap_servers,
            auto_offset_reset='earliest',
            enable_auto_commit=True,
            group_id=None,
            value_deserializer=lambda x: json.loads(x.decode('utf-8'))
        )
        
        engine = get_db_engine()
        metadata = MetaData(bind=engine)
        session = sessionmaker(bind=engine)()
        
        raceStatusDim = Table(table_name, metadata, autoload_with=engine)
        
        timeout = 10
        last_message_time = time.time()
        
        number_raceStatus_loaded = 0
        
        while True:
            messages = consumer.poll(timeout_ms=1000)
            if not messages:
                if time.time() - last_message_time > timeout:
                    break
                continue
            
            last_message_time = time.time()
            
            for topic_partition, msgs in messages.items():
                for message in msgs:
                    status_data = message.value
                    
                    status_id = int(status_data['statusId'])
                    status_description = status_data['status']
                    
                    # Check if status already exists in the database
                    existing_status = session.execute(
                        select([raceStatusDim.c.statusId]).where(raceStatusDim.c.status == status_description)
                    ).fetchone()
                    
                    if existing_status:
                        continue
                    
                    # Create new unique statusId
                    max_status_id_query = select([func.max(raceStatusDim.c.statusId)])
                    max_status_id = session.execute(max_status_id_query).scalar() or 0
                    next_status_id = max_status_id + 1
                    
                    # Insert new status into raceStatusDim table
                    insert_stmt = raceStatusDim.insert().values(
                        statusId=next_status_id,
                        status=status_description
                    )
                    
                    session.execute(insert_stmt)
                    session.commit()
                    number_raceStatus_loaded += 1
        
        consumer.close()
        session.close()
        
        print(f'Total number of new race statuses loaded into the database: {number_raceStatus_loaded}')  # Log

    @task
    def consume_and_load_driverStandingsDim(table_name, dependant_driver_table):
        
        consumer = KafkaConsumer(
            kafka_topic_driverStandings,
            bootstrap_servers=kafka_bootstrap_servers,
            auto_offset_reset='earliest',
            enable_auto_commit=True,
            group_id=None,
            value_deserializer=lambda x: json.loads(x.decode('utf-8'))
        )

        engine = get_db_engine()
        metadata = MetaData(bind=engine)
        session = sessionmaker(bind=engine)()

        # Tables needed to ensure key integrity
        driverStandingsDim = Table(table_name, metadata, autoload_with=engine)
        driverDim = Table(dependant_driver_table, metadata, autoload_with=engine)

        timeout = 10
        last_message_time = time.time()
        
        total_driver_standings_loaded = 0  # Initialize a counter for the number of driver standings loaded log

        while True:
            # Waiting for new Kafka messages
            messages = consumer.poll(timeout_ms=1000)
            if not messages:
                if time.time() - last_message_time > timeout:
                    break
                continue

            last_message_time = time.time()

            for topic_partition, msgs in messages.items():
                for message in msgs:
                    standings = message.value['MRData']['StandingsTable']['StandingsLists'][0]['DriverStandings']

                    for standing in standings:
                        driver_ref = standing['Driver']['driverId']

                        # Fetch driverId from the database, driverRef is the equivalent to driverId from the API
                        driver_query = select([driverDim.c.driverId]).where(driverDim.c.driverRef == driver_ref)
                        driver_result = session.execute(driver_query).fetchone()

                        if not driver_result:
                            # we need the driver for the standings, so if there is no driver with that ID -> skip
                            continue

                        driver_id = driver_result[0]
                        position = int(standing['position'])
                        points = float(standing['points'])
                        wins = int(standing['wins'])

                        # Generate a new driverStandingsId
                        new_driverStandingsId = session.execute(select([func.max(driverStandingsDim.c.driverStandingsId)])).scalar() + 1

                        # Insert new driver standings into driverStandingsDim table
                        insert_stmt = driverStandingsDim.insert().values(
                            driverStandingsId=new_driverStandingsId,
                            driverId=driver_id,
                            position_driverstandings=position,
                            points_driverstandings=points,
                            wins=wins
                        )

                        session.execute(insert_stmt)
                        session.commit()
                        total_driver_standings_loaded += 1  # update counter for log

        consumer.close()
        session.close()
        
        print(f'Total number of driver standings loaded into the database: {total_driver_standings_loaded}')  # Log
    
    @task
    def consume_and_load_constructorStandingsDim(table_name, dependant_constructor_table):
        
        consumer = KafkaConsumer(
            kafka_topic_constructorStandings,
            bootstrap_servers=kafka_bootstrap_servers,
            auto_offset_reset='earliest',
            enable_auto_commit=True,
            group_id=None,
            value_deserializer=lambda x: json.loads(x.decode('utf-8'))
        )

        engine = get_db_engine()
        metadata = MetaData(bind=engine)
        session = sessionmaker(bind=engine)()

        # Tables needed to ensure key integrity
        constructorStandingsDim = Table(table_name, metadata, autoload_with=engine)
        constructorDim = Table(dependant_constructor_table, metadata, autoload_with=engine)

        timeout = 10
        last_message_time = time.time()
        
        total_constructor_standings_loaded = 0  # Initialize a counter for the number of constructor standings loaded log

        while True:
            # Waiting for new Kafka messages
            messages = consumer.poll(timeout_ms=1000)
            if not messages:
                if time.time() - last_message_time > timeout:
                    break
                continue

            last_message_time = time.time()

            for topic_partition, msgs in messages.items():
                for message in msgs:
                    standings = message.value['MRData']['StandingsTable']['StandingsLists'][0]['ConstructorStandings']

                    for standing in standings:
                        constructor_ref = standing['Constructor']['constructorId']

                        # Fetch constructorId from the database, constructorRef is the equivalent to constructorId from the API
                        constructor_query = select([constructorDim.c.constructorId]).where(constructorDim.c.constructorRef == constructor_ref)
                        constructor_result = session.execute(constructor_query).fetchone()

                        if not constructor_result:
                            # We need the constructor for the standings, so if there is no constructor with that ID -> skip
                            continue

                        constructor_id = constructor_result[0]
                        position = int(standing['position'])
                        points = float(standing['points'])
                        wins = int(standing['wins'])

                        # Check for duplicate
                        duplicate_check_query = select([constructorStandingsDim.c.constructorStandingsId]).where(
                            and_(
                                constructorStandingsDim.c.constructorId == constructor_id,
                                constructorStandingsDim.c.position_constructorstandings == position,
                                constructorStandingsDim.c.points_constructorstandings == points,
                                constructorStandingsDim.c.wins_constructorstandings == wins
                            )
                        )
                        duplicate_result = session.execute(duplicate_check_query).fetchone()

                        if duplicate_result:
                            # Duplicate found, skip insertion
                            continue

                        # Generate a new constructorStandingsId
                        new_constructorStandingsId = session.execute(select([func.max(constructorStandingsDim.c.constructorStandingsId)])).scalar() + 1

                        # Insert new constructor standings into constructorStandingsDim table
                        insert_stmt = constructorStandingsDim.insert().values(
                            constructorStandingsId=new_constructorStandingsId,
                            constructorId=constructor_id,
                            position_constructorstandings=position,
                            points_constructorstandings=points,
                            wins_constructorstandings=wins
                        )

                        session.execute(insert_stmt)
                        session.commit()
                        total_constructor_standings_loaded += 1  # update counter for log

        consumer.close()
        session.close()
        
        print(f'Total number of constructor standings loaded into the database: {total_constructor_standings_loaded}')  # Log

    @task
    def consume_and_load_raceResultsFact(table_name):

        consumer = KafkaConsumer(
            kafka_topic_raceResults,
            bootstrap_servers=kafka_bootstrap_servers,
            auto_offset_reset='earliest',
            enable_auto_commit=True,
            group_id=None,
            value_deserializer=lambda x: json.loads(x.decode('utf-8'))
        )

        engine = get_db_engine()
        metadata = MetaData(bind=engine)
        session = sessionmaker(bind=engine)()

        # Tables needed for foreign key dependencies
        raceResultsFact = Table(table_name, metadata, autoload_with=engine)
        raceStatusDim = Table("raceStatusDim", metadata, autoload_with=engine)
        raceDim = Table("raceDim", metadata, autoload_with=engine)
        driverDim = Table("driverDim", metadata, autoload_with=engine)
        constructorDim = Table("constructorDim", metadata, autoload_with=engine)
        constructorStandingsDim = Table("constructorStandingsDim", metadata, autoload_with=engine)
        driverStandingsDim = Table("driverStandingsDim", metadata, autoload_with=engine)

        timeout = 10
        number_race_results_loaded = 0

        start_time = time.time()
        while True:
            message = consumer.poll(timeout_ms=1000, max_records=1)
            
            if not message:
                print("No new messages received. Ending task.")
                break
            
            for tp, messages in message.items():
                for msg in messages:
                    race_result_data = msg.value
                    
                    # To ensure 'round' exists in race_result_data
                    if 'round' not in race_result_data:
                        print(f"Skipping message: 'round' key not found in Kafka message.")
                        continue
                    
                    round_number = int(race_result_data['round'])
                    race_date = race_result_data.get('date')  # Fetch the date from Kafka message
                    
                    # Fetch raceId from database based on round and date
                    race_query = select([raceDim.c.raceId]).where(
                        (raceDim.c.round == round_number) &
                        (raceDim.c.date == race_date)
                    )
                    result = session.execute(race_query).fetchone()
                    
                    if not result:
                        print(f"No race found for round {round_number} and date {race_date}. Skipping message.")
                        continue
                    
                    raceId = result[0]
                    
                    constructorRef_api = race_result_data['constructorId']
                    driverRef_api = race_result_data['driverId']
                    status_description = race_result_data['statusId']  # Assuming this is the status description from Kafka
                    positionOrder = int(race_result_data['positionOrder'])
                    points = float(race_result_data['points'])
                    laps = int(race_result_data['laps'])
                    grid = int(race_result_data['grid'])
                    fastestLapTime = race_result_data['fastestLapTime']
                    
                    # Handle fastestLapSpeed, it might be None
                    fastestLapSpeed = float(race_result_data['fastestLapSpeed']) if race_result_data['fastestLapSpeed'] is not None else None
                    
                    race_time = race_result_data['time']
                    
                    # Handle fastestLap, it might be None
                    fastestLap = int(race_result_data['fastestLap']) if race_result_data['fastestLap'] is not None else None
                    
                    # Query raceStatusDim to get statusId
                    status_query = select([raceStatusDim.c.statusId]).where(raceStatusDim.c.status == status_description)
                    result = session.execute(status_query).fetchone()
                    
                    if result:
                        statusId = result[0]
                    else:
                        print(f"Invalid statusId value '{status_description}' for raceId {raceId}. Skipping.")
                        continue
                    
                    # Fetch constructorId from database based on constructorRef from the API
                    constructor_query = select([constructorDim.c.constructorId]).where(
                        constructorDim.c.constructorRef == constructorRef_api
                    )
                    result = session.execute(constructor_query).fetchone()
                    
                    if not result:
                        print(f"No constructor found for constructorRef {constructorRef_api}. Skipping message.")
                        continue
                    
                    constructorId = result[0]
                    
                    # Fetch driverId from database based on driverRef_api
                    driver_query = select([driverDim.c.driverId]).where(
                        driverDim.c.driverRef == driverRef_api
                    )
                    result = session.execute(driver_query).fetchone()
                    
                    if not result:
                        print(f"No driver found for driverRef {driverRef_api}. Skipping message.")
                        continue
                    
                    driverId = result[0]
                    
                    # Fetch constructorStandingsId and driverStandingsId based on constructorId and driverId
                    constructor_standings_query = select([constructorStandingsDim.c.constructorStandingsId]).where(
                        constructorStandingsDim.c.constructorId == constructorId
                    )
                    result = session.execute(constructor_standings_query).fetchone()
                    
                    if result:
                        constructorStandingsId = result[0]
                    else:
                        print(f"No constructor standings found for constructorId {constructorId}. Skipping message.")
                        continue
                    
                    driver_standings_query = select([driverStandingsDim.c.driverStandingsId]).where(
                        driverStandingsDim.c.driverId == driverId
                    )
                    result = session.execute(driver_standings_query).fetchone()
                    
                    if result:
                        driverStandingsId = result[0]
                    else:
                        print(f"No driver standings found for driverId {driverId}. Skipping message.")
                        continue
                    
                    # Generate new resultId
                    max_result_id_query = select([func.max(raceResultsFact.c.resultId)])
                    max_result_id = session.execute(max_result_id_query).scalar()
                    new_result_id = max_result_id + 1 if max_result_id else 1
                    
                    # Insert into raceResultsFact table
                    insert_stmt = raceResultsFact.insert().values(
                        resultId=new_result_id,
                        raceId=raceId,
                        constructorId=constructorId,
                        driverId=driverId,
                        constructorStandingsId=constructorStandingsId,
                        driverStandingsId=driverStandingsId,
                        statusId=statusId,
                        positionOrder=positionOrder,
                        points=points,
                        laps=laps,
                        grid=grid,
                        fastestLapTime=fastestLapTime,
                        fastestLapSpeed=fastestLapSpeed,
                        time=race_time,
                        fastestLap=fastestLap
                    )
                    
                    session.execute(insert_stmt)
                    session.commit()
                    number_race_results_loaded += 1
            
            # Break the loop if no new messages are received for the specified timeout period
            if time.time() - start_time > timeout:
                print("Timeout reached. Ending task.")
                break

        consumer.close()
        session.close()

        print(f"Total number of race results loaded into the database: {number_race_results_loaded}")



# -- CONSUME AND LOAD -- 
    consume_and_load_driver_task = consume_and_load_driverDim('driverDim')
    consume_and_load_circuit_task = consume_and_load_circuitDim('circuitDim')
    consume_and_load_constructor_task = consume_and_load_constructorDim('constructorDim')
    consume_and_load_race_task = consume_and_load_raceDim('raceDim', 'circuitDim')
    consume_and_load_freePracticeDim_task = consume_and_load_freePracticeDim('freePracticeDim', "raceDim")
    consume_and_load_lapsDim_task = consume_and_load_lapsDim('lapsDim', 'raceDim', 'driverDim')
    consume_and_load_pitStopsDim_task = consume_and_load_pitStopsDim('pitStopsDim', 'raceDim', 'driverDim')
    consume_and_load_raceStatusDim_task = consume_and_load_raceStatusDim('raceStatusDim')
    consume_and_load_driverStandingsDim_task = consume_and_load_driverStandingsDim('driverStandingsDim', 'driverDim')
    consume_and_load_constructorStandingsDim_task = consume_and_load_constructorStandingsDim('constructorStandingsDim', 'constructorDim')
    consume_and_load_raceResultsFact_task = consume_and_load_raceResultsFact('raceResultsFact')
    
    
# -- TASKFLOW --
    wait_for_publish_dag >> consume_and_load_raceStatusDim_task >> consume_and_load_raceResultsFact_task
    wait_for_publish_dag >> consume_and_load_constructor_task >> consume_and_load_raceResultsFact_task
    wait_for_publish_dag >> consume_and_load_circuit_task >> consume_and_load_race_task >> consume_and_load_freePracticeDim_task >> consume_and_load_raceResultsFact_task
    wait_for_publish_dag >> [consume_and_load_driver_task, consume_and_load_race_task, consume_and_load_raceStatusDim_task] >> consume_and_load_lapsDim_task >> consume_and_load_raceResultsFact_task
    wait_for_publish_dag >> [consume_and_load_driver_task, consume_and_load_race_task] >> consume_and_load_pitStopsDim_task >> consume_and_load_raceResultsFact_task
    wait_for_publish_dag >> [consume_and_load_driver_task, consume_and_load_race_task] >> consume_and_load_driverStandingsDim_task >> consume_and_load_raceResultsFact_task
    wait_for_publish_dag >> consume_and_load_constructor_task >> consume_and_load_constructorStandingsDim_task >> consume_and_load_raceResultsFact_task

    
    # for testing, no dag dependency:
    '''
    consume_and_load_circuit_task >> consume_and_load_race_task >> consume_and_load_freePracticeDim_task >> consume_and_load_raceResultsFact_task
    [consume_and_load_driver_task, consume_and_load_race_task] >> consume_and_load_lapsDim_task >> consume_and_load_raceResultsFact_task
    [consume_and_load_driver_task, consume_and_load_race_task] >> consume_and_load_pitStopsDim_task >> consume_and_load_raceResultsFact_task
    [consume_and_load_driver_task, consume_and_load_race_task] >> consume_and_load_driverStandingsDim_task >> consume_and_load_raceResultsFact_task
    consume_and_load_constructor_task >> consume_and_load_constructorStandingsDim_task >> consume_and_load_raceResultsFact_task
    
    '''