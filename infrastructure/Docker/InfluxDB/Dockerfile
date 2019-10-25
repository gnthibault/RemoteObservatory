# Doc from https://hub.docker.com/_/influxdb
# you can generate sample conf with
# docker run --rm influxdb influxd config > influxdb.conf

# Then run the configuration with:
# docker run \
# -p 8086:8086 \
# -d \
# -v $PWD/influxdb.conf:/etc/influxdb/influxdb.conf:ro \
#  -v /home/data:/var/lib/influxdb \
# -e "INFLUXDB_REPORTING_DISABLED=true" \
# -e "INFLUXDB_DATA_QUERY_LOG_ENABLED=false" \
# influxdb -config /etc/influxdb/influxdb.conf


# Example of how to use it:
# Creating a DB named mydb:
# curl -G http://localhost:8086/query --data-urlencode "q=CREATE DATABASE remoteobservatory"
# Inserting into the DB:
# curl -i -XPOST 'http://localhost:8086/write?db=mydb' --data-binary 'cpu_load_short,host=server01,region=us-west value=0.64 1434055562000000000'


# with the client initializing a db looks like this:
# influx -execute "CREATE DATABASE influx_db"
# Créons l’utilisateur influx_user :
# influx -execute “CREATE USER influx_user WITH PASSWORD 'influx_password'”
# influx -execute “GRANT ALL ON influx_db TO influx_user
# Il est possible de créer une retention policy pour déterminer la durée de conservation des données :
# influx -execute ‘CREATE RETENTION POLICY "one_year" ON "influx_db" DURATION 365d’
