"""
Live HTTP Verification for Environmental Anomaly V2 Endpoints.
Queries http://127.0.0.1:8000 to verify routes and live MEAD-V2 model inference.
"""
import urllib.request
import json

base = "http://127.0.0.1:8000"

# 1. OpenAPI check
print("=== 1. OPENAPI VERIFICATION ===")
req = urllib.request.urlopen(f"{base}/openapi.json")
schema = json.loads(req.read().decode())
paths = sorted(schema.get("paths", {}).keys())
for ep in [
    "/api/v1/ml/anomalies",
    "/api/v1/ml/anomalies/detect",
    "/api/v1/ml/environmental-anomaly/model-info",
    "/api/v1/ml/environmental-anomaly/health"
]:
    print(f"  {ep} present: {ep in paths}")

# 2. GET /api/v1/ml/anomalies
print("\n=== 2. GET /api/v1/ml/anomalies ===")
req = urllib.request.urlopen(f"{base}/api/v1/ml/anomalies")
data = json.loads(req.read().decode())
items = data.get("data", [])
print(f"  Status: {req.status}, Count: {len(items)}")
for item in items:
    print(f"  - [{item.get('id')}] {item.get('region')} | Score: {item.get('anomalyScore')} | Baseline: {item.get('baselineExpectedValue')} | Observed: {item.get('observedCurrentValue')} | AnomalyType: {item.get('anomalyType')}")

# 3. POST /api/v1/ml/anomalies/detect
print("\n=== 3. POST /api/v1/ml/anomalies/detect ===")
payload = json.dumps({
    "latitude": 15.0,
    "longitude": 65.0,
    "sst": 31.5,
    "timestamp": "2025-06-01"
}).encode("utf-8")
req_post = urllib.request.Request(
    f"{base}/api/v1/ml/anomalies/detect",
    data=payload,
    headers={"Content-Type": "application/json"}
)
res_post = urllib.request.urlopen(req_post)
detect_data = json.loads(res_post.read().decode())
res_obj = detect_data.get("data", {})
print(f"  Status: {res_post.status}")
print(f"  Live Result ID: {res_obj.get('id')}")
print(f"  Region: {res_obj.get('region')}")
print(f"  Anomaly Score: {res_obj.get('anomalyScore')}")
print(f"  Baseline SST: {res_obj.get('baselineExpectedValue')}")
print(f"  Observed SST: {res_obj.get('observedCurrentValue')}")
print(f"  SST Deviation: {res_obj.get('sst_anomaly_celsius')} °C")
print(f"  Direction: {res_obj.get('warm_cold_direction')}")
print(f"  In Arabian Sea: {res_obj.get('in_arabian_sea')}")
print(f"  Severity: {res_obj.get('severity')}")
print(f"  Mitigation Advice: {res_obj.get('mitigationAdvice')}")

# 4. Model info & Health
print("\n=== 4. MODEL INFO & HEALTH ===")
info_res = urllib.request.urlopen(f"{base}/api/v1/ml/environmental-anomaly/model-info")
print(f"  Model info status: {info_res.status}")
info_data = json.loads(info_res.read().decode()).get("data", {})
print(f"  Model Name: {info_data.get('model_name')}")
print(f"  Model Version: {info_data.get('model_version')}")
print(f"  Algorithm: {info_data.get('algorithm')}")

health_res = urllib.request.urlopen(f"{base}/api/v1/ml/environmental-anomaly/health")
print(f"  Health status: {health_res.status}")
print(f"  Health body: {health_res.read().decode()}")
