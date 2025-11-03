import json
import os
from AWSIoTPythonSDK.MQTTLib import AWSIoTMQTTClient
from influxdb_client import InfluxDBClient, Point, WritePrecision
import time

# --- AWS IoT Core settings ---
IOT_ENDPOINT = os.getenv("IOT_ENDPOINT")
CLIENT_ID = os.getenv("CLIENT_ID")
PATH_TO_CERT = os.getenv("PATH_TO_CERT")
PATH_TO_KEY = os.getenv("PATH_TO_KEY")
PATH_TO_ROOT = os.getenv("PATH_TO_ROOT")
TOPIC = "building/+/zone/+/telemetry"

# --- InfluxDB settings ---
INFLUX_URL = os.getenv("INFLUX_URL")
INFLUX_TOKEN = os.getenv("INFLUX_TOKEN")
INFLUX_ORG = os.getenv("ORG")
INFLUX_BUCKET = os.getenv("BUCKET")

# Connect to InfluxDB
influx_client = InfluxDBClient(url=INFLUX_URL, token=INFLUX_TOKEN, org=INFLUX_ORG)
write_api = influx_client.write_api()

# Callback to handle messages from AWS IoT Core
def message_callback(client, userdata, message):
    payload = json.loads(message.payload)
    print("--- received payload: ", payload)

    point = Point("telemetry") \
        .tag("building", payload["building"]) \
        .tag("zone", payload["zone"]) \
        .field("temperature", payload["temperature"]) \
        .field("humidity", payload["humidity"]) \
        .field("occupancy", payload.get("occupancy", 0)) \
        .time(time.time_ns(), WritePrecision.NS)
        
    print("Writing point:", point.to_line_protocol())
    write_api.write(bucket=INFLUX_BUCKET, record=point)
    print(f"Written to InfluxDB: {payload}")

# Connect to AWS IoT Core
client = AWSIoTMQTTClient(CLIENT_ID)
client.configureEndpoint(IOT_ENDPOINT, 8883)
client.configureCredentials(PATH_TO_ROOT, PATH_TO_KEY, PATH_TO_CERT)
client.connect()

# Subscribe to IoT Core topic
client.subscribe(TOPIC, 1, message_callback)

print("Bridge running — receiving telemetry...")
while True:
    pass

