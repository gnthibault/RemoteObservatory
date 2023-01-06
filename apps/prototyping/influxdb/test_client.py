from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.write_api import SYNCHRONOUS

bucket = "observatory"

client = InfluxDBClient(url="http://localhost:8086", token="observatory", org="observatory")

#write_api = client.write_api(write_options=SYNCHRONOUS)
#p = Point("my_measurement").tag("location", "Prague").field("temperature", 25.3)
#write_api.write(bucket=bucket, record=p)
## using Table structure


q = '''
    from(bucket: "observatory")
      |> range(start: -7d, stop: now())
      |> filter(fn: (r) => r._measurement == "mqtt_observatory_broker")
      |> filter(fn: (r) => r._field == "data")
      |> yield(name: "notification")
'''
# Notice filter on r._field is useless, you should use keep()

query_api = client.query_api()
notifications = query_api.query(q)

# Result can be one or multiple tables depending on your query
#for table in tables:
#    for row in table.records:
#        print (row.values)
for notification in notifications[0].records:
    #print(notification)
    #FluxRecord() table: 0, {'result': 'notification', 'table': 0, '_start': datetime.datetime(2022, 12, 30, 10, 17, 1, 300950, tzinfo=tzutc()), '_stop': datetime.datetime(2023, 1, 6, 10, 17, 1, 300950, tzinfo=tzutc()), '_time': datetime.datetime(2023, 1, 5, 19, 47, 7, 548470, tzinfo=tzutc()), '_value': 'This is a test', '_field': 'data', '_measurement': 'mqtt_observatory_broker', 'host': 'observatory_pi', 'topic': 'observatory/BROKER'}
    print(notification['_value'])
