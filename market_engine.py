
"""
BUMI SHIFT 7.1
Integrated FastAPI Backend
HANOVA | Sarawak, Malaysia

Main functions:
- NASA POWER historical climate retrieval
- All 11 crop recommendations
- Personalized crop and rotation assessment
- Preferred crop and farmer-reported drainage
- Market and local agricultural insights
- 3D farming scenario data
- Official source attribution

No Gemini dependency.

Scientific limitations:
- Historical NASA observations are not forecasts.
- Crop compatibility indices are provisional.
- Drainage is farmer-reported, not measured.
- Soil-health benefits are not predicted.
- Market information is not a profitability forecast.
"""

import copy
import logging
import math

from pathlib import Path
from functools import lru_cache

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from climate_engine import get_historical_climate
from crop_engine import build_recommendations, CROPS
from strategy_engine import enrich

from market_engine import (
    build_market_assessment,
    get_crop_market_profile,
    get_all_crop_market_profiles,
    get_sources,
    market_data_status
)


# ============================================
# 1. APPLICATION CONFIGURATION
# ============================================

ROOT = Path(__file__).resolve().parent

logging.basicConfig(level=logging.INFO)

logger = logging.getLogger("bumi_shift")

app = FastAPI(
    title="BUMI SHIFT",
    version="7.1",
    description=(
        "NASA-powered agricultural decision-support "
        "platform for Sarawak, Malaysia."
    )
)

STATIC_DIR = ROOT / "static"

STATIC_DIR.mkdir(
    parents=True,
    exist_ok=True
)

app.mount(
    "/static",
    StaticFiles(directory=STATIC_DIR),
    name="static"
)


# ============================================
# 2. FARM SETTINGS
# ============================================

PRIORITIES = {
    "soil",
    "water",
    "resilience",
    "income"
}

ALL_CROPS = set(CROPS.keys())

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
    "min_lat": 0.5,
    "max_lat": 5.1,
    "min_lon": 109.5,
    "max_lon": 115.5
}


# ============================================
# 3. INPUT VALIDATION
# ============================================

def validate_location(latitude, longitude):

    if not (
        math.isfinite(latitude)
        and math.isfinite(longitude)
    ):
        raise HTTPException(
            status_code=422,
            detail={
                "code": "INVALID_COORDINATES"
            }
        )

    b = SARAWAK_BOUNDS

    if not (
        b["min_lat"] <= latitude <= b["max_lat"]
        and
        b["min_lon"] <= longitude <= b["max_lon"]
    ):
        raise HTTPException(
            status_code=422,
            detail={
                "code": "INVALID_LOCATION",
                "message": (
                    "Select a location within "
                    "the Sarawak pilot area."
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
                "code": "INVALID_PRIORITY"
            }
        )

    if baseline not in BASELINES:
        raise HTTPException(
            status_code=422,
            detail={
                "code": "INVALID_BASELINE"
            }
        )

    if (
        preferred_crop != "auto"
        and preferred_crop not in ALL_CROPS
    ):
        raise HTTPException(
            status_code=422,
            detail={
                "code": "INVALID_PREFERRED_CROP"
            }
        )

    if drainage not in DRAINAGE_OPTIONS:
        raise HTTPException(
            status_code=422,
            detail={
                "code": "INVALID_DRAINAGE"
            }
        )


# ============================================
# 4. NASA CLIMATE CACHE
# ============================================

@lru_cache(maxsize=80)
def cached_climate(latitude, longitude):

    return get_historical_climate(
        latitude,
        longitude
    )


# ============================================
# 5. PERSONALIZED FARM ASSESSMENT
# ============================================

@lru_cache(maxsize=160)
def cached_assessment(
    latitude,
    longitude,
    priority,
    baseline,
    preferred_crop,
    drainage
):
    """
    Produce a complete personalized assessment.

    NASA climate observations remain unchanged
    when farmer priorities or drainage change.

    Strategy comparisons and farming actions
    respond to the selected farmer inputs.
    """

    climate = cached_climate(
        latitude,
        longitude
    )

    crop_results = build_recommendations(
        latitude,
        longitude,
        climate
    )

    result = enrich(
        crop_results,
        climate,
        priority=priority,
        baseline=baseline,
        preferred_crop=preferred_crop,
        drainage=drainage
    )

    if not isinstance(result, dict):
        raise ValueError(
            "Strategy engine must return a dictionary."
        )

    # Avoid modifying a cached shared result.
    result = copy.deepcopy(result)

    # ========================================
    # MARKET ASSESSMENT
    # ========================================

    selected_strategy = next(
        (
            strategy
            for strategy in result.get(
                "strategies", []
            )
            if strategy.get("id")
            == result.get(
                "recommended_strategy_id"
            )
        ),
        None
    )

    market = build_market_assessment(
        preferred_crop=preferred_crop,
        baseline=baseline,
        selected_strategy=selected_strategy
    )

    result["market_insights"] = market

    # ========================================
    # FARMER INPUTS
    # ========================================

    result["farmer_inputs"] = {
        "latitude": latitude,
        "longitude": longitude,
        "priority": priority,
        "baseline": baseline,
        "preferred_crop": preferred_crop,
        "drainage": drainage
    }

    # ========================================
    # AVAILABLE CROPS
    # ========================================

    result["available_crops"] = [
        {
            "id": crop_id,
            "name": crop["name"],
            "family": crop["family"],
            "kind": crop["kind"],
            "approx_duration_months": (
                crop["months"]
            ),
            "planting_system": crop.get(
                "planting_system"
            )
        }
        for crop_id, crop in CROPS.items()
    ]

    # ========================================
    # DATA SOURCE ATTRIBUTION
    # ========================================

    result["data_sources"] = {
        "primary": {
            "name": "NASA POWER",
            "url": (
                "https://power.larc.nasa.gov/"
            ),
            "purpose": (
                "Historical environmental "
                "observations and estimates"
            )
        },
        "crop_model": {
            "name": (
                "BUMI SHIFT experimental "
                "crop screening"
            ),
            "purpose": (
                "Provisional crop compatibility "
                "and rotation comparison"
            )
        },
        "market": get_sources()
    }

    # ========================================
    # 3D VISUALIZATION CONTEXT
    # ========================================

    summary = climate.get(
        "summary", {}
    )

    result["farm_visualization"] = {
        "type": "illustrative_3d_scenario",
        "baseline_crop": baseline,
        "preferred_crop": preferred_crop,
        "drainage": drainage,
        "priority": priority,
        "selected_strategy_id": result.get(
            "recommended_strategy_id"
        ),
        "stages": (
            selected_strategy.get("stages", [])
            if selected_strategy
            else []
        ),
        "nasa_evidence": {
            "mean_annual_rainfall_mm": (
                summary.get(
                    "mean_annual_rainfall_mm"
                )
            ),
            "mean_temperature_c": (
                summary.get(
                    "mean_temperature_c"
                )
            ),
            "climate_period": result.get(
                "climate_period"
            )
        },
        "limitations": [
            "Simplified crop appearance.",
            "Illustrative development stages.",
            "Not a measured farm reconstruction.",
            "Not a crop-growth or yield prediction.",
            "Planting arrangements require local review."
        ]
    }

    return result


# ============================================
# 6. SERVICE STATUS
# ============================================

@app.get("/")
def home():

    return {
        "name": "BUMI SHIFT",
        "version": "7.1",
        "status": "running",
        "website": "/app",
        "api_endpoints": {
            "health": "/health",
            "climate": "/climate/history",
            "recommendations": "/recommendations",
            "crops": "/crops",
            "market": "/market",
            "market_sources": "/market/sources"
        }
    }


@app.get("/health")
def health():

    return {
        "status": "ok",
        "version": "7.1",
        "crop_count": len(CROPS),
        "market_engine_connected": True,
        "gemini_required": False
    }


# ============================================
# 7. WEBSITE
# ============================================

@app.get("/app")
def website():

    index = STATIC_DIR / "index.html"

    if not index.is_file():
        raise HTTPException(
            status_code=404,
            detail={
                "code": "WEBSITE_NOT_FOUND"
            }
        )

    return FileResponse(
        index,
        media_type="text/html"
    )


# ============================================
# 8. CROP LIBRARY
# ============================================

@app.get("/crops")
def get_crops():

    return {
        "region": "Sarawak, Malaysia",
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
                "planting_system": crop.get(
                    "planting_system"
                ),
                "description": crop.get(
                    "description"
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
            "Crop requirements are provisional "
            "screening assumptions."
        )
    }


# ============================================
# 9. NASA CLIMATE HISTORY
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

    validate_location(
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
            "NASA climate retrieval failed"
        )

        raise HTTPException(
            status_code=503,
            detail={
                "code": "CLIMATE_REQUEST_FAILED",
                "message": (
                    "Historical NASA climate data "
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

    validate_location(
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

        result = cached_assessment(
            round(latitude, 4),
            round(longitude, 4),
            priority,
            baseline,
            preferred_crop,
            drainage
        )

        return result

    except HTTPException:
        raise

    except Exception as exc:

        logger.exception(
            "Personalized assessment failed"
        )

        raise HTTPException(
            status_code=503,
            detail={
                "code": "ASSESSMENT_REQUEST_FAILED",
                "message": (
                    "The farming assessment "
                    "could not be completed."
                )
            }
        ) from exc


# ============================================
# 11. MARKET OVERVIEW
# ============================================

@app.get("/market")
def market_overview():

    try:
        return get_all_crop_market_profiles()

    except Exception as exc:

        logger.exception(
            "Market overview failed"
        )

        raise HTTPException(
            status_code=503,
            detail={
                "code": "MARKET_REQUEST_FAILED"
            }
        ) from exc


# ============================================
# 12. CROP-SPECIFIC MARKET PROFILE
# ============================================

@app.get("/market/crop/{crop_id}")
def crop_market_profile(crop_id: str):

    if crop_id not in ALL_CROPS:
        raise HTTPException(
            status_code=404,
            detail={
                "code": "CROP_NOT_FOUND"
            }
        )

    profile = get_crop_market_profile(
        crop_id
    )

    if profile is None:
        raise HTTPException(
            status_code=404,
            detail={
                "code": "MARKET_PROFILE_NOT_FOUND"
            }
        )

    return profile


# ============================================
# 13. MARKET SOURCES
# ============================================

@app.get("/market/sources")
def market_sources():

    return {
        "region": "Sarawak, Malaysia",
        "sources": get_sources(),
        "data_status": market_data_status(),
        "primary_environmental_source": (
            "NASA POWER"
        ),
        "note": (
            "Market information provides "
            "supplementary agricultural context."
        )
    }


# ============================================
# 14. MARKET ASSESSMENT
# ============================================

@app.get("/market/assessment")
def market_assessment(
    baseline: str = "rice",
    preferred_crop: str = "auto"
):

    if baseline not in BASELINES:
        raise HTTPException(
            status_code=422,
            detail={
                "code": "INVALID_BASELINE"
            }
        )

    if (
        preferred_crop != "auto"
        and preferred_crop not in ALL_CROPS
    ):
        raise HTTPException(
            status_code=422,
            detail={
                "code": "INVALID_PREFERRED_CROP"
            }
        )

    return build_market_assessment(
        preferred_crop=preferred_crop,
        baseline=baseline
    )


# ============================================
# 15. CACHE STATUS
# ============================================

@app.get("/system/cache")
def cache_status():
    """
    Exposes aggregate cache counts only.
    No farmer inputs or cached results
    are returned.
    """

    climate_info = cached_climate.cache_info()
    assessment_info = cached_assessment.cache_info()

    return {
        "climate": {
            "entries": climate_info.currsize,
            "maximum": climate_info.maxsize
        },
        "assessments": {
            "entries": assessment_info.currsize,
            "maximum": assessment_info.maxsize
        }
    }
