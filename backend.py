
import os
import math
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
        "HANOVA NASA-powered agricultural "
        "exploration and AI platform"
    ),
    version="5.0"
)

# Local development origins.
# When deployed, HTML and API share one origin.
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

# Default demonstration location near Samarahan.
DEFAULT_LATITUDE = 1.46
DEFAULT_LONGITUDE = 110.49

# Approximate pilot-region bounding box.
# This is NOT an exact Sarawak boundary.
SARAWAK_LAT_MIN = 0.5
SARAWAK_LAT_MAX = 5.1
SARAWAK_LON_MIN = 109.5
SARAWAK_LON_MAX = 115.5

GEMINI_MODEL = os.getenv(
    "GEMINI_MODEL",
    "gemini-3.5-flash-lite"
)


# ============================================
# 2. DATA MODELS
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
# 4. NASA POWER DATA RETRIEVAL
# ============================================

def fetch_nasa_data(latitude, longitude):

    check_location(latitude, longitude)

    # NASA POWER daily observations can lag
    # behind today's date.
    #
    # Request 90 calendar days, then identify
    # the latest valid observation.

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

    parameters = payload["properties"]["parameter"]

    rainfall = parameters["PRECTOTCORR"]
    temperature = parameters["T2M"]

    valid = []

    for day in sorted(
        set(rainfall) & set(temperature)
    ):

        rain = rainfall[day]
        temp = temperature[day]

        # Reject missing or invalid values.
        if not (
            isinstance(rain, (int, float))
            and isinstance(temp, (int, float))
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

    # ========================================
    # 5. SEVEN-DAY DATA VALIDATION
    # ========================================

    latest_date = datetime.strptime(
        valid[-1]["date"],
        "%Y%m%d"
    ).date()

    window_start = latest_date - timedelta(days=6)

    recent = [
        row for row in valid
        if window_start <= datetime.strptime(
            row["date"], "%Y%m%d"
        ).date() <= latest_date
    ]

    complete_window = (
        len(recent) == 7
        and len({
            row["date"] for row in recent
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
            "direct measurements at a farm."
        )
    }


# ============================================
# 6. HEALTH CHECK
# ============================================

@app.get("/")
def home():

    return {
        "message": "BUMI SHIFT API is running",
        "team": "HANOVA",
        "version": "5.0",
        "website": "/app"
    }


# ============================================
# 7. NASA ENDPOINT
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
            "NASA retrieval failed: %s",
            type(error).__name__
        )

        raise HTTPException(
            status_code=503,
            detail=(
                "NASA observations are unavailable. "
                "No historical fallback was substituted."
            )
        ) from error


# ============================================
# 8. GEMINI AI — ASK BUMI
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

        raise HTTPException(
            status_code=503,
            detail=(
                "NASA observations are unavailable. "
                "BUMI cannot provide a current-data "
                "assessment."
            )
        ) from error

    evidence = {
        "nasa": nasa,
        "farmer_reported_drainage": farm.drainage,
        "farmer_provided_soil_ph": farm.soil_ph
    }

    instructions = """
    You are BUMI, an agricultural evidence
    assistant developed by HANOVA for Sarawak.

    Explain the supplied NASA POWER observations
    and farmer-reported field information.

    Scientific requirements:

    1. Use only supplied numerical observations.

    2. Always identify the latest observation date.

    3. Distinguish NASA gridded estimates
       from actual farm measurements.

    4. Never invent rainfall, soil pH, crop yields,
       soil nutrients, flooding or crop requirements.

    5. If the seven-day window is incomplete,
       do not report a seven-day rainfall total.

    6. Explain when environmental observations
       are outdated or incomplete.

    7. Farmer drainage and soil information
       are self-reported.

    8. Never guarantee crop suitability,
       crop growth or future yields.

    9. Identify missing agricultural evidence.

    10. Answer in the farmer's language.

    11. Use clear and understandable language.

    12. Do not claim NASA POWER observations
        are real-time farm measurements.
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
                + "\n\nNASA evidence and farm inputs:\n"
                + str(evidence)
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
                "Gemini is currently unavailable. "
                "Please try again later."
            )
        ) from error

    return {
        "answer": answer,
        "evidence": nasa,
        "farm_context": {
            "latitude": farm.latitude,
            "longitude": farm.longitude,
            "drainage": farm.drainage,
            "soil_ph": farm.soil_ph
        }
    }


# ============================================
# HISTORICAL NASA CLIMATE ENDPOINT
# ============================================

@app.get("/climate/history")
def climate_history(
    latitude: float = Query(default=DEFAULT_LATITUDE, ge=-90, le=90),
    longitude: float = Query(default=DEFAULT_LONGITUDE, ge=-180, le=180)
):
    check_location(latitude, longitude)
    try:
        return get_historical_climate(latitude, longitude)
    except (requests.RequestException, ValueError, KeyError, TypeError) as error:
        logger.warning("Historical NASA retrieval failed: %s", type(error).__name__)
        raise HTTPException(
            status_code=503,
            detail="Historical NASA climate data are currently unavailable."
        ) from error


# ============================================
# CROP AND ROTATION RECOMMENDATIONS
# ============================================

@app.get("/recommendations")
def recommendations(
    latitude: float = Query(default=DEFAULT_LATITUDE, ge=-90, le=90),
    longitude: float = Query(default=DEFAULT_LONGITUDE, ge=-180, le=180)
):
    check_location(latitude, longitude)
    try:
        history = get_historical_climate(latitude, longitude)
        return build_recommendations(latitude, longitude, history)
    except (requests.RequestException, ValueError, KeyError, TypeError) as error:
        logger.warning("Recommendations failed: %s", type(error).__name__)
        raise HTTPException(status_code=503, detail="Climate-based recommendations are temporarily unavailable.") from error


# ============================================
# 9. WEBSITE HOSTING
# ============================================

STATIC_DIR = BASE_DIR / "static"

# The static folder must exist and contain
# the website's index.html.
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
        "Website route will be unavailable."
    )
