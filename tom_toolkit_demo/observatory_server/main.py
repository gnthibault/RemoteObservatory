# Generic imports
from datetime import datetime, timedelta, timezone
from fastapi import FastAPI, Depends, HTTPException, Request, Response
from fastapi.responses import FileResponse, JSONResponse
from sqlalchemy import select, text
from sqlalchemy.exc import MultipleResultsFound
from sqlalchemy.orm import Session

#from sqlalchemy.dialects.mssql.information_schema import sequences
import uvicorn


# Local imports
from observatory_server.datamodel import (
    Base,
    DataProductType,
    Observation,
    ObservationOrm,
    ObservationStatus,
    PKTYPE_MODEL,
)
from observatory_server.db_utils import (
    engine,
    get_session,
    pk_hash
)

# -----------------------------
# FastAPI app
# -----------------------------
app = FastAPI()

################################################################################
# TODELETE
from fastapi.responses import FileResponse, JSONResponse
import os
import uuid
#from PIL import Image, ImageDraw, ImageFont
import asyncio

# Directory to store dynamically generated images
# It's good practice to use a temporary directory or a dedicated folder
# that can be cleaned up periodically.
TEMP_IMAGE_DIR = "temp_generated_images"


@app.get("/get_observation_data/{observation_id}")
def get_observation_data(observation_id: int, request: Request, db: Session = Depends(get_session)):
    """
    """
    # First, retrieve all files for a given observation

    base_url = str(request.base_url)   # e.g. "http://127.0.0.1:8888/"
    data_products = []
    unique_id = "UNIQUE_ID"
    file_name = "instrumental_response.fits"

    # for i in range(3):
    #     # Generate a unique filename to avoid collisions
    #     unique_id = uuid.uuid4()
    #     file_name = f"dynamic_image_{unique_id}.jpeg"
    #     file_path = os.path.join(TEMP_IMAGE_DIR, file_name)
    #
    #     # --- Dynamic Image Generation using Pillow ---
    #     try:
    #         # Create a new image with a dynamic background color
    #         img_size = (400, 300)
    #         bg_color = (50 + i * 30, 100 + i * 20, 150 + i * 10) # Changes per image
    #         img = Image.new('RGB', img_size, color=bg_color)
    #         draw = ImageDraw.Draw(img)
    #
    #         # Add dynamic text to the image
    #         text_color = (255, 255, 255) # White text
    #         try:
    #             # Try to load a default font, or use a generic one if not found
    #             font = ImageFont.truetype("arial.ttf", 30)
    #         except IOError:
    #             font = ImageFont.load_default()
    #
    #         text = f"Image {i+1} - {unique_id}"
    #         text_width, text_height = draw.textbbox((0,0), text, font=font)[2:] # Get text size
    #         text_x = (img_size[0] - text_width) / 2
    #         text_y = (img_size[1] - text_height) / 2
    #         draw.text((text_x, text_y), text, fill=text_color, font=font)
    #
    #         # Save the image as JPEG
    #         img.save(file_path, "JPEG")

    # Construct the URL for the generated file
    download_url = f"{base_url}/download/{file_name}"
    data_products.append({
        'id':str(unique_id),
        'url':download_url,
        "data_product_type": DataProductType.SPECTROSCOPY,
        'filename':file_name})

        # except Exception as e:
        #     print(f"Error generating image {i+1}: {e}")
        #     raise HTTPException(status_code=500, detail=f"Failed to generate image {i+1}")

    return JSONResponse(content={"data_products": data_products})

@app.get("/download/{filename}")
async def download_file(filename: str):
    """
    Serves a dynamically generated file by its filename.
    """
    file_path = os.path.join(TEMP_IMAGE_DIR, filename)
    # Basic security check: ensure the filename doesn't try to access parent directories
    if ".." in filename or filename.startswith("/"):
        raise HTTPException(status_code=400, detail="Invalid filename.")
    # Check if the file exists and is a JPEG
    if os.path.exists(file_path):
        return FileResponse(path=file_path, media_type="application/octet-stream", filename=filename)
    else:
        raise HTTPException(status_code=404, detail="File not found.")

# Optional: A simple cleanup mechanism for old files (for demonstration)
# In a production environment, consider a more robust background task or
# a dedicated file management service.
@app.on_event("startup") #Repace with lifespan
async def startup_event():
    print(f"Temporary image directory: {TEMP_IMAGE_DIR}")
    # You might want to clean up old files on startup or periodically
    # For simplicity, this example doesn't include automatic cleanup,
    # but it's crucial for production.
    os.makedirs(TEMP_IMAGE_DIR, exist_ok=True)


# TODELETE
from pydantic import BaseModel, ConfigDict
from typing import List, Optional, Dict, Any
# from sqlalchemy.orm import DeclarativeBase
#
# class Base(DeclarativeBase):
#     pass


# l = {
#     'target_id': 2,
#     'params': {
#         'cadence_strategy': '',
#         'facility': 'RemoteObservatory',
#         'target_id': 2,
#         'observation_type': 'default_field',
#         'exposure_time': 300,
#         'exposure_count': 43
#     }
# }

# class Item(Base):
#     __tablename__ = "items"
#
#     id = Column(Integer, primary_key=True, index=True)
#     name = Column(String, nullable=False)
#     description = Column(String, nullable=True)

# class ItemModel(BaseModel):
#     name: str
#     description: str | None = None

################################################################################
#def request_observation(observation: dict[Any, Any], db: Session = Depends(get_session)):
@app.post("/request_observation")
def request_observation(observation: Observation, db: Session = Depends(get_session)):
    # Observation(**observation)
    db_item = ObservationOrm(**observation.model_dump())
    db.add(db_item)
    db.commit()
    db.refresh(db_item)  # refresh to get autogenerated ID
    return db_item.to_dict()

@app.get("/get_observation_status/{observation_id}")
def get_observation_status(observation_id: int, db: Session = Depends(get_session)):
    stmt = (
        select(
            ObservationOrm.status,
            ObservationOrm.scheduled_start_at,
            ObservationOrm.scheduled_end_at,
        )
        .where(ObservationOrm.id == observation_id)
    )

    rows = db.execute(stmt).all()
    if not rows:
        raise HTTPException(status_code=404, detail="Observation not found")
    if len(rows) > 1:
        raise HTTPException(status_code=500, detail="Multiple observations found with same ID")
    row = rows[0]
    return {
        "state": row.status,
        "scheduled_start": row.scheduled_start_at,
        "scheduled_end": row.scheduled_end_at,
    }

@app.get("/cancel_observation/{observation_id}")
def cancel_observation(observation_id: int, db: Session = Depends(get_session)):
    # Try to fetch the observation
    observation = db.get(ObservationOrm, observation_id)
    if not observation:
        raise HTTPException(status_code=404, detail="Observation not found")
    # Update the status
    observation.status = ObservationStatus.CANCELED
    observation.updated_at = datetime.now(tz=timezone.utc)  # optional, if you track updates
    db.commit()
    db.refresh(observation)
    return {"id": observation.id, "status": observation.status}

# Run the server with uvicorn main:app --reload
# OR
if __name__ == "__main__":
    # Create the database tables
    # Base.metadata.drop_all(bind=engine)
    # Base.metadata.create_all(bind=engine)
    uvicorn.run(app, host="0.0.0.0", port=8888)


# from contextlib import asynccontextmanager
# @asynccontextmanager
# async def lifespan(app: FastAPI):
#     global db
#     # Startup
#     db = Session()   # init your db connection/session factory
#     yield
#     # Shutdown
#     db.close()
#
# app = FastAPI(lifespan=lifespan)
