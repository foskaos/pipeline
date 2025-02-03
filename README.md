# Pipeline for Interview

How to use this:

1. clone repo
2. docker-compose up --build
3. create msk_db in postgres
4. create analytics_db in postgres

How it works:

we have a postgres container and a 'web container'

the web container is where django is set up and will have the pipeline. It waits until postgres is up to start



3.
copy file
docker cp msk_db.sql postgres_db:/msk_db.sql
enter container
docker exec -it postgres_db psql -U msk_user -d msk_database
create database 

docker exec -it postgres_db psql -U msk_user -d msk_db -f /msk_db.sql
copy file


