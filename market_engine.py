
"""
BUMI SHIFT 7.2
Sarawak Market Strategy Advisor
HANOVA | NASA Space Apps Challenge

Scope:
- 11 supported crops
- Sarawak-specific agricultural evidence
- District-aware market context
- Personalized selling strategies
- Buyer, transport and storage considerations
- Crop-specific post-harvest actions

No invented market prices, buyers, yields,
revenue or profit estimates.

NASA POWER remains the primary environmental
source in the wider BUMI SHIFT platform.
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


# ==========================================
# 1. OFFICIAL SOURCE DIRECTORY
# ==========================================

SOURCES = {
    "dosm_state": {
        "name": "OpenDOSM — Crops by State",
        "url": (
            "https://open.dosm.gov.my/"
            "data-catalogue/crops_state"
        ),
        "geographic_scope": "Sarawak",
        "purpose": "Agricultural production and area"
    },
    "dosm_district_production": {
        "name": "OpenDOSM — District Production",
        "url": (
            "https://open.dosm.gov.my/"
            "data-catalogue/crops_district_production"
        ),
        "geographic_scope": "Sarawak districts",
        "purpose": "Crop production statistics"
    },
    "dosm_district_area": {
        "name": "OpenDOSM — District Crop Area",
        "url": (
            "https://open.dosm.gov.my/"
            "data-catalogue/crops_district_area"
        ),
        "geographic_scope": "Sarawak districts",
        "purpose": "Crop planted-area statistics"
    },
    "sarawak": {
        "name": "Sarawak Government Open Data",
        "url": "https://data.sarawak.gov.my/",
        "geographic_scope": "Sarawak",
        "purpose": "Regional agricultural information"
    },
    "fama": {
        "name": "FAMA Agri Market Insight",
        "url": "https://ami.fama.gov.my/",
        "geographic_scope": "Malaysia",
        "purpose": "Official market-price reference portal"
    }
}


# ==========================================
# 2. SUPPORTED CROPS
# ==========================================

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

# Strict crop matching.
# Sweet corn observations are not equivalent
# to total maize production.

CROP_SPECIES = {
    "rice": {"paddy", "rice", "padi"},
    "maize": {"sweet_corn", "jagung_manis"},
    "mung_bean": {"mung_bean", "kacang_hijau"},
    "groundnut": {
        "groundnut", "groundnuts",
        "peanut", "kacang_tanah"
    },
    "soybean": {"soybean", "soya_bean"},
    "sweet_potato": {
        "sweet_potato", "ubi_keledek"
    },
    "cassava": {"cassava", "ubi_kayu"},
    "pineapple": {"pineapple", "nanas"},
    "banana": {"banana", "pisang"},
    "coconut": {"coconut", "kelapa"},
    "durian": {"durian"}
}

STATE_CATEGORIES = {
    "rice": {"paddy"},
    "coconut": {"coconut"}
}


# ==========================================
# 3. CROP-SPECIFIC MARKET KNOWLEDGE
# ==========================================

MARKET_PROFILES = {
    "rice": {
        "products": ["Paddy grain", "Milled rice"],
        "channels": [
            "Paddy collection centres",
            "Rice millers"
        ],
        "postharvest": [
            "Grain drying",
            "Moisture control",
            "Grading"
        ],
        "considerations": [
            "Confirm purchasing and grading requirements.",
            "Arrange drying and suitable storage."
        ],
        "focus": "Paddy quality and collection",
        "handling": (
            "Check grain moisture and arrange drying "
            "before storage or delivery."
        ),
        "selling": (
            "Confirm collection arrangements, accepted "
            "varieties and grain specifications."
        ),
        "delivery": (
            "Coordinate harvest, drying and collection "
            "with the intended buyer."
        )
    },
    "maize": {
        "products": ["Sweet corn", "Grain maize"],
        "channels": [
            "Fresh produce buyers",
            "Grain traders"
        ],
        "postharvest": [
            "Harvest timing",
            "Sorting",
            "Grain drying where applicable"
        ],
        "considerations": [
            "Confirm whether the intended product is "
            "sweet corn or grain maize.",
            "Check variety and delivery specifications."
        ],
        "focus": "Product type and harvest timing",
        "handling": (
            "Fresh sweet corn needs timely handling, "
            "while grain maize requires suitable drying."
        ),
        "selling": (
            "Confirm the maize product, variety, "
            "quality and quantity required by buyers."
        ),
        "delivery": (
            "Plan harvest and delivery according to "
            "the selected maize product."
        )
    },
    "mung_bean": {
        "products": ["Dried mung beans"],
        "channels": [
            "Grain traders",
            "Food processors"
        ],
        "postharvest": [
            "Drying",
            "Cleaning",
            "Storage"
        ],
        "considerations": [
            "Confirm potential grain buyers.",
            "Check moisture and grading requirements."
        ],
        "focus": "Dry grain quality",
        "handling": (
            "Arrange drying, cleaning and "
            "moisture-controlled storage."
        ),
        "selling": (
            "Confirm grain quality, quantity and "
            "delivery requirements with potential buyers."
        ),
        "delivery": (
            "Protect dried grain from moisture "
            "during storage and transportation."
        )
    },
    "groundnut": {
        "products": [
            "Fresh groundnuts",
            "Dried groundnuts"
        ],
        "channels": [
            "Produce buyers",
            "Food processors"
        ],
        "postharvest": [
            "Cleaning",
            "Drying",
            "Safe storage"
        ],
        "considerations": [
            "Confirm fresh or dried product requirements.",
            "Control moisture and storage quality."
        ],
        "focus": "Drying and product quality",
        "handling": (
            "Plan appropriate drying and storage "
            "to reduce deterioration and contamination risks."
        ),
        "selling": (
            "Confirm whether buyers require fresh "
            "or dried groundnuts and their quality specifications."
        ),
        "delivery": (
            "Coordinate collection after appropriate "
            "cleaning and handling."
        )
    },
    "soybean": {
        "products": ["Dry soybeans"],
        "channels": [
            "Grain traders",
            "Food processors"
        ],
        "postharvest": [
            "Drying",
            "Grading",
            "Storage"
        ],
        "considerations": [
            "Confirm buyer variety preferences.",
            "Review grain moisture and quality requirements."
        ],
        "focus": "Grain quality and storage",
        "handling": (
            "Arrange suitable drying, grading "
            "and grain storage."
        ),
        "selling": (
            "Confirm processor requirements "
            "and acceptance of the selected variety."
        ),
        "delivery": (
            "Protect dried grain quality "
            "during transport."
        )
    },
    "sweet_potato": {
        "products": [
            "Fresh storage roots",
            "Processed products"
        ],
        "channels": [
            "Fresh produce buyers",
            "Food processors"
        ],
        "postharvest": [
            "Careful harvesting",
            "Sorting",
            "Appropriate storage"
        ],
        "considerations": [
            "Confirm preferred varieties and root sizes.",
            "Reduce handling damage."
        ],
        "focus": "Root quality and grading",
        "handling": (
            "Minimize root damage and review "
            "suitable curing and storage practices."
        ),
        "selling": (
            "Confirm buyer preferences for "
            "variety, root size and grading."
        ),
        "delivery": (
            "Arrange careful packing and "
            "timely delivery."
        )
    },
    "cassava": {
        "products": [
            "Fresh cassava roots",
            "Processed cassava"
        ],
        "channels": [
            "Root buyers",
            "Food processors"
        ],
        "postharvest": [
            "Prompt collection",
            "Careful handling",
            "Appropriate processing"
        ],
        "considerations": [
            "Confirm fresh-root or processing requirements.",
            "Arrange prompt post-harvest collection."
        ],
        "focus": "Rapid harvest-to-buyer coordination",
        "handling": (
            "Fresh cassava roots deteriorate rapidly "
            "after harvest. Coordinate prompt collection "
            "or appropriate processing."
        ),
        "selling": (
            "Confirm whether buyers require fresh roots "
            "or specific processing varieties."
        ),
        "delivery": (
            "Agree on a harvest-to-buyer schedule "
            "that minimizes delays."
        )
    },
    "pineapple": {
        "products": [
            "Fresh pineapple",
            "Processed pineapple"
        ],
        "channels": [
            "Fruit buyers",
            "Food processors"
        ],
        "postharvest": [
            "Maturity checks",
            "Fruit grading",
            "Transport"
        ],
        "considerations": [
            "Confirm fruit size and variety preferences.",
            "Coordinate harvest maturity and delivery."
        ],
        "focus": "Fruit maturity and delivery",
        "handling": (
            "Harvest at an appropriate maturity "
            "and minimize fruit damage."
        ),
        "selling": (
            "Confirm buyer requirements for "
            "variety, size and fruit quality."
        ),
        "delivery": (
            "Coordinate fruit collection "
            "and careful transport."
        )
    },
    "banana": {
        "products": [
            "Fresh bananas",
            "Processed bananas"
        ],
        "channels": [
            "Fruit wholesalers",
            "Retailers"
        ],
        "postharvest": [
            "Bunch handling",
            "Ripening management",
            "Transport"
        ],
        "considerations": [
            "Confirm variety and ripeness requirements.",
            "Reduce bruising during transport."
        ],
        "focus": "Ripening and fruit handling",
        "handling": (
            "Minimize bruising and coordinate "
            "ripening and post-harvest handling."
        ),
        "selling": (
            "Confirm preferred varieties "
            "and maturity requirements."
        ),
        "delivery": (
            "Plan collection and delivery "
            "to maintain fruit quality."
        )
    },
    "coconut": {
        "products": [
            "Young coconuts",
            "Mature coconuts"
        ],
        "channels": [
            "Fresh produce buyers",
            "Coconut processors"
        ],
        "postharvest": [
            "Harvesting",
            "Sorting",
            "Transport"
        ],
        "considerations": [
            "Confirm young or mature coconut demand.",
            "Plan harvesting labour and transport."
        ],
        "focus": "Product maturity and collection",
        "handling": (
            "Plan harvesting labour, collection "
            "and product handling."
        ),
        "selling": (
            "Confirm whether buyers want "
            "young or mature coconuts."
        ),
        "delivery": (
            "Review long-term collection "
            "and transport arrangements."
        )
    },
    "durian": {
        "products": [
            "Fresh durian",
            "Processed durian"
        ],
        "channels": [
            "Fruit traders",
            "Food processors"
        ],
        "postharvest": [
            "Harvest timing",
            "Careful handling",
            "Transport"
        ],
        "considerations": [
            "Confirm cultivar-specific buyer requirements.",
            "Plan collection and orchard marketing."
        ],
        "focus": "Cultivar demand and harvest logistics",
        "handling": (
            "Arrange timely fruit collection "
            "and appropriate handling."
        ),
        "selling": (
            "Confirm cultivar-specific requirements "
            "before committing to long-term orchard planting."
        ),
        "delivery": (
            "Coordinate fruit collection, "
            "handling and transport."
        )
    }
}


# ==========================================
# 4. OFFICIAL DATA SETTINGS
# ==========================================

DATASETS = {
    "state": {
        "url": (
            "https://storage.data.gov.my/"
            "agriculture/crops_state.csv"
        ),
        "source_url": SOURCES["dosm_state"]["url"]
    },
    "district_production": {
        "url": (
            "https://storage.data.gov.my/"
            "agriculture/crops_district_production.csv"
        ),
        "source_url": SOURCES[
            "dosm_district_production"
        ]["url"]
    },
    "district_area": {
        "url": (
            "https://storage.data.gov.my/"
            "agriculture/crops_district_area.csv"
        ),
        "source_url": SOURCES[
            "dosm_district_area"
        ]["url"]
    }
}

# No numerical observation is hard-coded.
# Dataset columns and district coverage must
# match the expected schema before publishing.

_cache = {}
CACHE_SECONDS = 86400


def normalize(value):
    return re.sub(
        r"[^a-z0-9]+",
        "_",
        str(value or "").strip().lower()
    ).strip("_")


def numeric(value):
    try:
        n = float(str(value).replace(",", ""))
        return n if math.isfinite(n) and n >= 0 else None
    except (TypeError, ValueError):
        return None


def year_of(value):
    try:
        year = int(str(value)[:4])
        return year if 1900 <= year <= date.today().year else None
    except (TypeError, ValueError):
        return None


def download_dataset(key):
    cached = _cache.get(key)
    now = time.monotonic()

    if cached and now - cached[0] < CACHE_SECONDS:
        return cached[1]

    try:
        response = requests.get(
            DATASETS[key]["url"],
            timeout=15,
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
            return []

        _cache[key] = (now, rows)
        return rows

    except (
        requests.RequestException,
        ValueError,
        UnicodeError,
        csv.Error
    ) as exc:
        logger.warning(
            "Market dataset %s retrieval: %s",
            key,
            type(exc).__name__
        )
        return []


# ==========================================
# 5. SARAWAK STATISTICS
# ==========================================

def make_record(
    crop_id,
    year,
    value,
    measure,
    unit,
    scope,
    district,
    source_key
):
    return {
        "crop_id": crop_id,
        "crop": (
            "Sweet corn"
            if crop_id == "maize"
            else CROP_NAMES[crop_id]
        ),
        "year": year,
        "value": round(value, 2),
        "measure": measure,
        "unit": unit,
        "geographic_coverage": scope,
        "district": district,
        "state": "Sarawak",
        "source": "OpenDOSM",
        "source_url": DATASETS[source_key]["source_url"],
        "record_type": "historical_official_statistic"
    }


def latest_by_measure(records):
    latest = {}

    for record in sorted(
        records,
        key=lambda x: x["year"],
        reverse=True
    ):
        latest.setdefault(
            record["measure"],
            record
        )

    return list(latest.values())


@lru_cache(maxsize=128)
def district_crop_statistics(crop_id, district):
    if crop_id not in CROP_NAMES or not district:
        return []

    target = normalize(district)
    output = []

    configurations = [
        (
            "district_production",
            "production",
            "Production",
            "metric tonnes"
        ),
        (
            "district_area",
            "planted_area",
            "Planted area",
            "ha"
        )
    ]

    for key, field, measure, unit in configurations:
        rows = download_dataset(key)

        if not rows:
            continue

        required = {
            "state", "district", "crop_species",
            "date", field
        }

        if not required.issubset(rows[0].keys()):
            logger.warning(
                "Unexpected schema in %s", key
            )
            continue

        # One exact observation per species,
        # district, year and measure.
        observations = {}
        conflicts = set()

        for row in rows:
            if normalize(row.get("state")) != "sarawak":
                continue

            if normalize(row.get("district")) != target:
                continue

            species = normalize(row.get("crop_species"))

            if species not in CROP_SPECIES[crop_id]:
                continue

            year = year_of(row.get("date"))
            value = numeric(row.get(field))

            if year is None or value is None:
                continue

            obs_key = (year, species)

            if obs_key in observations:
                if observations[obs_key] != value:
                    conflicts.add(obs_key)
            else:
                observations[obs_key] = value

        years_with_conflicts = {
            year for year, _ in conflicts
        }

        yearly = {}

        for (year, species), value in observations.items():
            if year in years_with_conflicts:
                continue

            yearly[year] = yearly.get(year, 0) + value

        for year, value in yearly.items():
            output.append(make_record(
                crop_id, year, value,
                measure, unit,
                "district",
                district,
                key
            ))

    return latest_by_measure(output)


@lru_cache(maxsize=32)
def sarawak_crop_statistics(crop_id):
    if crop_id not in CROP_NAMES:
        return []

    allowed = STATE_CATEGORIES.get(crop_id)

    if not allowed:
        # Do not construct a state-wide figure
        # from district records unless full
        # reporting coverage is independently verified.
        return []

    rows = download_dataset("state")

    if not rows:
        return []

    required = {
        "state", "crop_type", "date",
        "production", "planted_area"
    }

    if not required.issubset(rows[0].keys()):
        logger.warning("Unexpected state dataset schema")
        return []

    output = []

    for row in rows:
        if normalize(row.get("state")) != "sarawak":
            continue

        if normalize(row.get("crop_type")) not in allowed:
            continue

        year = year_of(row.get("date"))

        if year is None:
            continue

        for field, measure, unit in [
            ("production", "Production", "metric tonnes"),
            ("planted_area", "Planted area", "ha")
        ]:
            value = numeric(row.get(field))

            if value is None:
                continue

            output.append(make_record(
                crop_id, year, value,
                measure, unit,
                "state",
                None,
                "state"
            ))

    return latest_by_measure(output)


def select_market_evidence(crop_id, district=None):
    local = (
        district_crop_statistics(crop_id, district)
        if district else []
    )

    regional = sarawak_crop_statistics(crop_id)

    return {
        "selected_district": district,
        "district_statistics": local,
        "sarawak_statistics": regional,
        "display_statistics": local or regional,
        "evidence_scope": (
            "district" if local else "sarawak"
        ),
        "source_note": (
            "Historical cultivation statistics "
            "do not establish current market demand."
        )
    }


# ==========================================
# 6. PERSONALIZED MARKET STRATEGY
# ==========================================

def market_readiness(
    crop_id,
    buyer="unknown",
    transport="unknown",
    storage="unknown"
):
    """
    Generate a practical crop-specific market plan.

    Inputs are farmer-reported arrangements.
    Recommendations are rule-based, not AI-generated.

    Compatible with the existing:
    /market/readiness/{crop_id} endpoint.
    """

    if crop_id not in MARKET_PROFILES:
        return None

    allowed = {"yes", "no", "unknown"}

    answers = {
        "buyer": buyer if buyer in allowed else "unknown",
        "transport": (
            transport if transport in allowed
            else "unknown"
        ),
        "storage": (
            storage if storage in allowed
            else "unknown"
        )
    }

    profile = MARKET_PROFILES[crop_id]
    crop_name = CROP_NAMES[crop_id]

    actions = []

    def add_action(priority, title, description):
        actions.append({
            "priority": priority,
            "title": title,
            "description": description
        })

    # Prioritize the constraint most likely
    # to prevent successful marketing.

    if answers["buyer"] != "yes":
        add_action(
            1,
            "Identify a potential buyer",
            profile["selling"]
        )

    if answers["transport"] != "yes":
        add_action(
            2,
            "Arrange harvest transport",
            profile["delivery"]
        )

    if answers["storage"] != "yes":
        add_action(
            3,
            "Prepare post-harvest handling",
            profile["handling"]
        )

    add_action(
        4,
        "Confirm product specifications",
        profile["selling"]
    )

    # Crop-specific recommendation
    # takes priority over generic checklist text.

    if answers["buyer"] != "yes":
        headline = (
            "Confirm a suitable selling pathway "
            "before commercial planting."
        )

    elif answers["transport"] != "yes":
        headline = (
            "Secure a practical harvest-to-buyer "
            "delivery arrangement."
        )

    elif answers["storage"] != "yes":
        if crop_id == "cassava":
            headline = (
                "Arrange prompt cassava collection "
                "or processing before planting at scale."
            )
        elif crop_id in {
            "rice", "mung_bean",
            "groundnut", "soybean"
        }:
            headline = (
                "Prepare suitable drying and "
                "storage arrangements before harvest."
            )
        else:
            headline = (
                "Resolve crop handling and "
                "storage requirements before harvest."
            )

    else:
        headline = (
            "Confirm buyer terms and coordinate "
            "your crop-specific harvest schedule."
        )

    return {
        "crop_id": crop_id,
        "crop_name": crop_name,
        "headline": headline,
        "focus": profile["focus"],
        "handling_advice": profile["handling"],
        "selling_advice": profile["selling"],
        "delivery_advice": profile["delivery"],
        "products": profile["products"],
        "channels": profile["channels"],
        "postharvest": profile["postharvest"],
        "answers": answers,
        "recommended_actions": actions,
        "next_actions": [
            action["description"]
            for action in actions
        ],
        "interpretation": headline,
        "confirmed_arrangements": sum(
            value == "yes"
            for value in answers.values()
        ),
        "total_arrangements": 3,
        "note": (
            "Practical guidance based on farmer "
            "inputs and crop characteristics. "
            "Buyer availability and sales "
            "require local confirmation."
        )
    }


# ==========================================
# 7. PUBLIC BACKEND FUNCTIONS
# ==========================================

def get_sources():
    return [
        {"id": key, **value}
        for key, value in SOURCES.items()
    ]


def get_crop_market_profile(crop_id, district=None):
    if crop_id not in MARKET_PROFILES:
        return None

    profile = MARKET_PROFILES[crop_id]

    evidence = select_market_evidence(
        crop_id,
        district
    )

    return {
        "crop_id": crop_id,
        "name": CROP_NAMES[crop_id],
        **profile,
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
                "question": (
                    "Have you identified a potential buyer?"
                )
            },
            {
                "id": "transport",
                "question": (
                    "Can you transport your harvest?"
                )
            },
            {
                "id": "storage",
                "question": (
                    "Have you arranged suitable "
                    "handling or storage?"
                )
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

    for crop_id in [baseline, preferred_crop]:
        if (
            crop_id in MARKET_PROFILES
            and crop_id not in ids
        ):
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
        get_crop_market_profile(
            crop_id,
            district
        )
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
            "Statistics are restricted to Sarawak.",
            "Historical production does not prove demand.",
            "Buyer availability requires confirmation.",
            "No yield, revenue or profit is predicted."
        ]
    }


def get_all_crop_market_profiles(district=None):
    return {
        "region": "Sarawak, Malaysia",
        "district": district,
        "crop_count": len(MARKET_PROFILES),
        "crops": [
            get_crop_market_profile(
                crop_id,
                district
            )
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
            "Sarawak-only exact-crop observations"
        )
    }
