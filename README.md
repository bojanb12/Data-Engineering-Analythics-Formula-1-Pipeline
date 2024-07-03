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
- [Project Structure](#project-structure)
- [License](#license)

## Introduction

This project, developed as part of a Data Engineering Internship, aims to build a comprehensive data pipeline for Formula 1 data. The project encompasses various stages, including data modeling, creating an ETL (Extract, Transform, Load) process using Apache Airflow and Kafka, API data scraping, and developing interactive reports using PowerBI. This pipeline is designed to handle large volumes of data, ensure real-time processing, and provide insightful visualizations for stakeholders.

## Features

- **Data Modeling:** Designing a star schema suitable for analytical queries on Formula 1 data.
- **ETL Process:** Automating data extraction, transformation, and loading using Apache Airflow and Kafka for real-time data streaming.
- **API Data Scraping:** Integrating additional data sources via API scraping to enrich the dataset.
- **Data Analysis:** Creating comprehensive and interactive PowerBI reports to visualize and analyze key metrics.

## Project Tasks

### Data Modeling

The project begins with designing and implementing a star schema based on the Formula 1 dataset. This involves:

- **Schema Design:** Using dimensions such as Race, Driver, Team, Circuit, and Time to structure the data.
- **Entity-Relationship Diagram (ERD):** Defining primary and foreign keys to establish relationships between tables.

![ER Diagram](path/to/er-diagram.png)

### ETL Process

The ETL process is automated using Apache Airflow, which schedules and manages data workflows. Key components include:

- **Data Extraction:** Pulling raw data from various sources.
- **Data Transformation:** Using custom Python operators within Airflow to clean, transform, and prepare the data.
- **Data Loading:** Ingesting the transformed data into the star schema in the database.
- **Real-Time Streaming:** Implementing Kafka to handle data streaming, ensuring that data is processed in real-time.

![ETL Process](path/to/etl-process.png)

### API Data Scraping

To enrich the existing dataset, additional data is scraped from APIs. This involves:

- **API Selection:** Choosing an appropriate API, such as the Ergast API, for additional Formula 1 data.
- **Data Integration:** Developing a Python script to fetch data from the API and integrating it into the existing pipeline, ensuring compatibility with the star schema.

![API Integration](path/to/api-integration.png)

### Data Analysis

Once the data is processed and stored, analytical tasks are performed to derive insights. This includes:

- **Database Views:** Creating views in the database to simplify complex queries.
- **Data Visualization:** Using PowerBI to create interactive dashboards that display key metrics and insights.

![Data Analysis](path/to/data-analysis.png)

### PowerBI Report

The final stage involves developing a PowerBI report to visualize the enriched Formula 1 dataset. This report includes:

- **Interactive Dashboards:** Showcasing race results, driver performance, team standings, and circuit statistics.
- **Actionable Insights:** Providing insights for various stakeholders, including race strategists, team managers, and enthusiasts.

![PowerBI Dashboard](path/to/powerbi-dashboard.png)

## Installation

To set up the project locally, follow these steps:

1. **Clone the Repository:**
    ```sh
    git clone https://github.com/bojanb12/Data-Engineering-Analythics-Formula-1-Pipeline.git
    ```
2. **Navigate to the Project Directory:**
    ```sh
    cd Data-Engineering-Analythics-Formula-1-Pipeline
    ```
3. **Set Up the Environment and Install Dependencies:**
    ```sh
    pip install -r requirements.txt
    ```
4. **Start Docker Containers:**
    ```sh
    docker-compose up
    ```

## Usage

To run the project:

1. **Access the Airflow Web Server:**
    Open your browser and go to `http://localhost:8080` to access the Airflow web interface and trigger the DAGs.
2. **Run the API Scraping Script:**
    ```sh
    python scripts/api_scrape.py
    ```
3. **Visualize Data in PowerBI:**
    - Open PowerBI.
    - Connect to the database created by the pipeline.
    - Load the data and explore the interactive reports.

## Project Structure

The project repository is organized as follows:

```plaintext
.
├── dags/
│   ├── etl_pipeline.py           # ETL pipeline defined using Apache Airflow
│   └── kafka_pipeline.py         # Kafka pipeline for real-time data processing
├── scripts/
│   └── api_scrape.py             # Python script for API data scraping
├── docker-compose.yml            # Docker Compose file to set up services
├── requirements.txt              # Python dependencies
├── README.md                     # Project README file
└── PowerBI/
    └── Formula1_Report.pbix      # PowerBI report file
