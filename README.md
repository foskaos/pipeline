
# Pipeline for Interview

## Overview
This project sets up a data pipeline using Docker and Docker Compose, integrating PostgreSQL and Django. The pipeline runs within a Dockerized environment, ensuring consistency across different setups.

Essential commands provided in a Makefile

## Prerequisites
- [Docker](https://www.docker.com/get-started) installed on your system.
- [Docker Compose](https://docs.docker.com/compose/install/) installed.

## Setup Instructions

### 1. Clone the Repository
```
git clone https://github.com/foskaos/pipeline
```

### 2. Prepare the Database
Copy the `msk_db.sql` file to the root directory of the project. This will be run in 'init-db.sh' when the container runs

### 3. Configure Environment Variables
Create a `.env` file in the project root and populate it with the following variables:

```
# PostgreSQL Settings
POSTGRES_DB=msk_database
POSTGRES_USER=msk_user
POSTGRES_PASSWORD=msk_password
POSTGRES_HOST=db
POSTGRES_PORT=5432
POSTGRES_SECONDARY_DB=msk_db
POSTGRES_ANALYTICS_DB=analytics_db

# Django Environment
DEBUG=1
SECRET_KEY=supersecretkey
```

### 4. Build and Start the Containers
Run the following command to build and start the containers:
```
docker-compose up --build
```
This will also run the migration which creates all the neccessary tables in the database.
Also sets up an hourly cron job

### 5. Access the Container
To enter the container's shell, open another terminal and run (the container is just called 'web':
```
docker-compose exec web bash
```

### 7. Run the tests
Execute the following command inside the web container to run the pipeline:
```
make test
```

### 7. Run the Pipeline
Execute the following command inside the web container to run the pipeline:
```
make run-pipeline
```

## Architecture Overview
This project consists of two main containers:
- **PostgreSQL Container (`db`)**: Hosts the primary and analytical databases.
- **Web Container (`web`)**: Runs the Django application and executes the data pipeline. It ensures PostgreSQL is fully initialized before starting.

## Notes
- The web container will automatically wait for the PostgreSQL database to be ready before starting Django.
- Ensure that Docker is running before executing any commands.

## Areas of Improvement
- During the loading of the analytics tables, we find a large number of orphaned relationships. We are removing the broken link but still importing the record. It might make sense to remove them at this stage
- Limited processing of slugs. The majority of slugs are parsed but a more extensive parser would be beneficial
- Better data cleansing at analytic stage
- The ```patient_journey_schedule_window``` table is quite large, it would be good to make an incremental loader for it, perhaps using hasing?
- To check which survey results were created in time, we could do make new table. It would have a conditional field base on the milestone slug to get the milestone date. The actual date window could be found from this. Then we could join the survey results based on this window and produce a list of patient activities that were compled in the schedule window
- As this is already dockerized, we could simply run ```make test``` in the container. The CI/CD pipeline could be configured to run this on every merge request
- WAY more testing. (Schedule slug transformer)


## Troubleshooting

- you may need to set up the provided data manually, but there is a docker command for this:
```
docker-compose run sql
```

