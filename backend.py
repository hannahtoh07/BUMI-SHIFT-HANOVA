
"""
BUMI SHIFT 7.2
NASA + District-Aware Market Intelligence Backend
HANOVA | Sarawak, Malaysia

Core:
- NASA POWER climate analysis
- 11 crop recommendations
- Personalized farming strategies
- District-aware market evidence
- Market readiness checklist
- 3D farming scenario context

No Gemini API required.
"""

import copy
import logging
import math
import re

from pathlib import Path
from functools import lru_cache

import requests

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
    market_data_status,
    market_readiness
)


# ============================================
# 1. CONFIGURATION
# ============================================

ROOT = Path(__file__).resolve().parent
STATIC_DIR = ROOT / "static"

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("bumi_shift")

app = FastAPI(
    title="BUMI SHIFT",
    version="7.2",
    description=(
        "NASA-powered farming decision support "
        "with Sarawak market intelligence."
    )
)

app.mount(
    "/static",
    StaticFiles(directory=STATIC_DIR),
    name="static"
)

PRIORITIES = {
    "soil", "water", "resilience", "income"
}

BASELINES = {
    "rice", "maize", "mung_bean",
    "groundnut", "soybean", "sweet_potato"
}

ALL_CROPS = set(CROPS.keys())

DRAINAGE = {
    "unknown", "poor", "moderate", "good"
}

READINESS = {
    "yes", "no", "unknown"
}

SARAWAK = {
    "min_lat": 0.5,
    "max_lat": 5.1,
    "min_lon": 109.5,
    "max_lon": 115.5
}

NOMINATIM_URL = (
    "https://nominatim.openstreetmap.org/reverse"
)


# ============================================
# 2. VALIDATION
# ============================================

def validate_location(latitude, longitude):

    if not (
        math.isfinite(latitude)
        and math.isfinite(longitude)
    ):
        raise HTTPException(
            422,
            detail={"code": "INVALID_COORDINATES"}
        )

    if not (
        SARAWAK["min_lat"] <= latitude
        <= SARAWAK["max_lat"]
        and
        SARAWAK["min_lon"] <= longitude
        <= SARAWAK["max_lon"]
    ):
        raise HTTPException(
            422,
            detail={
                "code": "INVALID_LOCATION",
                "message": "Select a Sarawak location."
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
            422,
            detail={"code": "INVALID_PRIORITY"}
        )

    if baseline not in BASELINES:
        raise HTTPException(
            422,
            detail={"code": "INVALID_BASELINE"}
        )

    if (
        preferred_crop != "auto"
        and preferred_crop not in ALL_CROPS
    ):
        raise HTTPException(
            422,
            detail={"code": "INVALID_PREFERRED_CROP"}
        )

    if drainage not in DRAINAGE:
        raise HTTPException(
            422,
            detail={"code": "INVALID_DRAINAGE"}
        )


# ============================================
# 3. DISTRICT RESOLUTION
# ============================================

def normalize_district(value):

    text = str(value or "").strip()

    text = re.sub(
        r"\b(District|Daerah)\b",
        "",
        text,
        flags=re.IGNORECASE
    )

    return " ".join(text.split())


@lru_cache(maxsize=128)
def resolve_district(latitude, longitude):
    """
    Provisional administrative district lookup.

    OpenStreetMap address fields are not
    guaranteed to match official Malaysian
    district boundaries.

    No district is invented if uncertain.
    """

    try:
        response = requests.get(
            NOMINATIM_URL,
            params={
                "lat": latitude,
                "lon": longitude,
                "format": "jsonv2",
                "addressdetails": 1,
                "zoom": 10
            },
            headers={
                "User-Agent": (
                    "BUMI-SHIFT-HANOVA/7.2 "
                    "(agricultural research prototype)"
                )
            },
            timeout=12
        )

        response.raise_for_status()

        data = response.json()
        address = data.get("address", {})

        state = str(
            address.get("state", "")
        ).lower()

        if "sarawak" not in state:
            return None

        # Prefer district-level fields.
        candidates = [
            address.get("state_district"),
            address.get("county")
        ]

        for candidate in candidates:
            if candidate:
                return normalize_district(
                    candidate
                )

        return None

    except (
        requests.RequestException,
        ValueError,
        KeyError
    ):
        logger.warning(
            "District lookup could not be completed"
        )
        return None


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
# 5. PERSONALIZED ASSESSMENT
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

    climate = cached_climate(
        latitude,
        longitude
    )

    crops = build_recommendations(
        latitude,
        longitude,
        climate
    )

    result = enrich(
        crops,
        climate,
        priority=priority,
        baseline=baseline,
        preferred_crop=preferred_crop,
        drainage=drainage
    )

    if not isinstance(result, dict):
        raise ValueError(
            "Strategy engine returned invalid data."
        )

    result = copy.deepcopy(result)

    strategies = result.get(
        "strategies", []
    )

    recommended_id = result.get(
        "recommended_strategy_id"
    )

    selected_strategy = next(
        (
            s for s in strategies
            if s.get("id") == recommended_id
        ),
        None
    )

    if selected_strategy is None:
        selected_strategy = next(
            (
                s for s in strategies
                if s.get("type") != "baseline"
            ),
            None
        )

    district = resolve_district(
        latitude,
        longitude
    )

    market = build_market_assessment(
        preferred_crop=preferred_crop,
        baseline=baseline,
        selected_strategy=selected_strategy,
        district=district
    )

    result["market_insights"] = market

    result["farmer_inputs"] = {
        "latitude": latitude,
        "longitude": longitude,
        "priority": priority,
        "baseline": baseline,
        "preferred_crop": preferred_crop,
        "drainage": drainage
    }

    result["location_context"] = {
        "state": "Sarawak",
        "country": "Malaysia",
        "district": district,
        "district_method": (
            "OpenStreetMap reverse geocoding"
        ),
        "district_verified": False
    }

    result["available_crops"] = [
        {
            "id": crop_id,
            "name": crop["name"],
            "family": crop["family"],
            "kind": crop["kind"],
            "approx_duration_months":
                crop["months"]
        }
        for crop_id, crop in CROPS.items()
    ]

    result["data_sources"] = {
        "primary": {
            "name": "NASA POWER",
            "url": "https://power.larc.nasa.gov/",
            "purpose": (
                "Historical environmental observations"
            )
        },
        "market": get_sources()
    }

    summary = climate.get("summary", {})

    result["farm_visualization"] = {
        "type": "illustrative_3d_scenario",
        "baseline_crop": baseline,
        "preferred_crop": preferred_crop,
        "drainage": drainage,
        "priority": priority,
        "selected_strategy_id": (
            selected_strategy.get("id")
            if selected_strategy
            else None
        ),
        "stages": (
            selected_strategy.get("stages", [])
            if selected_strategy
            else []
        ),
        "nasa_evidence": {
            "mean_annual_rainfall_mm":
                summary.get(
                    "mean_annual_rainfall_mm"
                ),
            "mean_temperature_c":
                summary.get(
                    "mean_temperature_c"
                ),
            "climate_period":
                result.get("climate_period")
        },
        "limitations": [
            "Simplified crop appearance.",
            "Illustrative development stages.",
            "Not a measured farm reconstruction.",
            "Not a crop-growth prediction."
        ]
    }

    return result


# ============================================
# 6. SERVICE ENDPOINTS
# ============================================

@app.get("/")
def home():

    return {
        "name": "BUMI SHIFT",
        "version": "7.2",
        "status": "running",
        "website": "/app"
    }


@app.get("/health")
def health():

    return {
        "status": "ok",
        "version": "7.2",
        "crop_count": len(CROPS),
        "market_engine_connected": True,
        "gemini_required": False
    }


@app.get("/app")
def website():

    return FileResponse(
        STATIC_DIR / "index.html"
    )


# ============================================
# 7. NASA CLIMATE
# ============================================

@app.get("/climate/history")
def climate_history(
    latitude: float = 1.46,
    longitude: float = 110.49
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
            503,
            detail={
                "code": "CLIMATE_REQUEST_FAILED"
            }
        ) from exc


# ============================================
# 8. FARM RECOMMENDATIONS
# ============================================

@app.get("/recommendations")
def recommendations(
    latitude: float = 1.46,
    longitude: float = 110.49,
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
        return cached_assessment(
            round(latitude, 4),
            round(longitude, 4),
            priority,
            baseline,
            preferred_crop,
            drainage
        )

    except Exception as exc:

        logger.exception(
            "Assessment failed"
        )

        raise HTTPException(
            503,
            detail={
                "code": "ASSESSMENT_REQUEST_FAILED"
            }
        ) from exc


# ============================================
# 9. CROP LIBRARY
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
                "approx_duration_months":
                    crop["months"]
            }
            for crop_id, crop in CROPS.items()
        ]
    }


# ============================================
# 10. MARKET INTELLIGENCE
# ============================================

@app.get("/market")
def market_overview(
    district: str | None = None
):

    return get_all_crop_market_profiles(
        district=district
    )


@app.get("/market/crop/{crop_id}")
def crop_market(
    crop_id: str,
    district: str | None = None
):

    if crop_id not in ALL_CROPS:
        raise HTTPException(
            404,
            detail={"code": "CROP_NOT_FOUND"}
        )

    return get_crop_market_profile(
        crop_id,
        district=district
    )


@app.get("/market/sources")
def market_sources():

    return {
        "region": "Sarawak, Malaysia",
        "sources": get_sources(),
        "data_status": market_data_status()
    }


@app.get("/market/assessment")
def market_assessment(
    baseline: str = "rice",
    preferred_crop: str = "auto",
    district: str | None = None
):

    if baseline not in BASELINES:
        raise HTTPException(
            422,
            detail={"code": "INVALID_BASELINE"}
        )

    if (
        preferred_crop != "auto"
        and preferred_crop not in ALL_CROPS
    ):
        raise HTTPException(
            422,
            detail={"code": "INVALID_PREFERRED_CROP"}
        )

    return build_market_assessment(
        baseline=baseline,
        preferred_crop=preferred_crop,
        district=district
    )


# ============================================
# 11. MARKET READINESS
# ============================================

@app.get("/market/readiness/{crop_id}")
def readiness(
    crop_id: str,
    buyer: str = "unknown",
    transport: str = "unknown",
    storage: str = "unknown"
):

    if crop_id not in ALL_CROPS:
        raise HTTPException(
            404,
            detail={"code": "CROP_NOT_FOUND"}
        )

    for value in (buyer, transport, storage):
        if value not in READINESS:
            raise HTTPException(
                422,
                detail={"code": "INVALID_READINESS_INPUT"}
            )

    return market_readiness(
        crop_id,
        buyer=buyer,
        transport=transport,
        storage=storage
    )


# ============================================
# 12. DISTRICT LOOKUP
# ============================================

@app.get("/location/district")
def location_district(
    latitude: float = Query(1.46),
    longitude: float = Query(110.49)
):

    validate_location(
        latitude,
        longitude
    )

    district = resolve_district(
        round(latitude, 4),
        round(longitude, 4)
    )

    return {
        "state": "Sarawak",
        "country": "Malaysia",
        "district": district,
        "method": "OpenStreetMap reverse geocoding",
        "verified": False
    }
