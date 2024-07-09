# Data Engineering and Analytics: Formula 1 Pipeline

## Table of Contents

- [Introduction](#introduction)
- [Features](#features)
- [Project Tasks](#project-tasks)
  - [Data Modeling](#data-modeling)
  - [ETL Process](#etl-process)
  - [API Data Scraping](#api-data-scraping)
  - [Data Analysis](#data-analysis)
  - [PowerBI Report](#powerbi-report)
- [Installation](#installation)
- [Usage](#usage)
- [Project Structure](#project-structure)

## Introduction

This project, developed as part of a Data Engineering Internship, aims to build a comprehensive data pipeline for Formula 1 data. The project encompasses various stages, including data modeling, creating an ETL (Extract, Transform, Load) process using Apache Airflow and Kafka, API data scraping, and developing interactive reports using PowerBI. This pipeline is designed to handle large volumes of data, ensure real-time processing, and provide insightful visualizations for Formula 1 enthusiasts.

## Features

- **Data Modeling:** Designing a star schema suitable for analytical queries on Formula 1 data.
- **ETL Process:** Automating data extraction, transformation, and loading using Apache Airflow and Kafka for real-time data streaming.
- **API Data Scraping:** Integrating additional data sources via API scraping to enrich the dataset.
- **Data Analysis:** Creating comprehensive and interactive PowerBI reports to visualize and analyze key metrics.

## Project Tasks

### Data Modeling

The destination database for the processed data is implemented using PostgreSQL.
The first step in the data modeling process involved designing and implementing a star schema based on the Formula 1 dataset.

- **Schema Design:** Using dimensions such as Race, Driver, Team, Circuit, and Time to structure the data.
- **Entity-Relationship Diagram (ERD):** Defining primary and foreign keys to establish relationships between tables.

![ER Diagram](https://github.com/bojanb12/Data-Engineering-Analythics-Formula-1-Pipeline/blob/main/Readme/F1DataSet_Schema%20(5).png)

The star schema includes the following tables:

- **Dimension Tables:**
  - `sprintDim`
  - `driverDim`
  - `constructorDim`
  - `raceDim`
  - `circuitDim`
  - `raceStatusDim`
  - `driverStandingsDim`
  - `constructorStandingsDim`
  - `pitStopsDim`
  - `lapsDim`
  - `qualificationsDim`
  - `freePracticeDim`
- **Fact Table:**
  - `raceResultsFact`

#### Docker

The Docker Compose setup facilitates seamless communication between services:

- **PostgreSQL Server:** Used as the main database for storing transformed data.
- **Airflow PostgreSQL Server:** Acts as the metadata database for Airflow, ensuring task scheduling and execution.
- **Kafka:** Handles real-time data streaming between various stages of the ETL process.
- **Docker Services:** These services, defined in `docker-compose.yml`, ensure that all components (Airflow, PostgreSQL, Kafka, etc.) are correctly configured and can communicate efficiently.

The `docker-compose.yml` file specifies the setup and dependencies of each service. For example, the PostgreSQL database for Airflow is initialized with a user and database named 'airflow', while the source database is set up to be populated with initial tables from an SQL script upon starting.

### ETL Process

The ETL process is automated using Apache Airflow, which schedules and manages data workflows. Key components include:

- **Data Extraction:** Pulling raw data from various sources.
- **Data Transformation:** Using custom Python operators within Airflow to clean, transform, and prepare the data.
- **Data Loading:** Ingesting the transformed data into the star schema in the database.
- **Real-Time Streaming:** Implementing Kafka to handle data streaming, ensuring that data is processed in real-time.

![ETL Process](https://github.com/bojanb12/Data-Engineering-Analythics-Formula-1-Pipeline/blob/main/Readme/csv_pipeline.png)

![Kafka Process](https://github.com/bojanb12/Data-Engineering-Analythics-Formula-1-Pipeline/blob/main/Readme/kafka_consumeAndLoadDag.png)

### API Data Scraping

To enrich the existing dataset, additional data is scraped from APIs. This involves:

- **API Selection:** Choosing an appropriate API, such as the Ergast API, for additional Formula 1 data.
- **Data Integration:** Developing a Python script to fetch data from the API and integrating it into the existing pipeline, ensuring compatibility with the star schema.

### Data Analysis

Once the data is processed and stored, analytical tasks are performed to derive insights. This includes:

- **Database Views:** Creating views in the database to simplify complex queries.
- **Data Visualization:** Using PowerBI to create interactive dashboards that display key metrics and insights.

### PowerBI Report

The final stage involves developing a PowerBI report to visualize the enriched Formula 1 dataset. This report includes:

- **Interactive Dashboards:** Showcasing race results, driver performance, team standings, and circuit statistics.
- **Actionable Insights:** Providing insights for various stakeholders, including race strategists, team managers, and enthusiasts.

![PowerBI Dashboard](https://github.com/bojanb12/Data-Engineering-Analythics-Formula-1-Pipeline/blob/main/Readme/report2.png)

![PowerBI Dashboard2](https://github.com/bojanb12/Data-Engineering-Analythics-Formula-1-Pipeline/blob/main/Readme/report1.png)

![PowerBI Dashboard3](https://github.com/bojanb12/Data-Engineering-Analythics-Formula-1-Pipeline/blob/main/Readme/report3.png)

![PowerBI Dashboard4](https://github.com/bojanb12/Data-Engineering-Analythics-Formula-1-Pipeline/blob/main/Readme/report4.png)

## Installation

To set up the project locally, follow these steps:

1. Clone the Repository:
    ```sh
    git clone https://github.com/bojanb12/Data-Engineering-Analythics-Formula-1-Pipeline.git
    ```
2. Navigate to the Project Directory:
    ```sh
    cd Data-Engineering-Analythics-Formula-1-Pipeline
    ```
3. Set Up the Environment and Install Dependencies:
    ```sh
    pip install -r requirements.txt
    ```
4. Start Docker Containers:
    ```sh
    docker-compose up
    ```

## Usage

To run the project:

1. Access the Airflow Web Server: Open your browser and go to `http://localhost:8080` to access the Airflow web interface and trigger the DAGs.
2. Run the API Scraping Script:
    ```sh
    python scripts/api_scrape.py
    ```
3. Visualize Data in PowerBI:
    - Open PowerBI.
    - Connect to the database created by the pipeline.
    - Load the data and explore the interactive reports.

## Project Structure

The project repository is organized as follows:

    .
    ├── dags/
    │   ├── etl_pipeline.py           # ETL pipeline defined using Apache Airflow
    │   └── kafka_pipeline.py         # Kafka pipeline for real-time data processing
    ├── scripts/
    │   └── api_scrape.py             # Python script for API data scraping
    ├── docker-compose.yml            # Docker Compose file to set up services
    ├── requirements.txt              # Python dependencies
    ├── README.md                     # Project README file
    ├── DB_Schema/                    # Database schema images and SQL files
    ├── EDA/                          # Exploratory Data Analysis notebooks
    ├── PowerBIReport/                # PowerBI report file
    ├── config/                       # Configuration files
    ├── logs/                         # Log files
    ├── practice/                     # Practice scripts and notebooks
    ├── source_db_init/               # Scripts for initializing the source database
    ├── sql/                          # SQL scripts for data processing
    ├── .gitignore                    # Git ignore file
    ├── DEProjekat_workspace.code-workspace # Workspace configuration file
    ├── Dockerfile                    # Dockerfile for building the Docker image
    ├── docker-compose.yaml           # Docker Compose file
    └── web_scrape.py                 # Web scraping script
