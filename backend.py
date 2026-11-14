
"""
BUMI SHIFT 5.0
HANOVA | Sarawak Crop Decision Support

Backend services:
- NASA POWER recent climate observations
- NASA POWER ten-year historical climate
- Crop compatibility screening
- Crop rotation comparison
- Gemini-powered Ask BUMI
- FastAPI website hosting

This prototype produces screening indicators,
not guaranteed agricultural outcomes.
"""

import os
import math
import json
import logging

from pathlib import Path
from datetime import date, datetime, timedelta
from functools import lru_cache

import requests

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from google import genai

from climate_engine import get_historical_climate
from crop_engine import build_recommendations


# ============================================
# 1. CONFIGURATION
# ============================================

BASE_DIR = Path(__file__).resolve().parent

load_dotenv(BASE_DIR / ".env")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("BUMI_SHIFT")

app = FastAPI(
    title="BUMI SHIFT API",
    description=(
        "HANOVA NASA-powered crop rotation "
        "and environmental decision-support system"
    ),
    version="5.0"
)

# Same-origin hosting is used on Render.
# These origins support optional local development.
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://127.0.0.1:5500",
        "http://localhost:5500"
    ],
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"]
)

NASA_URL = (
    "https://power.larc.nasa.gov/"
    "api/temporal/daily/point"
)

DEFAULT_LATITUDE = 1.46
DEFAULT_LONGITUDE = 110.49

# Approximate Sarawak pilot bounding box.
# This is not an exact administrative boundary.
SARAWAK_LAT_MIN = 0.5
SARAWAK_LAT_MAX = 5.1
SARAWAK_LON_MIN = 109.5
SARAWAK_LON_MAX = 115.5

GEMINI_MODEL = os.getenv(
    "GEMINI_MODEL",
    "gemini-3.5-flash-lite"
)


# ============================================
# 2. INPUT MODEL
# ============================================

class FarmQuestion(BaseModel):

    question: str = Field(
        min_length=1,
        max_length=1000
    )

    latitude: float = Field(
        default=DEFAULT_LATITUDE,
        ge=-90,
        le=90
    )

    longitude: float = Field(
        default=DEFAULT_LONGITUDE,
        ge=-180,
        le=180
    )

    # Retained for compatibility with the
    # previous HTML interface.
    # Farmers are not required to supply these.
    drainage: str = Field(
        default="unknown",
        pattern="^(unknown|good|poor)$"
    )

    soil_ph: float | None = Field(
        default=None,
        ge=0,
        le=14
    )


# ============================================
# 3. LOCATION VALIDATION
# ============================================

def check_location(latitude, longitude):

    if not (
        SARAWAK_LAT_MIN <= latitude <= SARAWAK_LAT_MAX
        and SARAWAK_LON_MIN <= longitude <= SARAWAK_LON_MAX
    ):
        raise HTTPException(
            status_code=400,
            detail=(
                "This prototype currently supports "
                "the approximate Sarawak pilot region."
            )
        )


# ============================================
# 4. RECENT NASA POWER OBSERVATIONS
# ============================================

def fetch_nasa_data(latitude, longitude):

    check_location(latitude, longitude)

    end_date = date.today()
    start_date = end_date - timedelta(days=89)

    params = {
        "parameters": "PRECTOTCORR,T2M",
        "community": "AG",
        "latitude": latitude,
        "longitude": longitude,
        "start": start_date.strftime("%Y%m%d"),
        "end": end_date.strftime("%Y%m%d"),
        "format": "JSON",
        "time-standard": "UTC"
    }

    response = requests.get(
        NASA_URL,
        params=params,
        timeout=60
    )

    response.raise_for_status()

    payload = response.json()

    parameters = payload[
        "properties"
    ]["parameter"]

    rainfall = parameters["PRECTOTCORR"]
    temperature = parameters["T2M"]

    valid = []

    for day in sorted(
        set(rainfall) & set(temperature)
    ):

        rain = rainfall[day]
        temp = temperature[day]

        if not (
            isinstance(rain, (int, float))
            and not isinstance(rain, bool)
            and isinstance(temp, (int, float))
            and not isinstance(temp, bool)
            and math.isfinite(rain)
            and math.isfinite(temp)
            and rain >= 0
            and rain != -999
            and temp != -999
        ):
            continue

        valid.append({
            "date": day,
            "rainfall_mm": float(rain),
            "temperature_c": float(temp)
        })

    if not valid:
        raise ValueError(
            "NASA returned no valid paired observations."
        )

    latest_date = datetime.strptime(
        valid[-1]["date"],
        "%Y%m%d"
    ).date()

    window_start = latest_date - timedelta(days=6)

    recent = [
        row for row in valid
        if window_start <= datetime.strptime(
            row["date"],
            "%Y%m%d"
        ).date() <= latest_date
    ]

    complete_window = (
        len(recent) == 7
        and len({
            row["date"]
            for row in recent
        }) == 7
    )

    if complete_window:

        rainfall_total = round(
            sum(
                row["rainfall_mm"]
                for row in recent
            ),
            2
        )

        mean_temperature = round(
            sum(
                row["temperature_c"]
                for row in recent
            ) / 7,
            2
        )

    else:
        rainfall_total = None
        mean_temperature = None

    data_age_days = (
        date.today() - latest_date
    ).days

    return {
        "source": "NASA POWER Daily API",
        "source_url": NASA_URL,
        "location": "Selected coordinates",
        "latitude": latitude,
        "longitude": longitude,
        "latest_observation": str(latest_date),
        "data_age_days": data_age_days,
        "window_start": str(window_start),
        "window_end": str(latest_date),
        "recent_valid_days": len(recent),
        "rainfall_window_complete": complete_window,
        "recent_rainfall_mm": rainfall_total,
        "recent_mean_temperature_c": mean_temperature,
        "observations": recent,
        "data_note": (
            "NASA POWER provides gridded "
            "environmental estimates rather than "
            "direct measurements at individual farms."
        )
    }


# ============================================
# 5. CACHED HISTORICAL CLIMATE
# ============================================

# Coordinates are rounded for cache reuse.
# The cache is stored in server memory and
# disappears when Render restarts.
#
# A historical request can be slow.
# The first request is not cached.

@lru_cache(maxsize=64)
def cached_historical_climate(latitude, longitude):

    return get_historical_climate(
        latitude,
        longitude
    )


def historical_climate(latitude, longitude):

    check_location(latitude, longitude)

    return cached_historical_climate(
        round(latitude, 4),
        round(longitude, 4)
    )


# ============================================
# 6. HEALTH CHECK
# ============================================

@app.get("/")
def home():

    return {
        "message": "BUMI SHIFT API is running",
        "team": "HANOVA",
        "version": "5.0",
        "website": "/app",
        "endpoints": [
            "/nasa",
            "/climate/history",
            "/recommendations",
            "/ask"
        ]
    }


# ============================================
# 7. RECENT NASA ENDPOINT
# ============================================

@app.get("/nasa")
def get_nasa(
    latitude: float = Query(
        default=DEFAULT_LATITUDE,
        ge=-90,
        le=90
    ),
    longitude: float = Query(
        default=DEFAULT_LONGITUDE,
        ge=-180,
        le=180
    )
):

    try:
        return fetch_nasa_data(
            latitude,
            longitude
        )

    except HTTPException:
        raise

    except (
        requests.RequestException,
        ValueError,
        KeyError,
        TypeError
    ) as error:

        logger.warning(
            "NASA recent retrieval failed: %s",
            type(error).__name__
        )

        raise HTTPException(
            status_code=503,
            detail=(
                "Recent NASA observations are "
                "temporarily unavailable."
            )
        ) from error


# ============================================
# 8. HISTORICAL CLIMATE ENDPOINT
# ============================================

@app.get("/climate/history")
def climate_history(
    latitude: float = Query(
        default=DEFAULT_LATITUDE,
        ge=-90,
        le=90
    ),
    longitude: float = Query(
        default=DEFAULT_LONGITUDE,
        ge=-180,
        le=180
    )
):

    try:
        return historical_climate(
            latitude,
            longitude
        )

    except HTTPException:
        raise

    except (
        requests.RequestException,
        ValueError,
        KeyError,
        TypeError
    ) as error:

        logger.warning(
            "Historical climate retrieval failed: %s",
            type(error).__name__
        )

        raise HTTPException(
            status_code=503,
            detail=(
                "Historical NASA climate data "
                "are temporarily unavailable."
            )
        ) from error


# ============================================
# 9. CROP RECOMMENDATIONS ENDPOINT
# ============================================

@app.get("/recommendations")
def get_recommendations(
    latitude: float = Query(
        default=DEFAULT_LATITUDE,
        ge=-90,
        le=90
    ),
    longitude: float = Query(
        default=DEFAULT_LONGITUDE,
        ge=-180,
        le=180
    )
):

    try:

        history = historical_climate(
            latitude,
            longitude
        )

        return build_recommendations(
            latitude,
            longitude,
            history
        )

    except HTTPException:
        raise

    except (
        requests.RequestException,
        ValueError,
        KeyError,
        TypeError
    ) as error:

        logger.warning(
            "Crop recommendation failed: %s",
            type(error).__name__
        )

        raise HTTPException(
            status_code=503,
            detail=(
                "Crop recommendations are "
                "temporarily unavailable."
            )
        ) from error


# ============================================
# 10. ASK BUMI — GEMINI AI
# ============================================

@app.post("/ask")
def ask_bumi(farm: FarmQuestion):

    if not os.getenv("GEMINI_API_KEY"):
        raise HTTPException(
            status_code=503,
            detail="Gemini API key is missing."
        )

    try:

        nasa = fetch_nasa_data(
            farm.latitude,
            farm.longitude
        )

    except HTTPException:
        raise

    except (
        requests.RequestException,
        ValueError,
        KeyError,
        TypeError
    ) as error:

        logger.warning(
            "NASA data unavailable for Ask BUMI: %s",
            type(error).__name__
        )

        raise HTTPException(
            status_code=503,
            detail=(
                "NASA observations are unavailable. "
                "BUMI cannot assess recent conditions."
            )
        ) from error

    evidence = {
        "recent_nasa": nasa,
        "farmer_reported_drainage": farm.drainage,
        "farmer_provided_soil_ph": farm.soil_ph
    }

    instructions = """
    You are BUMI, a friendly agricultural
    evidence assistant developed by HANOVA
    for Sarawak farmers.

    Explain the supplied NASA POWER observations
    using understandable language.

    Scientific rules:

    1. Use only supplied numerical observations.

    2. Identify the latest observation date.

    3. Distinguish NASA gridded estimates
       from direct farm measurements.

    4. Never invent rainfall, soil properties,
       crop yields or profits.

    5. Do not claim historical observations
       are future weather forecasts.

    6. Do not guarantee crop suitability.

    7. If seven-day observations are incomplete,
       do not report a seven-day rainfall total.

    8. Explain uncertainty and missing evidence.

    9. Answer in the farmer's language.

    10. Keep explanations practical and clear.
    """

    try:

        client = genai.Client(
            api_key=os.environ["GEMINI_API_KEY"]
        )

        response = client.models.generate_content(
            model=GEMINI_MODEL,
            contents=(
                instructions
                + "\n\nFarmer question:\n"
                + farm.question
                + "\n\nEnvironmental evidence:\n"
                + json.dumps(
                    evidence,
                    ensure_ascii=False
                )
            )
        )

        answer = response.text

        if not answer:
            raise ValueError(
                "Gemini returned an empty response."
            )

    except Exception as error:

        logger.warning(
            "Gemini request failed: %s",
            type(error).__name__
        )

        raise HTTPException(
            status_code=503,
            detail=(
                "Gemini is temporarily unavailable. "
                "Please try again later."
            )
        ) from error

    return {
        "answer": answer,
        "evidence": nasa
    }


# ============================================
# 11. WEBSITE HOSTING
# ============================================

STATIC_DIR = BASE_DIR / "static"

if STATIC_DIR.is_dir():

    app.mount(
        "/static",
        StaticFiles(directory=STATIC_DIR),
        name="static"
    )

    @app.get("/app")
    def serve_website():

        html_file = STATIC_DIR / "index.html"

        if not html_file.is_file():
            raise HTTPException(
                status_code=404,
                detail="Website index.html not found."
            )

        return FileResponse(html_file)

else:

    logger.warning(
        "Static folder not found. "
        "Website route is unavailable."
    )
