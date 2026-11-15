
"""
BUMI SHIFT 7.1
Market & Local Agricultural Insights Engine

HANOVA | Sarawak, Malaysia

Purpose:
- Provide market context for all 11 crops
- Explain crop-specific selling considerations
- Identify potential marketing channels
- Provide official Malaysian and Sarawak data sources
- Support personalized crop-shifting decisions
- Accept independently verified numerical records

NASA POWER remains the primary environmental
evidence source for BUMI SHIFT.

This engine does NOT:
- Invent market prices
- Predict market demand
- Estimate revenue per hectare
- Estimate profit per hectare
- Predict crop yields
- Claim live FAMA API integration

Market information is supplementary to the
NASA-powered crop and rotation assessment.
"""

from datetime import date
from math import isfinite


# ============================================
# 1. OFFICIAL DATA SOURCE DIRECTORY
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
        "geographic_scope": (
            "Malaysia, including Sarawak"
        ),
        "data_type": "Agricultural statistics"
    },

    "sarawak": {
        "name": "Sarawak Government Open Data",
        "short_name": "Sarawak Open Data",
        "url": "https://data.sarawak.gov.my/",
        "purpose": (
            "Regional agricultural production, "
            "crop-area statistics and publications."
        ),
        "geographic_scope": "Sarawak, Malaysia",
        "data_type": "Regional government statistics"
    },

    "fama": {
        "name": (
            "Federal Agricultural Marketing Authority"
        ),
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
# 2. MARKET PROFILES FOR ALL 11 CROPS
# ============================================

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
        "perishability": (
            "Relatively storable when properly dried"
        )
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
        "perishability": (
            "Relatively storable when properly dried"
        )
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
        "perishability": (
            "Fresh produce with storage limitations"
        )
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
        "perishability": (
            "Depends on maturity and product"
        )
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
# 3. VERIFIED NUMERICAL RECORDS
# ============================================

# Numerical government statistics or market
# prices can be added here after independent
# source verification.
#
# Required fields:
#
# {
#     "type": "price" or "production",
#     "value": numeric value,
#     "unit": "RM/kg", "tonnes", "ha", etc.,
#     "year": 2025 or "date": "2025-01-01",
#     "source": "FAMA" or "DOSM",
#     "geographic_coverage": "Sarawak, Malaysia",
#     "source_url": "official source URL"
# }
#
# Price records additionally require:
# "market_level": "farmgate", "wholesale",
#                 or "retail"
#
# No unverified numerical values are included.

VERIFIED_RECORDS = {}


# ============================================
# 4. NUMERICAL RECORD VALIDATION
# ============================================

def valid_number(value):

    return (
        isinstance(value, (int, float))
        and not isinstance(value, bool)
        and isfinite(value)
    )


def validate_record(record):
    """
    Check the structure of a supplied record.

    Passing validation does not independently
    verify the original source's accuracy.
    """

    if not isinstance(record, dict):
        return False

    required = [
        "value",
        "unit",
        "source",
        "geographic_coverage",
        "source_url"
    ]

    for field in required:
        if field not in record:
            return False

        if field != "value" and not record[field]:
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
# 5. OFFICIAL SOURCE DIRECTORY
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
# 6. INDIVIDUAL CROP MARKET PROFILE
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

    has_prices = any(
        record.get("type") == "price"
        for record in records
    )

    return {
        "crop_id": crop_id,
        **profile,
        "verified_statistics": records,
        "numerical_data_available": bool(records),
        "market_price_status": (
            "verified_records_available"
            if has_prices
            else "no_verified_price_record"
        ),
        "sources": get_sources()
    }


# ============================================
# 7. PERSONALIZED MARKET ASSESSMENT
# ============================================

def build_market_assessment(
    preferred_crop="auto",
    baseline="rice",
    selected_strategy=None
):
    """
    Build crop-specific market information
    for the farmer's current assessment.

    This does not modify the NASA climate
    compatibility scores.
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

    verified_price_count = sum(
        1
        for profile in profiles
        for record in profile[
            "verified_statistics"
        ]
        if record.get("type") == "price"
    )

    return {
        "region": "Sarawak, Malaysia",
        "generated_on": date.today().isoformat(),
        "preferred_crop": preferred_crop,
        "baseline": baseline,
        "crop_profiles": profiles,
        "official_sources": get_sources(),
        "verified_price_records": (
            verified_price_count
        ),
        "price_data_integrated": (
            verified_price_count > 0
        ),
        "limitations": [
            "Market characteristics are qualitative guidance.",
            "Market prices are not automatically retrieved.",
            "Official source links do not imply live data integration.",
            "Local buyer availability requires verification.",
            "No revenue or profit predictions are generated."
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
# 9. MARKET DATA STATUS
# ============================================

def market_data_status():

    valid_records = [
        record
        for records in VERIFIED_RECORDS.values()
        for record in records
        if validate_record(record)
    ]

    return {
        "region": "Sarawak, Malaysia",
        "official_source_count": len(SOURCES),
        "crop_profile_count": len(MARKET_PROFILES),
        "verified_numerical_records": len(
            valid_records
        ),
        "live_price_api_connected": False,
        "revenue_estimation_enabled": False,
        "profit_estimation_enabled": False,
        "primary_environmental_source": (
            "NASA POWER"
        ),
        "note": (
            "Market information supports "
            "practical farming decisions "
            "but does not determine "
            "climate compatibility."
        )
    }
