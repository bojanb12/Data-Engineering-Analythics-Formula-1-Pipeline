# Data Engineering and Analytics: Formula 1 Pipeline

![Project Banner](path/to/banner-image.png)

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
- [Contributing](#contributing)
- [License](#license)
- [Acknowledgments](#acknowledgments)

## Introduction

This project is part of a Data Engineering Internship, aimed at building a robust data pipeline for Formula 1 data. The project involves data modeling, ETL process creation using Apache Airflow and Kafka, API data scraping, and developing a PowerBI report.

## Features

- **Data Modeling:** Creating a star schema for the Formula 1 dataset.
- **ETL Process:** Automating data extraction, transformation, and loading using Apache Airflow and Kafka.
- **API Data Scraping:** Integrating additional data from APIs.
- **Data Analysis:** Using PowerBI to create interactive reports.

## Project Tasks

### Data Modeling

- Designed and implemented a star schema using the Formula 1 dataset.
- Identified dimensions such as Race, Driver, Team, Circuit, and Time, along with necessary fact tables.
- Defined primary and foreign keys to establish relationships.

![ER Diagram](path/to/er-diagram.png)

### ETL Process

- Developed an ETL process using Apache Airflow to automate data handling.
- Wrote custom operators in Python for data transformation.
- Implemented Kafka for real-time data streaming.

![ETL Process](path/to/etl-process.png)

### API Data Scraping

- Identified a suitable API (Ergast API) for additional Formula 1 data.
- Created a Python script to scrape and integrate this data into the existing pipeline.

![API Integration](path/to/api-integration.png)

### Data Analysis

- Created database views to simplify data analysis.
- Used PowerBI to connect to the database and create dashboards.

![Data Analysis](path/to/data-analysis.png)

### PowerBI Report

- Designed interactive reports showcasing key metrics like race results, driver performance, team standings, and circuit statistics.

![PowerBI Dashboard](path/to/powerbi-dashboard.png)

## Installation

1. Clone the repository:
    ```sh
    git clone https://github.com/bojanb12/Data-Engineering-Analythics-Formula-1-Pipeline.git
    ```
2. Navigate to the project directory:
    ```sh
    cd Data-Engineering-Analythics-Formula-1-Pipeline
    ```
3. Set up the environment and install dependencies:
    ```sh
    pip install -r requirements.txt
    ```

## Usage

1. Start Docker containers:
    ```sh
    docker-compose up
    ```
2. Access the Airflow web server at `http://localhost:8080` and trigger the DAGs.
3. Run the API scraping script:
    ```sh
    python scripts/api_scrape.py
    ```
4. Open PowerBI and connect to the database to view the dashboard.
