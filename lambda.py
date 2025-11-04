import json, boto3
import os
import numpy as np
import onnxruntime as rt
from decimal import Decimal
import base64

iot_data = boto3.client('iot-data', endpoint_url= os.environ.get("ENDPOINT_URL"))
dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table(os.environ["DYNAMO_IOT_TABLE"])
# ----------------------------
# Configuration
# ----------------------------
MODEL_PATH = os.path.join(os.path.dirname(__file__), "hvac_model.onnx")


fan_speed_map = {
    0: "low",
    1: "medium",
    2: "high"
}

# Cached variables
session = None


# To load model from local path
def load_models():
    global session
    print("Loading ONNX model from local path...")
    session = rt.InferenceSession(MODEL_PATH)
    print("Model loaded successfully.")


def lambda_handler(event, context):
    print("event received: ", event)
    for record in event["Records"]:
        payload = base64.b64decode(record["kinesis"]["data"])
        data = json.loads(payload)
        item = json.loads(json.dumps(data), parse_float=Decimal)
        table.put_item(Item=item)
        global session

        # Load once per cold start
        if session is None:
            load_models()

        
        temperature = float(data.get("temperature", 22))
        humidity = float(data.get("humidity", 50))
        occupancy = float(data.get("occupancy", 1))

        X = np.array([[temperature, humidity, occupancy]], dtype=np.float32)

        # Run inference 
        input_name = session.get_inputs()[0].name
        preds = session.run(None, {input_name: X})[0][0]

        set_temp_pred = float(preds[0])
        fan_speed_enc_pred = int(round(preds[1]))
        fan_speed_pred = fan_speed_map.get(fan_speed_enc_pred, "unknown")
        
        command_topic = f"building/{data['building']}/zone/{data['zone']}/command"
        payload = {"building": data["building"], "zone_id": data["zone"], "set_temp": round(set_temp_pred, 1), "fan_speed": fan_speed_pred}
        # send command back to the simulator
        iot_data.publish(topic=command_topic, qos=1, payload=json.dumps(payload))
        
        print("Done ...")
    return {"status": "sent"}
        

