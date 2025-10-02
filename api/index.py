from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
import numpy as np
import pandas as pd
import json
from pathlib import Path
from mangum import Mangum

app = FastAPI()

# Enable CORS for POST requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["POST"],
    allow_headers=["*"],
)

# Load telemetry JSON at startup
data_file = Path(__file__).parent / "q-vercel-latency.json"
with open(data_file) as f:
    telemetry = pd.DataFrame(json.load(f))

@app.post("/")
async def get_metrics(payload: dict):
    regions = payload.get("regions", [])
    threshold = payload.get("threshold_ms", 180)

    results = {}
    for region in regions:
        subset = telemetry[telemetry["region"] == region]
        if subset.empty:
            continue

        latencies = subset["latency_ms"].to_numpy()
        uptimes = subset["uptime_pct"].to_numpy()

        results[region] = {
            "avg_latency": float(latencies.mean()),
            "p95_latency": float(np.percentile(latencies, 95)),
            "avg_uptime": float(uptimes.mean()),
            "breaches": int((latencies > threshold).sum())
        }

    return results

# Expose for Vercel Lambda
handler = Mangum(app)
