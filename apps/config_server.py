from fastapi import FastAPI, Query, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel
from enum import Enum
import uuid
import os
import zipfile

app = FastAPI()

# Define the ObservationStatus Enum
class ObservationStatus(str, Enum):
    posted      = "posted"
    scheduling  = "scheduling"
    acquiring   = "acquiring"
    calibrating = "calibrating"
    ready       = "ready"

# Define the request schema
class ObservationRequest(BaseModel):
    target: str
    exposure_time: float
    exposure_count: float

# Simple in-memory stores
observations = {}
statuses = {}

@app.post("/add_observation")
def add_observation(obs: ObservationRequest):
    observation_id = str(uuid.uuid4())
    observations[observation_id] = obs
    statuses[observation_id] = ObservationStatus.posted
    return {"observation_id": observation_id}

@app.get("/get_observation_status/{observation_id}")
def get_observation_status(observation_id: str):
    status = statuses.get(observation_id)
    if status is None:
        raise HTTPException(status_code=404, detail="Observation ID not found")
    return {"status": status}

@app.get("/get_observation_data/{observation_id}")
def get_observation_data(observation_id: str):
    if observation_id not in observations:
        raise HTTPException(status_code=404, detail="Observation ID not found")

    # Create a dummy zip file
    zip_filename = f"{observation_id}.zip"
    dummy_file = f"{observation_id}.txt"

    with open(dummy_file, "w") as f:
        f.write("Dummy observation data")

    with zipfile.ZipFile(zip_filename, "w") as zipf:
        zipf.write(dummy_file)

    # Cleanup dummy file after zipping
    os.remove(dummy_file)

    # Send the zip file
    return FileResponse(
        path=zip_filename,
        filename=zip_filename,
        media_type='application/zip'
    )


# pip install fastapi uvicorn
# uvicorn config_server:app --reload