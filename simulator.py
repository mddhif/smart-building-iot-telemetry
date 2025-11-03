import os
import time
import json
import random
from dotenv import load_dotenv
from AWSIoTPythonSDK.MQTTLib import AWSIoTMQTTClient

load_dotenv()

CLIENT_ID = os.getenv("CLIENT_ID", "BuildingSim")
ENDPOINT = os.getenv("AWS_IOT_ENDPOINT")
ROOT_CA = os.getenv("ROOT_CA_PATH", "AmazonRootCA1.pem")
PRIVATE_KEY = os.getenv("PRIVATE_KEY_PATH", "mything.private.key")
CERTIFICATE = os.getenv("CERTIFICATE_PATH", "mything.cert.pem")
BUILDING = os.getenv("BUILDING_ID", "building-1")
SIM_INTERVAL = float(os.getenv("SIM_INTERVAL", 10))

ZONES = [
    {"zone_id": "zone-101", "temp": 21.0, "hum": 45},
    {"zone_id": "zone-102", "temp": 23.5, "hum": 50},
    {"zone_id": "zone-103", "temp": 19.8, "hum": 40},
]

mqtt_client = AWSIoTMQTTClient(CLIENT_ID)
mqtt_client.configureEndpoint(ENDPOINT, 8883)
mqtt_client.configureCredentials(ROOT_CA, PRIVATE_KEY, CERTIFICATE)
mqtt_client.configureAutoReconnectBackoffTime(1, 32, 20)
mqtt_client.configureOfflinePublishQueueing(-1)
mqtt_client.configureDrainingFrequency(2)
mqtt_client.configureConnectDisconnectTimeout(10)
mqtt_client.configureMQTTOperationTimeout(5)

def on_command(client, userdata, message):
    """Callback for received commands"""
    payload = json.loads(message.payload.decode())
    print(f"--- Received command on {message.topic}: {payload}")

    # Example: {"zone_id": "zone-101", "set_temp": 22.5}
    for z in ZONES:
        if z["zone_id"] == payload.get("zone_id"):
            z["temp"] = payload.get("set_temp", z["temp"])
            print(f"--- Adjusted {z['zone_id']} temperature to {z['temp']}°C")

print("Connecting to AWS IoT Core...")
mqtt_client.connect()
print("---Connected---")

# Subscribe to all zone commands
command_topic = f"building/{BUILDING}/zone/+/command"
mqtt_client.subscribe(command_topic, 1, on_command)
print(f"--- Subscribed to {command_topic}")

# Publish telemetry periodically
try:
    while True:
        for z in ZONES:
            z["temp"] += random.uniform(-0.2, 0.2)
            z["hum"] += random.uniform(-1, 1)
            payload = {
                "building": BUILDING,
                "zone": z["zone_id"],
                "temperature": round(z["temp"], 2),
                "humidity": round(z["hum"], 1),
                "occupancy": random.choice([0, 1]),
                "ts": int(time.time())
            }
            topic = f"building/{BUILDING}/zone/{z['zone_id']}/telemetry"
            mqtt_client.publish(topic, json.dumps(payload), 1)
            print(f"--- Published -> {topic}: {payload}")
        time.sleep(SIM_INTERVAL)
except KeyboardInterrupt:
    print("--- Simulator stopped by user.")
    mqtt_client.disconnect()
