# Getting Started

- you can reference the docs, where this code is copied from: https://huggingface.co/datasets/rajpurkar/squad
- all you need is docker: https://get.docker.com/


# Run

- First, let’s get set up

```bash
# start the docker container
docker run -d --name pgai -p 5432:5432 \
-v pg-data:/home/postgres/pgdata/data \
-e POSTGRES_PASSWORD=password timescale/timescaledb-ha:pg17

# install PGAI in database
docker exec -it pgai psql -c "CREATE EXTENSION ai CASCADE;"
# go into the container
docker exec -it pgai psql
```

- Now, let’s create a table from your dataset

```bash
select ai.load_dataset('rajpurkar/squad', table_name => 'squad');
```
