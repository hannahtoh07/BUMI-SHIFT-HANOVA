
"""
BUMI SHIFT 7.0
Market & Local Agricultural Insights Engine

HANOVA | Sarawak, Malaysia

Purpose
-------
Support practical crop-shifting decisions with:

1. Official Malaysian agricultural data sources
2. Sarawak agricultural context
3. Crop-specific selling considerations
4. Market access and post-harvest requirements
5. Verified price and production records, if supplied
6. Clear source attribution

NASA remains the primary environmental evidence source.

This engine does NOT:
- Invent market prices
- Predict crop demand
- Estimate revenue per hectare
- Estimate profit per hectare
- Rank crops by unsupported financial returns

Official links are provided for reference.
Live price retrieval is not assumed.
"""

from datetime import date
from math import isfinite


# ============================================
# 1. OFFICIAL DATA SOURCES
# ============================================

SOURCES = {
    "dosm": {
        "name": "Department of Statistics Malaysia",
        "short_name": "DOSM",
        "url": "https://open.dosm.gov.my/",
        "catalogue": (
            "https://open.dosm.gov.my/"
            "data-catalogue/crops_state"
        ),
        "purpose": (
            "Official state-level agricultural "
            "production and planted-area statistics."
        ),
        "geographic_scope": "Malaysia, including Sarawak",
        "data_type": "Agricultural statistics"
    },

    "sarawak": {
        "name": "Sarawak Government Open Data",
        "short_name": "Sarawak Open Data",
        "url": "https://data.sarawak.gov.my/",
        "purpose": (
            "Sarawak agricultural production, "
            "crop-area and regional information."
        ),
        "geographic_scope": "Sarawak, Malaysia",
        "data_type": "Regional government statistics"
    },

    "fama": {
        "name": "Federal Agricultural Marketing Authority",
        "short_name": "FAMA",
        "url": "https://www.fama.gov.my/",
        "catalogue": "https://ami.fama.gov.my/",
        "purpose": (
            "Agricultural farmgate, wholesale "
            "and retail market-price references."
        ),
        "geographic_scope": "Malaysia",
        "data_type": "Market-price information"
    },

    "doa": {
        "name": "Department of Agriculture Malaysia",
        "short_name": "DOA",
        "url": "https://www.doa.gov.my/",
        "purpose": (
            "Crop production, agricultural "
            "practices and sector information."
        ),
        "geographic_scope": "Malaysia",
        "data_type": "Agricultural reference"
    }
}


# ============================================
# 2. CROP MARKET CHARACTERISTICS
# ============================================

# These are qualitative considerations.
# They are not numerical market forecasts.

MARKET_PROFILES = {

    "rice": {
        "name": "Rice",
        "products": [
            "Paddy grain",
            "Milled rice"
        ],
        "channels": [
            "Paddy collection centres",
            "Licensed grain buyers",
            "Rice milling and processing"
        ],
        "postharvest": [
            "Moisture control",
            "Drying",
            "Grain grading",
            "Storage"
        ],
        "considerations": [
            "Confirm paddy purchasing arrangements.",
            "Check grain moisture and quality requirements.",
            "Review access to drying and milling facilities."
        ],
        "perishability": "Storage-sensitive"
    },

    "maize": {
        "name": "Maize",
        "products": [
            "Fresh sweet corn",
            "Grain maize"
        ],
        "channels": [
            "Fresh produce buyers",
            "Wholesale markets",
            "Grain buyers",
            "Processing channels"
        ],
        "postharvest": [
            "Harvest timing",
            "Drying for grain",
            "Grading",
            "Transport"
        ],
        "considerations": [
            "Confirm whether buyers want sweet corn or grain maize.",
            "Check variety and quality specifications.",
            "Plan transport and post-harvest handling."
        ],
        "perishability": "Depends on product type"
    },

    "mung_bean": {
        "name": "Mung Bean",
        "products": [
            "Dry mung beans",
            "Beans for processing"
        ],
        "channels": [
            "Grain traders",
            "Food processors",
            "Wholesale markets"
        ],
        "postharvest": [
            "Drying",
            "Cleaning",
            "Sorting",
            "Moisture-controlled storage"
        ],
        "considerations": [
            "Confirm local buyers before planting.",
            "Check acceptable grain quality and moisture.",
            "Review drying and storage facilities."
        ],
        "perishability": "Relatively storable when properly dried"
    },

    "groundnut": {
        "name": "Groundnut",
        "products": [
            "Fresh groundnuts",
            "Dried groundnuts",
            "Processed peanut products"
        ],
        "channels": [
            "Fresh produce markets",
            "Grain traders",
            "Food processors"
        ],
        "postharvest": [
            "Cleaning",
            "Drying",
            "Sorting",
            "Moisture control"
        ],
        "considerations": [
            "Confirm demand for fresh or dried groundnuts.",
            "Review drying requirements.",
            "Control moisture to reduce storage-quality risks."
        ],
        "perishability": "Moisture-sensitive"
    },

    "soybean": {
        "name": "Soybean",
        "products": [
            "Dry soybeans",
            "Food-processing beans"
        ],
        "channels": [
            "Grain traders",
            "Food processors",
            "Wholesale buyers"
        ],
        "postharvest": [
            "Drying",
            "Cleaning",
            "Grading",
            "Storage"
        ],
        "considerations": [
            "Identify buyers and quality specifications.",
            "Check drying and storage capacity.",
            "Confirm demand for locally grown varieties."
        ],
        "perishability": "Relatively storable when properly dried"
    },

    "sweet_potato": {
        "name": "Sweet Potato",
        "products": [
            "Fresh storage roots",
            "Processed sweet potato products"
        ],
        "channels": [
            "Fresh produce markets",
            "Retailers",
            "Food processors"
        ],
        "postharvest": [
            "Careful harvesting",
            "Sorting",
            "Curing where appropriate",
            "Storage"
        ],
        "considerations": [
            "Check demand for specific varieties and root sizes.",
            "Minimize root damage during harvesting.",
            "Plan transport and storage conditions."
        ],
        "perishability": "Fresh produce with storage limitations"
    },

    "cassava": {
        "name": "Cassava",
        "products": [
            "Fresh cassava roots",
            "Cassava flour",
            "Starch",
            "Processed cassava products"
        ],
        "channels": [
            "Local produce buyers",
            "Food processors",
            "Industrial processors"
        ],
        "postharvest": [
            "Prompt handling",
            "Transport scheduling",
            "Processing",
            "Variety identification"
        ],
        "considerations": [
            "Confirm whether buyers require fresh or processing cassava.",
            "Arrange prompt handling after harvest.",
            "Verify suitable varieties and safe processing requirements."
        ],
        "perishability": "Highly perishable fresh roots"
    },

    "pineapple": {
        "name": "Pineapple",
        "products": [
            "Fresh pineapple",
            "Processed pineapple products"
        ],
        "channels": [
            "Fresh produce markets",
            "Wholesale buyers",
            "Fruit processors"
        ],
        "postharvest": [
            "Harvest maturity assessment",
            "Fruit grading",
            "Careful handling",
            "Transport"
        ],
        "considerations": [
            "Confirm variety and fruit-size preferences.",
            "Coordinate harvest timing with buyers.",
            "Review fruit handling and transport arrangements."
        ],
        "perishability": "Perishable fresh fruit"
    },

    "banana": {
        "name": "Banana",
        "products": [
            "Fresh bananas",
            "Processed banana products"
        ],
        "channels": [
            "Fresh produce wholesalers",
            "Retail markets",
            "Food processors"
        ],
        "postharvest": [
            "Harvest maturity control",
            "Bunch handling",
            "Ripening management",
            "Transport"
        ],
        "considerations": [
            "Check buyer preferences for banana varieties.",
            "Plan ripening and delivery schedules.",
            "Reduce bruising during handling."
        ],
        "perishability": "Highly perishable fresh fruit"
    },

    "coconut": {
        "name": "Coconut",
        "products": [
            "Fresh coconuts",
            "Coconut water",
            "Coconut milk",
            "Processed coconut products"
        ],
        "channels": [
            "Fresh produce markets",
            "Food processors",
            "Coconut-product buyers"
        ],
        "postharvest": [
            "Harvest scheduling",
            "Sorting",
            "Storage",
            "Transport"
        ],
        "considerations": [
            "Check demand for young versus mature coconuts.",
            "Identify buyers before orchard establishment.",
            "Review harvesting labour and transport needs."
        ],
        "perishability": "Depends on maturity and product"
    },

    "durian": {
        "name": "Durian",
        "products": [
            "Fresh durian",
            "Frozen durian",
            "Processed durian products"
        ],
        "channels": [
            "Fresh fruit buyers",
            "Wholesale markets",
            "Fruit processors"
        ],
        "postharvest": [
            "Harvest timing",
            "Fruit grading",
            "Careful handling",
            "Cold-chain planning where needed"
        ],
        "considerations": [
            "Confirm demand for the selected cultivar.",
            "Plan harvesting, collection and transport.",
            "Review long-term buyer arrangements before planting."
        ],
        "perishability": "Highly perishable fresh fruit"
    }
}


# ============================================
# 3. VERIFIED NUMERICAL DATA
# ============================================

# This dictionary is deliberately empty.
#
# Numerical records should only be inserted
# after checking the original government
# publication or official dataset.
#
# Each record must include:
# - value
# - unit
# - year or observation date
# - source
# - geographic coverage
#
# Price records must also include:
# - market level (farmgate, wholesale, retail)
#
# Do not place unverified figures here.

VERIFIED_RECORDS = {}


# ============================================
# 4. VALIDATION
# ============================================

def valid_number(value):
    return (
        isinstance(value, (int, float))
        and not isinstance(value, bool)
        and isfinite(value)
    )


def validate_record(record):
    """
    Validate a numerical market or
    agricultural statistics record.

    This validates structure, not the
    truth of the original source.
    """

    required = [
        "value",
        "unit",
        "source",
        "geographic_coverage"
    ]

    for field in required:
        if not record.get(field) and record.get(field) != 0:
            return False

    if not valid_number(record["value"]):
        return False

    if (
        not record.get("year")
        and not record.get("date")
    ):
        return False

    if record.get("type") == "price":
        if record.get("market_level") not in {
            "farmgate",
            "wholesale",
            "retail"
        }:
            return False

    return True


# ============================================
# 5. SOURCE DIRECTORY
# ============================================

def get_sources():

    return [
        {
            "id": source_id,
            **details
        }
        for source_id, details
        in SOURCES.items()
    ]


# ============================================
# 6. CROP MARKET PROFILE
# ============================================

def get_crop_market_profile(crop_id):

    profile = MARKET_PROFILES.get(
        crop_id
    )

    if profile is None:
        return None

    records = [
        record
        for record in VERIFIED_RECORDS.get(
            crop_id, []
        )
        if validate_record(record)
    ]

    return {
        "crop_id": crop_id,
        **profile,
        "verified_statistics": records,
        "numerical_data_available": bool(records),
        "market_price_status": (
            "verified_records_available"
            if any(
                record.get("type") == "price"
                for record in records
            )
            else "no_verified_price_record"
        ),
        "sources": get_sources()
    }


# ============================================
# 7. FARM MARKET ASSESSMENT
# ============================================

def build_market_assessment(
    preferred_crop="auto",
    baseline="rice",
    selected_strategy=None
):
    """
    Build market information for the
    farmer's selected scenario.

    Market evidence is kept separate
    from NASA climate compatibility.
    """

    selected_ids = []

    if baseline in MARKET_PROFILES:
        selected_ids.append(baseline)

    if (
        preferred_crop != "auto"
        and preferred_crop in MARKET_PROFILES
        and preferred_crop not in selected_ids
    ):
        selected_ids.append(
            preferred_crop
        )

    if selected_strategy:

        for crop_id in selected_strategy.get(
            "crop_ids", []
        ):
            if (
                crop_id in MARKET_PROFILES
                and crop_id not in selected_ids
            ):
                selected_ids.append(
                    crop_id
                )

    profiles = [
        get_crop_market_profile(crop_id)
        for crop_id in selected_ids
    ]

    profiles = [
        profile
        for profile in profiles
        if profile is not None
    ]

    return {
        "region": "Sarawak, Malaysia",
        "generated_on": date.today().isoformat(),
        "preferred_crop": preferred_crop,
        "baseline": baseline,
        "crop_profiles": profiles,
        "official_sources": get_sources(),
        "verified_price_records": sum(
            1
            for profile in profiles
            for record in profile[
                "verified_statistics"
            ]
            if record.get("type") == "price"
        ),
        "price_data_integrated": any(
            profile["market_price_status"]
            == "verified_records_available"
            for profile in profiles
        ),
        "limitations": [
            "Market characteristics are qualitative guidance.",
            "Market prices are not retrieved automatically.",
            "Official source links do not imply live data integration.",
            "Local buyer availability requires verification.",
            "No revenue, profit or crop-yield predictions are generated."
        ]
    }


# ============================================
# 8. ALL-CROP MARKET OVERVIEW
# ============================================

def get_all_crop_market_profiles():

    return {
        "region": "Sarawak, Malaysia",
        "crop_count": len(MARKET_PROFILES),
        "crops": [
            get_crop_market_profile(crop_id)
            for crop_id in MARKET_PROFILES
        ],
        "official_sources": get_sources(),
        "generated_on": date.today().isoformat()
    }


# ============================================
# 9. MARKET DATA TRANSPARENCY
# ============================================

def market_data_status():

    total_records = sum(
        len([
            record
            for record in records
            if validate_record(record)
        ])
        for records in VERIFIED_RECORDS.values()
    )

    return {
        "region": "Sarawak, Malaysia",
        "official_source_count": len(SOURCES),
        "crop_profile_count": len(MARKET_PROFILES),
        "verified_numerical_records": total_records,
        "live_price_api_connected": False,
        "revenue_estimation_enabled": False,
        "profit_estimation_enabled": False,
        "primary_environmental_source": "NASA POWER",
        "note": (
            "Market information supports practical "
            "decision-making but does not determine "
            "climate compatibility."
        )
    }
