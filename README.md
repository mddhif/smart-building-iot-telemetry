# Smart Building IoT Telemetry Pipeline (AWS + InfluxDB + ONNX)

This project showcases an **IoT telemetry pipeline** for smart building environments, built with **AWS IoT Core**, **Kinesis**, **Lambda**, **DynamoDB**, and **InfluxDB**.
It demonstrates how to collect, process, predict, and visualize sensor data from multiple building zones using an **end-to-end cloud-to-edge architecture**.

---

##  System Overview

###  Data Flow



---

##  Key Components

| Component | Description |
|------------|--------------|
| **Simulator** | Publishes telemetry data (`temperature`, `humidity`, `occupancy`) to AWS IoT Core MQTT topics like `building/{id}/zone/{id}/telemetry`. |
| **AWS IoT Core** | Central IoT hub that routes telemetry to multiple destinations (S3, Kinesis, Lambda). |
| **AWS Kinesis** | Streams real-time telemetry events for downstream analytics and Lambda processing. |
| **AWS Lambda** | Performs ONNX-based inference to predict `set_temp` and `fan_speed`, then stores data in DynamoDB and publishes commands back to devices. |
| **DynamoDB** | NoSQL database storing structured telemetry and prediction results. |
| **InfluxDB (Local)** | Time-series database for visualizing telemetry trends in real time. |
| **CloudWatch** | Observability layer for monitoring Lambda executions and IoT Core metrics. |
| **S3 + Athena + Glue** | Data lake and query layer for long-term telemetry analysis. |

---

##  AWS Architecture Diagram





---

##  Data Model Example

### Telemetry Message

```json
{
  "building": "building1",
  "zone": "zone-103",
  "temperature": 22.5,
  "humidity": 45.1,
  "occupancy": 1,
  "ts": 1762179569
}
```

### Predicted command 

```json
{
  "building": "building1",
  "zone": "zone-103",
  "set_temp": 21.5,
  "fan_speed": 3
}


```



##  Visualization & Analytics

###  Real-Time

- **InfluxDB UI** – Used locally to visualize telemetry streams such as **temperature**, **humidity**, and **occupancy**.

---

### Historical

- **Amazon S3 (Data Lake)** – Stores raw telemetry JSON files streamed from IoT Core.
- **Amazon Athena + AWS Glue** – Enables SQL-based querying and aggregation over historical telemetry data for analytics and reporting.
- **Amazon CloudWatch Logs Insights** – Analyze Lambda execution logs, detect anomalies, and troubleshoot issues using queries such as:

  ```sql
  fields @timestamp, @message
  | filter @message like /ERROR/
  | sort @timestamp desc
  | limit 20
