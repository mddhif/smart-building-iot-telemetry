import os
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import LabelEncoder
from sklearn.multioutput import MultiOutputRegressor
from influxdb_client import InfluxDBClient
import random
import joblib
from skl2onnx import convert_sklearn
from skl2onnx.common.data_types import FloatTensorType


INFLUX_URL = os.getenv("INFLUX_URL")
INFLUX_TOKEN = os.getenv("INFLUX_TOKEN")
INFLUX_ORG = os.getenv("ORG")
INFLUX_BUCKET = os.getenv("BUCKET")

client = InfluxDBClient(url=INFLUX_URL, token=INFLUX_TOKEN, org=INFLUX_ORG)
query_api = client.query_api()

def train_model():
    query = f'''
    from(bucket: "{INFLUX_BUCKET}")
      |> range(start: -7d)
      |> filter(fn: (r) => r._measurement == "telemetry")
      |> pivot(rowKey:["_time"], columnKey: ["_field"], valueColumn: "_value")
      |> keep(columns: ["temperature", "humidity", "occupancy"])
    '''
    tables = query_api.query(query)
    data = []

    for table in tables:
        for record in table.records:
            row = {
                "temperature": record["temperature"],
                "humidity": record["humidity"],
                "occupancy": int(record["occupancy"] or 0),
                "set_temp": round(22 + (21 - record["temperature"]) * 0.5),
                "fan_speed": random.choice(["low", "medium", "high"])
            }
            data.append(row)

    if not data:
        data = [
            {"temperature": 22.3, "humidity": 47.1, "occupancy": 1, "set_temp": 22, "fan_speed": "medium"},
            {"temperature": 24.0, "humidity": 50.2, "occupancy": 0, "set_temp": 23, "fan_speed": "high"},
        ]

    df = pd.DataFrame(data)
    le = LabelEncoder()
    df["fan_speed_enc"] = le.fit_transform(df["fan_speed"])

    X = df[["temperature", "humidity", "occupancy"]]
    y = df[["set_temp", "fan_speed_enc"]]

    model = MultiOutputRegressor(RandomForestRegressor(n_estimators=100, random_state=42))
    model.fit(X, y)

    # Save the encoder
    joblib.dump(le, "fan_speed_le.pkl")

    # Export to ONNX
    initial_type = [('float_input', FloatTensorType([None, 3]))]
    onnx_model = convert_sklearn(model, initial_types=initial_type)
    with open("hvac_model.onnx", "wb") as f:
        f.write(onnx_model.SerializeToString())

    print("ONNX model and label encoder saved!")


if __name__ == "__main__":
    train_model()
