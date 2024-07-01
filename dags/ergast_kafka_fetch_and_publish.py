from airflow import DAG
from airflow.sensors.external_task_sensor import ExternalTaskSensor
from airflow.hooks.base_hook import BaseHook
from airflow.operators.python import task

import pandas as pd
import requests
import time
from datetime import datetime
import json

from kafka import KafkaProducer
from kafka.errors import NoBrokersAvailable

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
    
    'f1_data_pipeline_kafka_fetchAndPublish',
    start_date=datetime(2024, 5, 27),
    schedule_interval='@weekly',
    catchup=False,
    
) as dag:
    
    # task for main dataset pipeline DAG dependancy
    wait_for_elt_dag = ExternalTaskSensor(
        
        task_id='wait_for_elt_dag',
        external_dag_id='f1_data_pipeline_taskflow',
        external_task_id='load_raceResults_task',
        start_date=datetime(2024, 5, 27),
        mode='poke',
        poke_interval=60,  
        timeout=600
    )   

    @task
    def fetch_and_publish_driver():
    
        url = 'http://ergast.com/api/f1/current/drivers.json'
        response = requests.get(url)
        data = response.json()
    
        retries = 5
        
        total_drivers_fetched = 0  # Initialize a counter for the number of drivers

        # Check if drivers data exists
        if 'MRData' in data and 'DriverTable' in data['MRData'] and 'Drivers' in data['MRData']['DriverTable']:
            drivers = data['MRData']['DriverTable']['Drivers']
            total_drivers_fetched = len(drivers)  # Update the counter
    
        for i in range(retries):
            try:
                print("tried to find producer")  # log
                producer = KafkaProducer(bootstrap_servers=kafka_bootstrap_servers, value_serializer=lambda v: json.dumps(v).encode('utf-8')) # the response has to be utf-8 in order to transform it later
                producer.send(kafka_topic_driver, value=data)
                producer.close()
                break
        
            # in case there are no Kafka brokers available, we wait
            except NoBrokersAvailable:
                if i < retries - 1:
                    print("sleeping")  # log
                    time.sleep(10)
                else:
                    raise
        
        print(f'Total number of drivers fetched: {total_drivers_fetched}')
    
    @task
    def fetch_and_publish_circuit():
    
        url = 'http://ergast.com/api/f1/current/circuits.json'
        response = requests.get(url)
        data = response.json()
    
        retries = 5
        
        total_circuits_fetched = 0  # Initialize a counter for the number of circuits

        # Check if circuits data exists
        if 'MRData' in data and 'CircuitTable' in data['MRData'] and 'Circuits' in data['MRData']['CircuitTable']:
            circuits = data['MRData']['CircuitTable']['Circuits']
            total_circuits_fetched = len(circuits)  # Update the counter
    
        for i in range(retries):
            try:
                print("tried to find producer")  # log
                producer = KafkaProducer(bootstrap_servers=kafka_bootstrap_servers, value_serializer=lambda v: json.dumps(v).encode('utf-8')) # the response has to be utf-8 in order to transform it later
                producer.send(kafka_topic_circuit, value=data)
                producer.close()
                break
        
            # in case there are no Kafka brokers available, we wait
            except NoBrokersAvailable:
                if i < retries - 1:
                    print("sleeping")  # log
                    time.sleep(10)
                else:
                    raise
        
        print(f'Total number of circuits fetched: {total_circuits_fetched}')

    @task
    def fetch_and_publish_constructor():
    
        url = 'http://ergast.com/api/f1/current/constructors.json'
        response = requests.get(url)
        data = response.json()
    
        retries = 5
        
        total_constructors_fetched = 0  # Initialize a counter for the number of constructors

        # Check if constructors data exists
        if 'MRData' in data and 'ConstructorTable' in data['MRData'] and 'Constructors' in data['MRData']['ConstructorTable']:
            constructors = data['MRData']['ConstructorTable']['Constructors']
            total_constructors_fetched = len(constructors)  # Update the counter
    
        for i in range(retries):
            try:
                print("tried to find producer")  # log
                producer = KafkaProducer(bootstrap_servers=kafka_bootstrap_servers, value_serializer=lambda v: json.dumps(v).encode('utf-8')) # the response has to be utf-8 in order to transform it later
                producer.send(kafka_topic_constructor, value=data)
                producer.close()
                break
        
            # in case there are no Kafka brokers available, we wait
            except NoBrokersAvailable:
                if i < retries - 1:
                    print("sleeping")  # log
                    time.sleep(10)
                else:
                    raise
                
        print(f'Total number of constructors fetched: {total_constructors_fetched}')
    
    @task
    def fetch_and_publish_race():
        base_url = 'http://ergast.com/api/f1/current'
        retries = 5
        total_races_fetched = 0  # Initialize a counter for the number of races

        # Fetch the list of races for the 2024 season
        response = requests.get(f'{base_url}.json')
        data = response.json()
        races = data['MRData']['RaceTable']['Races']

        for race in races:
            round_number = race['round']
            race_url = f'{base_url}/{round_number}/results.json'

            for i in range(retries):
                try:
                    race_response = requests.get(race_url)
                    race_data = race_response.json()

                    # Check if race results data exists
                    if 'MRData' in race_data and 'RaceTable' in race_data['MRData'] and 'Races' in race_data['MRData']['RaceTable']:
                        total_races_fetched += 1  # Update the counter

                    producer = KafkaProducer(
                        bootstrap_servers=kafka_bootstrap_servers,
                        value_serializer=lambda v: json.dumps(v).encode('utf-8')
                    )
                    producer.send(kafka_topic_race, value=race_data)
                    producer.close()
                    break

                # In case there are no Kafka brokers available, we wait
                except NoBrokersAvailable:
                    if i < retries - 1:
                        print("Sleeping")  # Log
                        time.sleep(10)
                    else:
                        raise
                    
        print(f'Total number of races fetched: {total_races_fetched}')  # Log
    
    @task
    def fetch_and_publish_freePractice():
    
        url = 'http://ergast.com/api/f1/current.json'
        response = requests.get(url)
        data = response.json()
    
        retries = 5
        
        total_free_practice_sessions = 0
        
        # Check if races data exists
        if 'MRData' in data and 'RaceTable' in data['MRData'] and 'Races' in data['MRData']['RaceTable']:
            races = data['MRData']['RaceTable']['Races']
            for race in races:
                # Count free practice sessions for each race
                for session in ['FirstPractice', 'SecondPractice', 'ThirdPractice']:
                    if session in race:
                        total_free_practice_sessions += 1
    
        for i in range(retries):
            try:
                print("tried to find producer")  # log
                producer = KafkaProducer(bootstrap_servers=kafka_bootstrap_servers, value_serializer=lambda v: json.dumps(v).encode('utf-8')) # the response has to be utf-8 in order to transform it later
                producer.send(kafka_topic_freePractice, value=data)
                producer.close()
                break
        
            # in case there are no Kafka brokers available, we wait
            except NoBrokersAvailable:
                if i < retries - 1:
                    print("sleeping")  # log
                    time.sleep(10)
                else:
                    raise
        
        print(f'Total number of free practice sessions fetched: {total_free_practice_sessions}')
    
    @task
    def fetch_and_publish_laps():
        
        base_url = 'http://ergast.com/api/f1/current'
        retries = 5
        total_laps_fetched = 0

        # Fetch the list of races for the current season
        response = requests.get(f'{base_url}.json')
        data = response.json()
        races = data['MRData']['RaceTable']['Races']

        print(f'Total races fetched: {len(races)}')

        for race in races:
            round_number = race['round']
            print(f'Fetching laps for race round: {round_number}')

            # Fetch the number of laps for this race
            lap_response = requests.get(f'{base_url}/{round_number}/laps/1.json')
            lap_data = lap_response.json()

            # Check if total laps is present in the response
            if 'total' in lap_data['MRData']:
                total_laps = int(lap_data['MRData']['total'])
                print(f'Total laps for round {round_number}: {total_laps}')
            else:
                print(f'No lap data available for round {round_number}')
                continue

            laps_fetched_for_round = 0

            if total_laps > 0:
                for lap_number in range(1, total_laps + 1):
                    url = f'{base_url}/{round_number}/laps/{lap_number}.json'
                    for i in range(retries):
                        try:
                            response = requests.get(url)
                            data = response.json()

                            # Check if 'Races' list is not empty
                            if 'Races' in data['MRData']['RaceTable'] and len(data['MRData']['RaceTable']['Races']) > 0:
                                producer = KafkaProducer(
                                    bootstrap_servers=kafka_bootstrap_servers,
                                    value_serializer=lambda v: json.dumps(v).encode('utf-8')
                                )
                                producer.send(kafka_topic_laps, value=data)
                                producer.close()
                                total_laps_fetched += 1
                                laps_fetched_for_round += 1
                                print(f'Fetched lap {lap_number} for round {round_number}')
                                break
                            else:
                                print(f'No lap data available for round {round_number}, lap {lap_number}')
                                break

                        except NoBrokersAvailable:
                            if i < retries - 1:
                                print("No brokers available, retrying...")
                                time.sleep(10)
                            else:
                                raise
            
            print(f'Total laps fetched for round {round_number}: {laps_fetched_for_round}')

        print(f'Total number of laps fetched: {total_laps_fetched}')
    
    @task
    def fetch_and_publish_pitStops():
        
        base_url = 'http://ergast.com/api/f1/current'
        retries = 5

        total_pitstops_fetched = 0  # Initialize counter for log

        try:
            # Fetch the list of races for the current season
            response = requests.get(f'{base_url}.json')
            response.raise_for_status()  # Raise HTTPError for bad responses

            data = response.json()

            # Check if races data exists
            if 'MRData' not in data or 'RaceTable' not in data['MRData'] or 'Races' not in data['MRData']['RaceTable']:
                raise ValueError("No races data available or unexpected response structure")

            races = data['MRData']['RaceTable']['Races']

            for race in races:
                round_number = race['round']

                # Fetch the pit stop data for this race
                pitstop_response = requests.get(f'{base_url}/{round_number}/pitstops.json')
                pitstop_response.raise_for_status()  # Raise HTTPError for bad responses

                pitstop_data = pitstop_response.json()

                # Check if race data exists in pitstop_data
                if 'MRData' not in pitstop_data or 'RaceTable' not in pitstop_data['MRData'] or 'Races' not in pitstop_data['MRData']['RaceTable']:
                    continue

                races_with_pitstops = pitstop_data['MRData']['RaceTable']['Races']

                # Iterate over each race with pit stops
                for race_with_pitstops in races_with_pitstops:
                    # Ensure there are pit stops available for this race
                    if 'PitStops' not in race_with_pitstops:
                        continue

                    pitstops = race_with_pitstops['PitStops']
                    
                    total_pitstops_fetched += len(pitstops)  # Update the counter for log

                    for pitstop in pitstops:
                        driver_id = pitstop['driverId']
                        stop = int(pitstop['stop'])
                        lap_pitstops = int(pitstop['lap'])
                        time_pitstops = pitstop['time']
                        duration_str = pitstop['duration']

                        # Handle duration conversion
                        try:
                            minutes, seconds = duration_str.split(':')
                            total_seconds = int(minutes) * 60 + float(seconds)
                        except ValueError:
                            # Handle cases where duration_str doesn't split into two parts
                            total_seconds = None  # or any default value you prefer

                        # Prepare the data for Kafka
                        kafka_data = {
                            'season': race['season'],  # Add season from race data
                            'round': race['round'],    # Add round from race data
                            'driverId': driver_id,
                            'stop': stop,
                            'lap_pitstops': lap_pitstops,
                            'time_pitstops': time_pitstops,
                            'duration': total_seconds
                        }

                        # Publish to Kafka topic
                        producer = KafkaProducer(
                            bootstrap_servers=kafka_bootstrap_servers,
                            value_serializer=lambda v: json.dumps(v).encode('utf-8')
                        )
                        producer.send(kafka_topic_pitStops, value=kafka_data)
                        producer.close()

                        # Sleep briefly to avoid rate limiting
                        time.sleep(0.1)
        
        except requests.exceptions.RequestException as e:
            # Handle any request exception (including HTTP errors)
            print(f"Request failed: {e}")
            raise  # Reraise the exception to indicate task failure
        
        except (ValueError, KeyError) as e:
            # Handle specific JSON or data structure errors
            print(f"Data processing failed: {e}")
            raise  # Reraise the exception to indicate task failure

        except Exception as e:
            # Handle any other unexpected errors
            print(f"Unexpected error: {e}")
            raise  # Reraise the exception to indicate task failure
        
        print(f'Total number of pit stops fetched: {total_pitstops_fetched}')  # Log the total fetched

    @task
    def fetch_and_publish_raceStatus():
        
        base_url = 'http://ergast.com/api/f1/status'
        
        total_raceStatus_fetched = 0 # for log
        
        # Fetch the status data
        response = requests.get(f'{base_url}.json')
        data = response.json()
        
        # Check if status data exists
        if 'MRData' not in data or 'StatusTable' not in data['MRData'] or 'Status' not in data['MRData']['StatusTable']:
            raise ValueError("No status data available or unexpected response structure")
        
        statuses = data['MRData']['StatusTable']['Status']
        
        for status in statuses:
            
            status_id = int(status['statusId'])
            status_description = status['status']
            
            total_raceStatus_fetched += len(statuses)  # Update the counter for log
            
            # Prepare the data for Kafka
            kafka_data = {
                'statusId': status_id,
                'status': status_description
            }
            
            # Publish to Kafka topic
            producer = KafkaProducer(
                bootstrap_servers=kafka_bootstrap_servers,
                value_serializer=lambda v: json.dumps(v).encode('utf-8')
            )
            producer.send(kafka_topic_raceStatus, value=kafka_data)
            producer.close()
            
            # Sleep briefly to avoid rate limiting
            time.sleep(0.1)
            
        print(f'Total number of new race statuses fetched: {total_raceStatus_fetched}') # log 

    @task
    def fetch_and_publish_driverStandings():
        base_url = 'http://ergast.com/api/f1/2024'
        retries = 5
        total_driver_standings_fetched = 0  # for log

        # Fetch the list of races for the 2024 season
        response = requests.get(f'{base_url}.json')
        data = response.json()
        races = data['MRData']['RaceTable']['Races']

        for race in races:
            round_number = race['round']
            print(f"Fetching driver standings for round {round_number}")

            # Fetch the driver standings for this round
            url = f'{base_url}/{round_number}/driverStandings.json'
            for i in range(retries):
                try:
                    response = requests.get(url)
                    response.raise_for_status()  # Raise HTTPError for bad responses
                    data = response.json()

                    # Check if the required keys are present in the response
                    if ('MRData' in data and 
                        'StandingsTable' in data['MRData'] and 
                        'StandingsLists' in data['MRData']['StandingsTable'] and 
                        len(data['MRData']['StandingsTable']['StandingsLists']) > 0):
                        
                        driver_standings = data['MRData']['StandingsTable']['StandingsLists'][0].get('DriverStandings', [])
                        total_driver_standings_fetched += len(driver_standings)
                        
                        if driver_standings:
                            producer = KafkaProducer(
                                bootstrap_servers=kafka_bootstrap_servers,
                                value_serializer=lambda v: json.dumps(v).encode('utf-8')
                            )
                            producer.send(kafka_topic_driverStandings, value=data)
                            producer.close()
                        else:
                            print(f"No driver standings available for round {round_number}")
                        break
                    else:
                        print(f"Standings data not found or empty for round {round_number}. Full response content:")
                        print(json.dumps(data, indent=4))  # Log the full response
                        break  # Exit retry loop since standings are not available for this round
                        
                except requests.exceptions.RequestException as e:
                    if i < retries - 1:
                        time.sleep(10)
                    else:
                        print(f"Request failed: {e}")
                        raise
        
        print(f'Total number of driver standings fetched: {total_driver_standings_fetched}')

    @task
    def fetch_and_publish_constructorStandings():
        
        base_url = 'http://ergast.com/api/f1/2024'
        retries = 5
        total_constructor_standings_fetched = 0  # for log

        # Fetch the list of races for the current season
        response = requests.get(f'{base_url}.json')
        data = response.json()
        races = data['MRData']['RaceTable']['Races']

        for race in races:
            round_number = race['round']
            print(f"Fetching constructor standings for round {round_number}")

            # Fetch the constructor standings for this round
            url = f'{base_url}/{round_number}/constructorStandings.json'
            for i in range(retries):
                try:
                    response = requests.get(url)
                    response.raise_for_status()  # Raise HTTPError for bad responses
                    data = response.json()

                    # Check if the required keys are present in the response
                    if ('MRData' in data and 
                        'StandingsTable' in data['MRData'] and 
                        'StandingsLists' in data['MRData']['StandingsTable'] and 
                        len(data['MRData']['StandingsTable']['StandingsLists']) > 0):

                        constructor_standings = data['MRData']['StandingsTable']['StandingsLists'][0].get('ConstructorStandings', [])
                        total_constructor_standings_fetched += len(constructor_standings)

                        if constructor_standings:
                            producer = KafkaProducer(
                                bootstrap_servers=kafka_bootstrap_servers,
                                value_serializer=lambda v: json.dumps(v).encode('utf-8')
                            )
                            producer.send(kafka_topic_constructorStandings, value=data)
                            producer.close()
                        else:
                            print(f"No constructor standings available for round {round_number}")
                        break
                    else:
                        print(f"Standings data not found or empty for round {round_number}. Full response content:")
                        print(json.dumps(data, indent=4))  # Log the full response
                        break  # Exit retry loop since standings are not available for this round

                except requests.exceptions.RequestException as e:
                    if i < retries - 1:
                        time.sleep(10)
                    else:
                        print(f"Request failed: {e}")
                        raise

        print(f'Total number of constructor standings fetched: {total_constructor_standings_fetched}')

    @task
    def fetch_and_publish_raceResults():

        base_url = 'http://ergast.com/api/f1'
        retries = 5

        total_results_fetched = 0  # Counter for the log

        try:
            # Fetch the list of races for the current season
            response = requests.get(f'{base_url}/2024/results.json')
            response.raise_for_status()  # Raise HTTPError for bad responses

            data = response.json()

            # Check if the races data exists
            if 'MRData' not in data or 'RaceTable' not in data['MRData'] or 'Races' not in data['MRData']['RaceTable']:
                raise ValueError("No races data available or unexpected response structure")

            races = data['MRData']['RaceTable']['Races']

            for race in races:
                round_number = race['round']
                race_date = race.get('date')  # Fetch the date of the race

                # Fetch the race results data for this race
                results_response = requests.get(f'{base_url}/2024/{round_number}/results.json')
                results_response.raise_for_status()  # Raise HTTPError for bad responses

                results_data = results_response.json()

                # Check if race data exists in results_data
                if 'MRData' not in results_data or 'RaceTable' not in results_data['MRData'] or 'Races' not in results_data['MRData']['RaceTable']:
                    continue

                races_with_results = results_data['MRData']['RaceTable']['Races']

                # Iterate over each race with results
                for race_with_results in races_with_results:
                    # Ensure there are results available for this race
                    if 'Results' not in race_with_results:
                        continue

                    results = race_with_results['Results']

                    for result in results:
                        driver_id = result['Driver']['driverId']
                        constructor_id = result['Constructor']['constructorId']
                        status_id = result['status']
                        position_order = result['position']
                        points = float(result['points'])
                        laps = int(result['laps'])
                        grid = int(result['grid'])
                        
                        # Check if 'Time' key exists
                        if 'Time' in result:
                            race_time = result['Time']['time']
                        else:
                            race_time = None  # or any default value, if it's not in the API response

                        # Check if 'FastestLap' key exists
                        if 'FastestLap' in result:
                            fastest_lap_time = result['FastestLap'].get('Time', {}).get('time')
                            fastest_lap_speed = float(result['FastestLap'].get('AverageSpeed', {}).get('speed'))
                            fastest_lap = int(result['FastestLap'].get('lap'))
                        else:
                            fastest_lap_time = None
                            fastest_lap_speed = None
                            fastest_lap = None

                        # Prepare the data for Kafka
                        kafka_data = {
                            'round': round_number,
                            'date': race_date,
                            'constructorId': constructor_id,
                            'driverId': driver_id,
                            'statusId': status_id,
                            'positionOrder': position_order,
                            'points': points,
                            'laps': laps,
                            'grid': grid,
                            'fastestLapTime': fastest_lap_time,
                            'fastestLapSpeed': fastest_lap_speed,
                            'time': race_time,
                            'fastestLap': fastest_lap
                        }

                        # Publish to Kafka topic
                        producer = KafkaProducer(
                            bootstrap_servers=kafka_bootstrap_servers,
                            value_serializer=lambda v: json.dumps(v).encode('utf-8')
                        )
                        producer.send(kafka_topic_raceResults, value=kafka_data)
                        producer.close()

                        # Sleep briefly to avoid rate limiting
                        time.sleep(0.1)

                        total_results_fetched += 1  # Update the counter for log
        
        # --- Error logs:
        except requests.exceptions.RequestException as e:
            # Handle any request exception (including HTTP errors)
            print(f"Request failed: {e}")
            raise  # Reraise the exception to indicate task failure

        except (ValueError, KeyError) as e:
            # Handle specific JSON or data structure errors
            print(f"Data processing failed: {e}")
            raise  # Reraise the exception to indicate task failure

        except Exception as e:
            # Handle any other unexpected errors
            print(f"Unexpected error: {e}")
            raise  # Reraise the exception to indicate task failure

        print(f'Total number of race results fetched: {total_results_fetched}')  # Log


# -- FETCH AND PUBLISH --
    fetch_and_publish_driver_task = fetch_and_publish_driver()
    fetch_and_publish_circuit_task = fetch_and_publish_circuit()
    fetch_and_publish_constructor_task = fetch_and_publish_constructor()
    fetch_and_publish_race_task = fetch_and_publish_race()
    fetch_and_publish_freePractice_task = fetch_and_publish_freePractice()
    fetch_and_publish_laps_task = fetch_and_publish_laps()
    fetch_and_publish_pitStops_task = fetch_and_publish_pitStops()
    fetch_and_publish_raceStatus_task = fetch_and_publish_raceStatus()
    fetch_and_publish_driverStandings_task = fetch_and_publish_driverStandings()
    fetch_and_publish_constructorStandings_task = fetch_and_publish_constructorStandings()
    fetch_and_publish_raceResults_task = fetch_and_publish_raceResults()
    
# -- TASKFLOW --
wait_for_elt_dag >> [fetch_and_publish_driver_task, fetch_and_publish_circuit_task, fetch_and_publish_constructor_task, fetch_and_publish_race_task, fetch_and_publish_freePractice_task, fetch_and_publish_laps_task, fetch_and_publish_pitStops_task, fetch_and_publish_raceStatus_task, fetch_and_publish_driverStandings_task, fetch_and_publish_constructorStandings_task, fetch_and_publish_raceResults_task]
#[fetch_and_publish_driver_task, fetch_and_publish_circuit_task, fetch_and_publish_constructor_task, fetch_and_publish_race_task, fetch_and_publish_freePractice_task, fetch_and_publish_laps_task, fetch_and_publish_pitStops_task, fetch_and_publish_raceStatus_task, fetch_and_publish_driverStandings_task, fetch_and_publish_constructorStandings_task] >> fetch_and_publish_raceResults_task