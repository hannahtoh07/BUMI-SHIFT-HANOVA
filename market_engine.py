
"""
BUMI SHIFT 7.2
District-Aware Sarawak Market Intelligence
HANOVA | NASA Space Apps Challenge

Official sources:
OpenDOSM / MAFS / DOA / DOSM

Rules:
- Sarawak records only
- Exact crop-species matches
- District evidence kept separate from state evidence
- Historical statistics retain their observation year
- No invented buyers, prices, yields, revenues or profits
- No API key required

This is agricultural market decision support,
not a forecast of demand or financial returns.
"""

import csv
import io
import logging
import math
import re
import time
from datetime import date
from functools import lru_cache

import requests

logger = logging.getLogger("bumi_shift.market")

DATASETS = {
    "district_production": {
        "url": "https://storage.data.gov.my/agriculture/crops_district_production.csv",
        "catalogue": "https://open.dosm.gov.my/data-catalogue/crops_district_production",
        "field": "production",
        "measure": "Production",
        "unit": "metric tonnes"
    },
    "district_area": {
        "url": "https://storage.data.gov.my/agriculture/crops_district_area.csv",
        "catalogue": "https://open.dosm.gov.my/data-catalogue/crops_district_area",
        "field": "planted_area",
        "measure": "Planted area",
        "unit": "ha"
    },
    "state": {
        "url": "https://storage.data.gov.my/agriculture/crops_state.csv",
        "catalogue": "https://open.dosm.gov.my/data-catalogue/crops_state"
    }
}

SOURCES = {
    "dosm_production": {
        "name": "OpenDOSM — Crop Production by District",
        "url": DATASETS["district_production"]["catalogue"],
        "geographic_scope": "Sarawak districts",
        "purpose": "Historical crop-specific production"
    },
    "dosm_area": {
        "name": "OpenDOSM — Crop Area by District",
        "url": DATASETS["district_area"]["catalogue"],
        "geographic_scope": "Sarawak districts",
        "purpose": "Historical crop-specific planted area"
    },
    "dosm_state": {
        "name": "OpenDOSM — Crop Area and Production by State",
        "url": DATASETS["state"]["catalogue"],
        "geographic_scope": "Sarawak",
        "purpose": "Historical state-level agricultural statistics"
    }
}

# Exact species identifiers.
# Sweet corn is not all maize.
CROP_SPECIES = {
    "rice": {"paddy", "rice"},
    "maize": {"sweet_corn"},
    "mung_bean": {"mung_bean"},
    "groundnut": {"groundnuts", "groundnut"},
    "soybean": {"soybean"},
    "sweet_potato": {"sweet_potato"},
    "cassava": {"cassava"},
    "pineapple": {"pineapple"},
    "banana": {"banana"},
    "coconut": {"coconut"},
    "durian": {"durian"}
}

# Only these state categories represent
# the requested crop directly.
STATE_CATEGORIES = {
    "rice": {"paddy"},
    "coconut": {"coconut"}
}

CROP_NAMES = {
    "rice": "Rice",
    "maize": "Maize",
    "mung_bean": "Mung Bean",
    "groundnut": "Groundnut",
    "soybean": "Soybean",
    "sweet_potato": "Sweet Potato",
    "cassava": "Cassava",
    "pineapple": "Pineapple",
    "banana": "Banana",
    "coconut": "Coconut",
    "durian": "Durian"
}

MARKET_PROFILES = {
    "rice": {
        "products": ["Paddy grain", "Milled rice"],
        "channels": ["Paddy collection centres", "Rice millers"],
        "postharvest": ["Drying", "Grading", "Moisture control"],
        "considerations": [
            "Confirm purchasing and grain-quality requirements.",
            "Review drying and storage arrangements."
        ]
    },
    "maize": {
        "products": ["Sweet corn", "Grain maize"],
        "channels": ["Produce buyers", "Grain traders"],
        "postharvest": ["Sorting", "Harvest timing", "Grain drying"],
        "considerations": [
            "Confirm whether buyers want sweet corn or grain maize.",
            "Check delivery timing and product specifications."
        ]
    },
    "mung_bean": {
        "products": ["Dried mung beans"],
        "channels": ["Grain traders", "Food processors"],
        "postharvest": ["Drying", "Cleaning", "Storage"],
        "considerations": [
            "Confirm a potential buyer before planting.",
            "Check moisture and storage requirements."
        ]
    },
    "groundnut": {
        "products": ["Fresh groundnuts", "Dried groundnuts"],
        "channels": ["Produce buyers", "Processors"],
        "postharvest": ["Cleaning", "Drying", "Safe storage"],
        "considerations": [
            "Confirm the intended fresh or dried product.",
            "Plan moisture control and quality checks."
        ]
    },
    "soybean": {
        "products": ["Dry soybeans"],
        "channels": ["Grain traders", "Food processors"],
        "postharvest": ["Drying", "Grading", "Storage"],
        "considerations": [
            "Verify demand for the selected variety.",
            "Confirm quality and moisture specifications."
        ]
    },
    "sweet_potato": {
        "products": ["Fresh roots", "Processed products"],
        "channels": ["Produce buyers", "Food processors"],
        "postharvest": ["Sorting", "Careful handling", "Storage"],
        "considerations": [
            "Confirm preferred varieties and root sizes.",
            "Reduce root damage during handling."
        ]
    },
    "cassava": {
        "products": ["Fresh roots", "Processed cassava"],
        "channels": ["Root buyers", "Processors"],
        "postharvest": ["Prompt transport", "Appropriate processing"],
        "considerations": [
            "Confirm processing or fresh-root requirements.",
            "Arrange timely transport after harvesting."
        ]
    },
    "pineapple": {
        "products": ["Fresh pineapple", "Processed pineapple"],
        "channels": ["Fruit buyers", "Processors"],
        "postharvest": ["Grading", "Maturity checks", "Transport"],
        "considerations": [
            "Confirm variety and fruit-size preferences.",
            "Coordinate harvesting with delivery."
        ]
    },
    "banana": {
        "products": ["Fresh bananas", "Processed bananas"],
        "channels": ["Fruit wholesalers", "Retailers"],
        "postharvest": ["Ripening", "Handling", "Transport"],
        "considerations": [
            "Confirm buyer variety preferences.",
            "Plan ripening and delivery arrangements."
        ]
    },
    "coconut": {
        "products": ["Young coconuts", "Mature coconuts"],
        "channels": ["Produce buyers", "Coconut processors"],
        "postharvest": ["Harvesting", "Sorting", "Transport"],
        "considerations": [
            "Confirm the intended coconut product.",
            "Review harvesting labour and transport."
        ]
    },
    "durian": {
        "products": ["Fresh durian", "Processed durian"],
        "channels": ["Fruit traders", "Processors"],
        "postharvest": ["Harvest timing", "Handling", "Transport"],
        "considerations": [
            "Verify cultivar-specific buyer requirements.",
            "Plan collection and long-term orchard marketing."
        ]
    }
}


# ============================================
# 1. DATA HELPERS
# ============================================

def normalize(value):
    text = str(value or "").strip().lower()
    return re.sub(r"[^a-z0-9]+", "_", text).strip("_")


def numeric(value):
    try:
        n = float(str(value).replace(",", ""))
        return n if math.isfinite(n) and n >= 0 else None
    except (ValueError, TypeError):
        return None


def year_of(value):
    try:
        return int(str(value)[:4])
    except (ValueError, TypeError):
        return None


# ============================================
# 2. OFFICIAL DATA DOWNLOAD
# ============================================

# Cache successful downloads for one day.
# Failed requests are not permanently cached.

_download_cache = {}
CACHE_SECONDS = 86400


def download_dataset(key):
    now = time.monotonic()

    cached = _download_cache.get(key)
    if cached and now - cached[0] < CACHE_SECONDS:
        return cached[1]

    url = DATASETS[key]["url"]

    try:
        response = requests.get(
            url,
            timeout=30,
            headers={
                "User-Agent": "BUMI-SHIFT-HANOVA/7.2"
            }
        )
        response.raise_for_status()

        rows = list(csv.DictReader(
            io.StringIO(
                response.content.decode("utf-8-sig")
            )
        ))

        if not rows:
            raise ValueError("Empty dataset")

        _download_cache[key] = (now, rows)
        return rows

    except (
        requests.RequestException,
        UnicodeError,
        csv.Error,
        ValueError
    ) as exc:
        logger.warning(
            "Official dataset %s: %s",
            key, type(exc).__name__
        )
        return []


# ============================================
# 3. EXACT SARAWAK CROP FILTER
# ============================================

def matches_crop(row, crop_id):
    if normalize(row.get("state")) != "sarawak":
        return False

    return normalize(
        row.get("crop_species")
    ) in CROP_SPECIES[crop_id]


def make_stat(
    crop_id, year, value,
    measure, unit, scope,
    district, source_key,
    crop_label=None
):
    return {
        "crop_id": crop_id,
        "crop": crop_label or CROP_NAMES[crop_id],
        "year": year,
        "value": round(value, 2),
        "measure": measure,
        "unit": unit,
        "geographic_coverage": scope,
        "district": district,
        "state": "Sarawak",
        "source": "OpenDOSM / MAFS / DOA",
        "source_url": DATASETS[source_key]["catalogue"],
        "record_type": "historical_official_statistic"
    }


# ============================================
# 4. DISTRICT RECORDS
# ============================================

@lru_cache(maxsize=128)
def district_crop_statistics(crop_id, district):
    if crop_id not in CROP_SPECIES:
        return []

    district = normalize(district)

    if not district:
        return []

    output = []

    for source_key in (
        "district_production",
        "district_area"
    ):
        dataset = DATASETS[source_key]
        rows = download_dataset(source_key)

        grouped = {}

        for row in rows:
            if not matches_crop(row, crop_id):
                continue

            if normalize(row.get("district")) != district:
                continue

            year = year_of(row.get("date"))
            value = numeric(row.get(dataset["field"]))

            if year is None or value is None:
                continue

            species = normalize(row.get("crop_species"))
            key = (year, species)

            # Avoid duplicate identical observations.
            # Conflicting duplicates are skipped rather
            # than silently added together.
            if key in grouped and grouped[key] != value:
                grouped[key] = None
            elif key not in grouped:
                grouped[key] = value

        yearly = {}

        for (year, _), value in grouped.items():
            if value is not None:
                yearly[year] = yearly.get(year, 0) + value

        for year, value in yearly.items():
            output.append(make_stat(
                crop_id, year, value,
                dataset["measure"],
                dataset["unit"],
                "district",
                district.replace("_", " ").title(),
                source_key,
                "Sweet corn" if crop_id == "maize"
                else None
            ))

    return sorted(
        output,
        key=lambda r: (r["year"], r["measure"]),
        reverse=True
    )


# ============================================
# 5. SARAWAK-WIDE RECORDS
# ============================================

@lru_cache(maxsize=32)
def sarawak_crop_statistics(crop_id):
    if crop_id not in CROP_SPECIES:
        return []

    output = []
    allowed = STATE_CATEGORIES.get(crop_id)

    if allowed:
        for row in download_dataset("state"):
            if normalize(row.get("state")) != "sarawak":
                continue

            if normalize(row.get("crop_type")) not in allowed:
                continue

            year = year_of(row.get("date"))
            if year is None:
                continue

            for field, measure, unit in (
                ("production", "Production", "metric tonnes"),
                ("planted_area", "Planted area", "ha")
            ):
                value = numeric(row.get(field))
                if value is not None:
                    output.append(make_stat(
                        crop_id, year, value,
                        measure, unit,
                        "state", None, "state"
                    ))

        if output:
            return sorted(
                output,
                key=lambda r: r["year"],
                reverse=True
            )

    # Older species-level district records can
    # be aggregated across Sarawak, provided
    # exact crop identifiers are used.
    for source_key in (
        "district_production",
        "district_area"
    ):
        dataset = DATASETS[source_key]
        rows = download_dataset(source_key)

        unique = {}
        conflicts = set()

        for row in rows:
            if not matches_crop(row, crop_id):
                continue

            district = normalize(row.get("district"))
            year = year_of(row.get("date"))
            species = normalize(row.get("crop_species"))
            value = numeric(row.get(dataset["field"]))

            if not district or year is None or value is None:
                continue

            key = (year, district, species)

            if key in unique and unique[key] != value:
                conflicts.add(key)
            else:
                unique[key] = value

        # Do not publish an aggregate for a year
        # containing conflicting duplicate records.
        years_with_conflicts = {
            key[0] for key in conflicts
        }

        totals = {}
        for (year, district, species), value in unique.items():
            if year in years_with_conflicts:
                continue
            totals[year] = totals.get(year, 0) + value

        for year, value in totals.items():
            output.append(make_stat(
                crop_id, year, value,
                dataset["measure"],
                dataset["unit"],
                "state_aggregated_from_districts",
                None, source_key,
                "Sweet corn" if crop_id == "maize"
                else None
            ))

    return sorted(
        output,
        key=lambda r: r["year"],
        reverse=True
    )


# ============================================
# 6. CHOOSE RELEVANT STATISTICS
# ============================================

def latest_by_measure(records):
    latest = {}

    for record in sorted(
        records,
        key=lambda r: r["year"],
        reverse=True
    ):
        latest.setdefault(
            record["measure"], record
        )

    return list(latest.values())


def select_market_evidence(crop_id, district=None):
    district_records = (
        latest_by_measure(
            district_crop_statistics(crop_id, district)
        )
        if district else []
    )

    state_records = latest_by_measure(
        sarawak_crop_statistics(crop_id)
    )

    return {
        "selected_district": district,
        "district_statistics": district_records,
        "sarawak_statistics": state_records,
        "display_statistics": (
            district_records
            if district_records
            else state_records
        ),
        "evidence_scope": (
            "district" if district_records
            else "sarawak"
        ),
        "source_note": (
            "Historical agricultural production and "
            "planted-area statistics are not "
            "measurements of current market demand."
        )
    }


# ============================================
# 7. MARKET READINESS CHECKLIST
# ============================================

def market_readiness(
    crop_id,
    buyer="unknown",
    transport="unknown",
    storage="unknown"
):
    if crop_id not in MARKET_PROFILES:
        return None

    allowed = {"yes", "no", "unknown"}

    answers = {
        "buyer": buyer if buyer in allowed else "unknown",
        "transport": transport if transport in allowed else "unknown",
        "storage": storage if storage in allowed else "unknown"
    }

    guidance = {
        "buyer": (
            "Identify a potential buyer and confirm "
            "product, quality, quantity and delivery terms."
        ),
        "transport": (
            "Check harvest collection, transport "
            "availability and travel time."
        ),
        "storage": (
            "Review crop-specific drying, handling "
            "and storage arrangements."
        )
    }

    actions = [
        guidance[key]
        for key, value in answers.items()
        if value != "yes"
    ]

    confirmed = sum(
        value == "yes"
        for value in answers.values()
    )

    return {
        "crop_id": crop_id,
        "answers": answers,
        "confirmed_arrangements": confirmed,
        "total_arrangements": 3,
        "next_actions": actions,
        "interpretation": (
            "Basic arrangements reported as confirmed."
            if confirmed == 3
            else "Review remaining arrangements "
                 "before committing to planting."
        ),
        "note": (
            "Farmer-reported preparation checklist, "
            "not a guarantee of sales."
        )
    }


# ============================================
# 8. PUBLIC FUNCTIONS
# ============================================

def get_sources():
    return [
        {"id": key, **details}
        for key, details in SOURCES.items()
    ]


def get_crop_market_profile(crop_id, district=None):
    if crop_id not in MARKET_PROFILES:
        return None

    evidence = select_market_evidence(
        crop_id, district
    )

    return {
        "crop_id": crop_id,
        "name": CROP_NAMES[crop_id],
        **MARKET_PROFILES[crop_id],
        **evidence,
        "verified_statistics": evidence[
            "display_statistics"
        ],
        "numerical_data_available": bool(
            evidence["display_statistics"]
        ),
        "market_price_status": "not_integrated",
        "readiness_questions": [
            {
                "id": "buyer",
                "question": "Have you identified a potential buyer?"
            },
            {
                "id": "transport",
                "question": "Can you transport the harvest?"
            },
            {
                "id": "storage",
                "question": "Have you arranged suitable handling or storage?"
            }
        ],
        "sources": get_sources()
    }


def build_market_assessment(
    preferred_crop="auto",
    baseline="rice",
    selected_strategy=None,
    district=None
):
    ids = []

    for crop_id in (baseline, preferred_crop):
        if crop_id in MARKET_PROFILES and crop_id not in ids:
            ids.append(crop_id)

    if selected_strategy:
        for crop_id in selected_strategy.get(
            "crop_ids", []
        ):
            if (
                crop_id in MARKET_PROFILES
                and crop_id not in ids
            ):
                ids.append(crop_id)

    profiles = [
        get_crop_market_profile(crop_id, district)
        for crop_id in ids
    ]

    return {
        "region": "Sarawak, Malaysia",
        "district": district,
        "generated_on": date.today().isoformat(),
        "baseline": baseline,
        "preferred_crop": preferred_crop,
        "crop_profiles": profiles,
        "official_sources": get_sources(),
        "verified_price_records": 0,
        "price_data_integrated": False,
        "market_readiness_enabled": True,
        "limitations": [
            "Only Sarawak and exact-crop statistics are displayed.",
            "District records are historical.",
            "Historical production is not evidence of current demand.",
            "Buyer availability must be confirmed locally.",
            "No revenue, profit or yield predictions are generated."
        ]
    }


def get_all_crop_market_profiles(district=None):
    return {
        "region": "Sarawak, Malaysia",
        "district": district,
        "crop_count": len(MARKET_PROFILES),
        "crops": [
            get_crop_market_profile(crop_id, district)
            for crop_id in MARKET_PROFILES
        ],
        "official_sources": get_sources(),
        "generated_on": date.today().isoformat()
    }


def market_data_status():
    return {
        "region": "Sarawak, Malaysia",
        "official_source_count": len(SOURCES),
        "crop_profile_count": len(MARKET_PROFILES),
        "live_price_api_connected": False,
        "revenue_estimation_enabled": False,
        "profit_estimation_enabled": False,
        "primary_environmental_source": "NASA POWER",
        "statistical_scope": (
            "Sarawak-specific exact crop records"
        )
    }
