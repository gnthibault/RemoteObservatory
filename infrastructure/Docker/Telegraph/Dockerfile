# extract of documentation from: https://hub.docker.com/_/telegraf
# you can generate sample conf with
# docker run --rm telegraf telegraf config > telegraf.conf
# Then run the configuration with:
# docker run \
# -d \
# -v $PWD/telegraf.conf:/etc/telegraf/telegraf.conf:ro \
# telegraf

# Example configuration for opening a port to push data to
# Plugin HTTP_LISTENER
#Le plugin http_listener fonctionne en mode push. Il ouvre un port http et attend qu’on lui pousse des métriques.
#
# cat /etc/telegraf/telegraf.d/http_listener.conf
# ## Influx HTTP write listener
# [[inputs.http_listener]]
# ## Address and port to host HTTP listener on
# service_address = ":8186"
# ## timeouts
# read_timeout = "10s"
# write_timeout = "10s"
# Il faut ensuite envoyer les métriques au format InfluxDB line-protocol :
# curl -i -XPOST 'http://localhost:8186/write' --data-binary 'account_deleted,host=server01,region=us-west value=32 1434055562000000000'


#Pour configurer le backend, nous allons utiliser le plugin output InfluxDB.
# cat /etc/telegraf/telegraf.conf
# …
# [[outputs.influxdb]]
# urls = ["http://localhost:8086"]
# database = "influx_db"
# username = "influx_user"
# password = "influx_password"
# …
