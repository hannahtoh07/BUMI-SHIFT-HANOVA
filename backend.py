
"""
BUMI SHIFT 7.0
Backend API | HANOVA | Sarawak, Malaysia

Purpose:
- Serve the BUMI SHIFT website
- Retrieve NASA POWER historical climate data
- Generate crop recommendations
- Support all 11 preferred crop choices
- Accept optional farmer-reported drainage
- Connect personalized farming strategies
- Preserve compatibility with existing engines
- Remove unused Gemini functionality

Scientific principles:
- NASA historical observations are not forecasts.
- Climate compatibility scores are provisional.
- Farmer-reported drainage is not satellite-measured.
- Economic feasibility requires independent evidence.
"""

import logging
import math
import inspect

from pathlib import Path
from functools import lru_cache

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from climate_engine import get_historical_climate
from crop_engine import build_recommendations, CROPS
from strategy_engine import enrich


# ============================================
# 1. APPLICATION SETUP
# ============================================

ROOT = Path(__file__).resolve().parent

logging.basicConfig(level=logging.INFO)

logger = logging.getLogger("bumi_shift")

app = FastAPI(
    title="BUMI SHIFT",
    version="7.0",
    description=(
        "NASA-powered crop and farming-shift "
        "decision-support system for Sarawak."
    )
)

app.mount(
    "/static",
    StaticFiles(
        directory=ROOT / "static"
    ),
    name="static"
)


# ============================================
# 2. SUPPORTED FARM SETTINGS
# ============================================

PRIORITIES = {
    "soil",
    "water",
    "resilience",
    "income"
}

# All 11 crops are available as preferred crops.
ALL_CROPS = set(CROPS.keys())

# Current crop selections remain compatible
# with the existing annual rotation engine.
BASELINES = {
    "rice",
    "maize",
    "mung_bean",
    "groundnut",
    "soybean",
    "sweet_potato"
}

DRAINAGE_OPTIONS = {
    "unknown",
    "poor",
    "moderate",
    "good"
}

SARAWAK_BOUNDS = {
    "min_latitude": 0.5,
    "max_latitude": 5.1,
    "min_longitude": 109.5,
    "max_longitude": 115.5
}


# ============================================
# 3. INPUT VALIDATION
# ============================================

def validate_coordinates(latitude, longitude):

    if not (
        math.isfinite(latitude)
        and math.isfinite(longitude)
    ):
        raise HTTPException(
            status_code=422,
            detail={
                "code": "INVALID_COORDINATES",
                "message": "Coordinates must be finite."
            }
        )

    bounds = SARAWAK_BOUNDS

    valid_location = (
        bounds["min_latitude"]
        <= latitude
        <= bounds["max_latitude"]
        and
        bounds["min_longitude"]
        <= longitude
        <= bounds["max_longitude"]
    )

    if not valid_location:
        raise HTTPException(
            status_code=422,
            detail={
                "code": "INVALID_LOCATION",
                "message": (
                    "Please select a location "
                    "within the Sarawak pilot area."
                )
            }
        )


def validate_settings(
    priority,
    baseline,
    preferred_crop,
    drainage
):

    if priority not in PRIORITIES:
        raise HTTPException(
            status_code=422,
            detail={
                "code": "INVALID_PRIORITY",
                "allowed": sorted(PRIORITIES)
            }
        )

    if baseline not in BASELINES:
        raise HTTPException(
            status_code=422,
            detail={
                "code": "INVALID_BASELINE",
                "allowed": sorted(BASELINES)
            }
        )

    if (
        preferred_crop != "auto"
        and preferred_crop not in ALL_CROPS
    ):
        raise HTTPException(
            status_code=422,
            detail={
                "code": "INVALID_PREFERRED_CROP",
                "allowed": (
                    ["auto"] + sorted(ALL_CROPS)
                )
            }
        )

    if drainage not in DRAINAGE_OPTIONS:
        raise HTTPException(
            status_code=422,
            detail={
                "code": "INVALID_DRAINAGE",
                "allowed": sorted(DRAINAGE_OPTIONS)
            }
        )


# ============================================
# 4. CACHED NASA CLIMATE DATA
# ============================================

@lru_cache(maxsize=80)
def cached_climate(latitude, longitude):

    return get_historical_climate(
        latitude,
        longitude
    )


# ============================================
# 5. FARM ASSESSMENT
# ============================================

@lru_cache(maxsize=160)
def assess(
    latitude,
    longitude,
    priority,
    baseline,
    preferred_crop="auto",
    drainage="unknown"
):
    """
    Build a farm assessment.

    During the staged upgrade, this function
    supports the existing four-argument
    strategy engine.

    Once strategy_engine.enrich accepts
    preferred_crop and drainage, these
    inputs are forwarded automatically.

    The response explicitly reports whether
    the strategy engine processed them.
    """

    climate = cached_climate(
        latitude,
        longitude
    )

    crops = build_recommendations(
        latitude,
        longitude,
        climate
    )

    # Determine which optional arguments the
    # installed strategy engine supports.
    signature = inspect.signature(enrich)
    parameters = signature.parameters

    supports_kwargs = any(
        p.kind == inspect.Parameter.VAR_KEYWORD
        for p in parameters.values()
    )

    optional_arguments = {}

    if (
        "preferred_crop" in parameters
        or supports_kwargs
    ):
        optional_arguments["preferred_crop"] = (
            preferred_crop
        )

    if (
        "drainage" in parameters
        or supports_kwargs
    ):
        optional_arguments["drainage"] = drainage

    result = enrich(
        crops,
        climate,
        priority,
        baseline,
        **optional_arguments
    )

    if not isinstance(result, dict):
        raise ValueError(
            "Strategy engine must return a dictionary."
        )

    # Avoid mutating an object owned by another
    # cached or shared component.
    result = dict(result)

    preferred_processed = (
        "preferred_crop" in optional_arguments
    )

    drainage_processed = (
        "drainage" in optional_arguments
    )

    # Preserve the original response fields.
    # Add metadata for the new frontend.
    result["farmer_inputs"] = {
        "latitude": latitude,
        "longitude": longitude,
        "priority": priority,
        "baseline": baseline,
        "preferred_crop": preferred_crop,
        "drainage": drainage
    }

    result["personalization"] = {
        "preferred_crop_processed": (
            preferred_processed
        ),
        "drainage_processed": (
            drainage_processed
        ),
        "strategy_engine_ready": (
            preferred_processed
            and drainage_processed
        )
    }

    result["available_crops"] = [
        {
            "id": crop_id,
            "name": crop["name"],
            "family": crop["family"],
            "kind": crop["kind"],
            "approx_duration_months": (
                crop["months"]
            )
        }
        for crop_id, crop in CROPS.items()
    ]

    result["data_sources"] = {
        "environmental": {
            "name": "NASA POWER",
            "url": (
                "https://power.larc.nasa.gov/"
            ),
            "type": (
                "Historical gridded "
                "environmental estimates"
            )
        },
        "crop_screening": {
            "name": (
                "BUMI SHIFT prototype "
                "crop screening model"
            ),
            "type": (
                "Experimental crop thresholds "
                "and compatibility calculations"
            )
        }
    }

    return result


# ============================================
# 6. SERVICE STATUS
# ============================================

@app.get("/")
def home():

    return {
        "status": "running",
        "name": "BUMI SHIFT",
        "version": "7.0",
        "website": "/app",
        "api": {
            "climate": "/climate/history",
            "recommendations": "/recommendations",
            "crops": "/crops",
            "health": "/health"
        }
    }


@app.get("/health")
def health():

    return {
        "status": "ok",
        "version": "7.0",
        "crop_count": len(CROPS),
        "gemini_required": False
    }


# ============================================
# 7. WEBSITE
# ============================================

@app.get("/app")
def website():

    index_file = (
        ROOT / "static" / "index.html"
    )

    if not index_file.is_file():
        raise HTTPException(
            status_code=404,
            detail={
                "code": "WEBSITE_NOT_FOUND"
            }
        )

    return FileResponse(
        index_file,
        media_type="text/html"
    )


# ============================================
# 8. CROP LIBRARY
# ============================================

@app.get("/crops")
def get_crops():

    return {
        "count": len(CROPS),
        "crops": [
            {
                "id": crop_id,
                "name": crop["name"],
                "family": crop["family"],
                "kind": crop["kind"],
                "approx_duration_months": (
                    crop["months"]
                ),
                "thresholds": {
                    "monthly_rainfall_mm": (
                        list(crop["rain"])
                    ),
                    "mean_temperature_c": (
                        list(crop["temp"])
                    )
                }
            }
            for crop_id, crop in CROPS.items()
        ],
        "note": (
            "Crop thresholds are provisional "
            "screening assumptions."
        )
    }


# ============================================
# 9. NASA CLIMATE ENDPOINT
# ============================================

@app.get("/climate/history")
def climate_history(
    latitude: float = Query(
        default=1.46,
        ge=-90,
        le=90
    ),
    longitude: float = Query(
        default=110.49,
        ge=-180,
        le=180
    )
):

    validate_coordinates(
        latitude,
        longitude
    )

    try:
        return cached_climate(
            round(latitude, 4),
            round(longitude, 4)
        )

    except Exception as exc:

        logger.exception(
            "NASA climate request failed"
        )

        raise HTTPException(
            status_code=503,
            detail={
                "code": "CLIMATE_REQUEST_FAILED",
                "message": (
                    "Historical climate data "
                    "could not be retrieved."
                )
            }
        ) from exc


# ============================================
# 10. PERSONALIZED RECOMMENDATIONS
# ============================================

@app.get("/recommendations")
def recommendations(
    latitude: float = Query(
        default=1.46,
        ge=-90,
        le=90
    ),
    longitude: float = Query(
        default=110.49,
        ge=-180,
        le=180
    ),
    priority: str = "soil",
    baseline: str = "rice",
    preferred_crop: str = "auto",
    drainage: str = "unknown"
):

    validate_coordinates(
        latitude,
        longitude
    )

    validate_settings(
        priority,
        baseline,
        preferred_crop,
        drainage
    )

    try:

        return assess(
            round(latitude, 4),
            round(longitude, 4),
            priority,
            baseline,
            preferred_crop,
            drainage
        )

    except HTTPException:
        raise

    except Exception as exc:

        logger.exception(
            "Farm assessment failed"
        )

        raise HTTPException(
            status_code=503,
            detail={
                "code": "ASSESSMENT_REQUEST_FAILED",
                "message": (
                    "The farm assessment "
                    "could not be completed."
                )
            }
        ) from exc


# ============================================
# 11. MARKET DATA SOURCES
# ============================================

@app.get("/market/sources")
def market_sources():
    """
    Official reference directory.

    This endpoint does not claim that
    live market prices have been retrieved.
    """

    return {
        "region": "Sarawak, Malaysia",
        "sources": [
            {
                "name": (
                    "Department of Statistics "
                    "Malaysia"
                ),
                "short_name": "DOSM",
                "url": (
                    "https://open.dosm.gov.my/"
                ),
                "purpose": (
                    "Official agricultural "
                    "production and area statistics"
                )
            },
            {
                "name": (
                    "Sarawak Government "
                    "Open Data"
                ),
                "short_name": "Sarawak Open Data",
                "url": (
                    "https://data.sarawak.gov.my/"
                ),
                "purpose": (
                    "Regional agricultural "
                    "statistics and publications"
                )
            },
            {
                "name": (
                    "Federal Agricultural "
                    "Marketing Authority"
                ),
                "short_name": "FAMA",
                "url": (
                    "https://ami.fama.gov.my/"
                ),
                "purpose": (
                    "Agricultural market-price "
                    "references"
                )
            }
        ],
        "price_data_integrated": False,
        "note": (
            "Market prices and production "
            "statistics must be verified "
            "before numerical display."
        )
    }


# ============================================
# 12. CACHE MANAGEMENT
# ============================================

@app.post("/admin/cache/clear")
def clear_cache():
    """
    Cache clearing is intentionally disabled
    over the public API.

    Restarting the Render service clears
    the current in-memory caches.

    Do not expose an unauthenticated
    administrative cache-clear endpoint.
    """

    raise HTTPException(
        status_code=403,
        detail={
            "code": "ADMIN_ACTION_DISABLED"
        }
    )
