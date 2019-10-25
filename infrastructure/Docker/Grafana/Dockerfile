# Doc from https://grafana.com/docs/installation/docker/
# All options defined in conf/grafana.ini can be overridden using environment
# variables by using the syntax GF_<SectionName>_<KeyName>
# don't forget to create a volume: docker volume create grafana-storage
# Check latest versions here: https://hub.docker.com/r/grafana/grafana/

# docker run \
# -d \
# --rm \
# -p 3000:3000 \
# --name=grafana \
# -e "GF_INSTALL_PLUGINS=grafana-clock-panel,grafana-simple-json-datasource" \
# -e "GF_INSTALL_PLUGINS=http://plugin-domain.com/my-custom-plugin.zip;custom-plugin" \
# -e "GF_SERVER_ROOT_URL=http://grafana.server.name" \
# -e "GF_SECURITY_ADMIN_PASSWORD=secret" \
# -v grafana-storage:/var/lib/grafana \
# grafana/grafana:6.4.3

# La première étape dans Grafana est d’ajouter la source de donnée (InfluxDB dans notre cas). Allons dans “Datasource” puis “Add Datasource” et ajoutons la base Influxdb.

# Database : influx_db
# Username : influx_user
# Password : influx_password


