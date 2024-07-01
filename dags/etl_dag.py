from airflow import DAG
from airflow.operators.python_operator import PythonOperator
from airflow.operators.bash import BashOperator
from airflow.providers.postgres.hooks.postgres import PostgresHook
from sqlalchemy import exc

from airflow.decorators import task    # TaskFlowAPI in order to be able to use @task decorators

from datetime import datetime
import pandas as pd
import numpy as np

'''    
    @task()
    def print_connection():
        from airflow.hooks.base_hook import BaseHook
        conn = BaseHook.get_connection("sourcedb_connection")
        print(conn.host, conn.login, conn.password)

    print_conn_task = print_connection()

'''

# iniciating the Airflow DAG, start time, interval
with DAG(
    
    'f1_data_pipeline_taskflow',
    start_date=datetime(2024, 5, 27),
    schedule_interval='@weekly',
    max_active_runs=1,
    catchup=False,
    
) as dag:
    
    @task
    def extract_data():
        
        csv_path = "/opt/airflow/csv/DatasetF1.csv"
        
        df = pd.read_csv(csv_path)
        
        # In some places in the dataset the value is set to '\N', we convert it to NaN so we can transform columns later
        df.replace('\\N', None, inplace=True)
        
        # ---TO NUMERIC--- 
        columns_to_numeric = ['position', 'fastestLap', 'fastestLapSpeed', 'alt', 'duration', 'milliseconds_laptimes', 'milliseconds', 'circuitId', 'milliseconds_pitstops']
        df[columns_to_numeric] = df[columns_to_numeric].apply(pd.to_numeric, errors='coerce', axis=1)
        
        #df['time'] = pd.to_datetime(df['time'])
        #df['duration'] = pd.to_timedelta(df['duration'], 'seconds')
        
        # ---DROP--- unecessary columns
        columns_to_drop = ['positionText', 'positionText_driverstandings', 'positionText_constructorstandings', 'number_drivers', 'milliseconds_pitstops']
        df = df.drop(columns=columns_to_drop)
        
        return df

    @task
    def driverDim_transform(df: pd.DataFrame):
        
        df.drop_duplicates(subset=['driverId'], inplace=True)
        
        df['dob'] = pd.to_datetime(df['dob']).dt.date
        
        #df.sort_values(by='driverId')
        
        driverDim = df[['driverId', 'driverRef', 'forename', 'surname', 'dob', 'nationality', 'code', 'number', 'url']].drop_duplicates()
        
        return driverDim
    
    @task
    def constructorDim_transform(df: pd.DataFrame):
        
        constructorDim = df[['constructorId', 'constructorRef', 'name', 'nationality_constructors', 'url_constructors']].drop_duplicates()
        
        return constructorDim
    
    @task
    def circuitDim_transform(df: pd.DataFrame):
        
        df.drop_duplicates(subset=['circuitId'], inplace=True)
        
        circuitDim = df[['circuitId', 'name_y', 'circuitRef', 'location', 'country', 'lat', 'lng', 'alt', 'url_y']].drop_duplicates()
        
        return circuitDim
    
    @task
    def raceStatusDim_transform(df: pd.DataFrame):
        
        df.drop_duplicates(subset=['statusId'], inplace=True)
        
        raceStatusDim = df[['statusId', 'status']].drop_duplicates()
        
        return raceStatusDim
    
    @task
    def raceDim_transform(df: pd.DataFrame):
        
        df.drop_duplicates(subset=['raceId'], inplace=True)
        
        raceDim = df[['raceId', 'circuitId', 'name_x', 'date', 'year', 'round', 'time_races', 'url_x']].drop_duplicates()
        
        return raceDim
    
    @task
    def sprint_transform(df: pd.DataFrame):
        
        #df.drop_duplicates(subset=['raceId'], inplace=True)
        
        raceDim = df[['raceId', 'driverId', 'sprint_date', 'sprint_time']].drop_duplicates()
        
        return raceDim
    
    @task
    def driverStandingsDim_transform(df: pd.DataFrame):
        
        #df.drop_duplicates(subset=['driverStandingsId'], inplace=True)
        
        driverStandingsDim = df[['driverStandingsId', 'driverId', 'position_driverstandings', 'points_driverstandings', 'wins']].drop_duplicates()
        
        return driverStandingsDim
    
    @task
    def constructorStandingsDim_transform(df: pd.DataFrame):
        
        constructorStandingsDim = df[['constructorStandingsId', 'constructorId', 'position_constructorstandings', 'wins_constructorstandings', 'points_constructorstandings']].drop_duplicates()
        
        return constructorStandingsDim
    
    @task
    def pitStopsDim_transform(df: pd.DataFrame):
        
        #df['milliseconds_pitstops'] = pd.to_timedelta(df['milliseconds_pitstops'], 'milliseconds')
        
        #df['duration'] = pd.to_datetime(df['duration'])
        
        pitStopsDim = df[['raceId', 'driverId', 'stop', 'lap_pitstops', 'time_pitstops', 'duration']].drop_duplicates()
        
        return pitStopsDim
    
    @task
    def qualificationsDim_transform(df: pd.DataFrame):
        
        qualificationsDim = df[['raceId', 'driverId', 'quali_time', 'quali_date']].drop_duplicates()
        
        return qualificationsDim
    
    @task
    def freePracticeDim_transform(df: pd.DataFrame):
        
        freePracticeDim = df[['raceId', 'fp1_date', 'fp2_date', 'fp3_date', 'fp1_time', 'fp2_time', 'fp3_time']].drop_duplicates()
        
        return freePracticeDim
    
    @task
    def lapsDim_transform(df: pd.DataFrame):
        
        #df['milliseconds_laptimes'] = pd.to_datetime(df['milliseconds_laptimes'])
        
        lapsDim = df[['raceId', 'driverId', 'lap', 'time_laptimes', 'milliseconds_laptimes', 'position_laptimes']].drop_duplicates()
        
        return lapsDim
    
    @task
    def raceResultsFact_transform(df: pd.DataFrame):
        
        #df['fastestLapTime'] = pd.to_datetime(df['fastestLapTime'], format='mixed')
        
        #df['milliseconds'] = pd.to_datetime(df['milliseconds'])
        
        raceResultsFact = df[['resultId', 'raceId', 'constructorId', 'driverId', 'constructorStandingsId', 'driverStandingsId', 'statusId', 'positionOrder', 'points', 'laps', 'grid', 'fastestLapTime', 'fastestLapSpeed', 'time', 'fastestLap']].drop_duplicates()
        
        return raceResultsFact

    @task
    def load_data(df: pd.DataFrame, table_name: str):
        
        # connection to the postgres database via sqlalchemy on the given connection id
        postgres_conn_id = 'sourcedb_connection'
        postgres_hook = PostgresHook(postgres_conn_id=postgres_conn_id)
        engine = postgres_hook.get_sqlalchemy_engine()
        df.to_sql(table_name, engine, if_exists='append', index=False)
        
        '''
        #ako se dag opet pokrene, a vec postoje ti kljucevi u tabeli, igorisemo ih, tj. samo unique dodajemo
        #jako usporava load, mora da postoji bolji nacin!!!
        for i in range(len(df)):
            try:
                df.iloc[i:i+1].to_sql(table_name, engine, if_exists='append',index=False)
            except exc.IntegrityError:
                pass #ako kljuc vec postoji, ignorisemo tu torku (idemo dalje da vidimo da li ima novih)
        '''
    
    data = extract_data()
    
    # -- Transformation tasks:
    driverDim = driverDim_transform(data)
    constructorDim = constructorDim_transform(data)
    circuitDim = circuitDim_transform(data)
    raceStatusDim = raceStatusDim_transform(data)
    raceDim = raceDim_transform(data)
    sprintDim = sprint_transform(data)
    driverStandingsDim = driverStandingsDim_transform(data)
    constructorStandingsDim = constructorStandingsDim_transform(data)
    pitStopsDim = pitStopsDim_transform(data)
    qualificationsDim = qualificationsDim_transform(data)
    freePracticeDim = freePracticeDim_transform(data)
    lapsDim = lapsDim_transform(data)
    raceResultsFact = raceResultsFact_transform(data)
    
    # -- Load tasks:
    load_constructor_task = load_data.override(task_id="load_constructor_task")(constructorDim, 'constructorDim')
    load_driver_task = load_data.override(task_id="load_driver_task")(driverDim, 'driverDim')
    load_circuit_task = load_data.override(task_id="load_circuit_task")(circuitDim, 'circuitDim')
    load_status_task = load_data.override(task_id="load_status_task")(raceStatusDim, 'raceStatusDim')
    load_race_task = load_data.override(task_id="load_race_task")(raceDim, 'raceDim')
    load_sprint_task = load_data.override(task_id="load_sprint_task")(sprintDim, 'sprintDim')
    load_driverStandings_task = load_data.override(task_id="load_driverStandings_task")(driverStandingsDim, 'driverStandingsDim')
    load_constructorStandings_task = load_data.override(task_id="load_constructorStandings_task")(constructorStandingsDim, 'constructorStandingsDim')
    load_pitStops_task = load_data.override(task_id="load_pitStops_task")(pitStopsDim, 'pitStopsDim')
    load_quafications_task = load_data.override(task_id="load_qualifications_task")(qualificationsDim, 'qualificationsDim')
    load_practice_task = load_data.override(task_id="load_practice_task")(freePracticeDim, 'freePracticeDim')
    load_laps_task = load_data.override(task_id="load_laps_task")(lapsDim, 'lapsDim')
    load_raceResults_task = load_data.override(task_id="load_raceResults_task")(raceResultsFact, 'raceResultsFact')
    
    # -- Task Flow:
    constructorDim >> raceDim 
    raceResultsFact >> lapsDim
    raceStatusDim >> pitStopsDim >> qualificationsDim >> sprintDim
    load_constructor_task >> load_constructorStandings_task 
    load_driver_task >> load_driverStandings_task
    load_circuit_task >> raceDim >> load_race_task
    pitStopsDim >> load_race_task >> [load_sprint_task, load_practice_task, load_pitStops_task, load_quafications_task, load_laps_task, load_status_task] >> load_raceResults_task

    #load_circuit_task >> load_status_task >> load_race_task >> load_sprint_task >> load_practice_task
    #[load_driver_task, load_race_task] >> load_pitStops_task >> load_quafications_task