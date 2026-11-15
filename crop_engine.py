
"""
BUMI SHIFT 6.5 — Crop Intelligence Engine
HANOVA | Sarawak, Malaysia

Compatible with:
- climate_engine.py 6.4
- strategy_engine.py
- backend.py
- static/index.html

Features:
- 11 crop candidates
- NASA monthly climate compatibility
- Candidate planting windows
- Crop-specific rainfall and temperature evidence
- Preliminary crop rotation screening
- Compatibility with existing strategy engine

Crop thresholds and weights are provisional.
Scores are not probabilities of cultivation success.
"""

from datetime import date
from calendar import monthrange
from statistics import mean
import math


# ============================================
# 1. CROP LIBRARY
# ============================================

# temp: monthly mean temperature (C)
# rain: monthly precipitation (mm)
# months: approximate growing duration
# cover: experimental management proxy,
# not measured vegetation or soil cover.

CROPS = {
    "rice": {
        "name": "Rice",
        "family": "Poaceae",
        "kind": "annual",
        "months": 4,
        "temp": (22, 34),
        "rain": (130, 450),
        "cover": 0.60
    },
    "maize": {
        "name": "Maize",
        "family": "Poaceae",
        "kind": "annual",
        "months": 4,
        "temp": (20, 33),
        "rain": (65, 240),
        "cover": 0.50
    },
    "mung_bean": {
        "name": "Mung Bean",
        "family": "Fabaceae",
        "kind": "annual",
        "months": 3,
        "temp": (23, 33),
        "rain": (45, 180),
        "cover": 0.65
    },
    "groundnut": {
        "name": "Groundnut",
        "family": "Fabaceae",
        "kind": "annual",
        "months": 4,
        "temp": (22, 32),
        "rain": (55, 220),
        "cover": 0.60
    },
    "soybean": {
        "name": "Soybean",
        "family": "Fabaceae",
        "kind": "annual",
        "months": 4,
        "temp": (20, 32),
        "rain": (65, 240),
        "cover": 0.65
    },
    "sweet_potato": {
        "name": "Sweet Potato",
        "family": "Convolvulaceae",
        "kind": "annual",
        "months": 4,
        "temp": (21, 34),
        "rain": (55, 260),
        "cover": 0.85
    },
    "cassava": {
        "name": "Cassava",
        "family": "Euphorbiaceae",
        "kind": "long_duration",
        "months": 10,
        "temp": (21, 34),
        "rain": (65, 280),
        "cover": 0.55
    },
    "pineapple": {
        "name": "Pineapple",
        "family": "Bromeliaceae",
        "kind": "long_duration",
        "months": 16,
        "temp": (20, 33),
        "rain": (65, 300),
        "cover": 0.65
    },
    "banana": {
        "name": "Banana",
        "family": "Musaceae",
        "kind": "perennial",
        "months": 12,
        "temp": (23, 34),
        "rain": (110, 380),
        "cover": 0.80
    },
    "coconut": {
        "name": "Coconut",
        "family": "Arecaceae",
        "kind": "perennial",
        "months": 36,
        "temp": (23, 34),
        "rain": (100, 400),
        "cover": 0.80
    },
    "durian": {
        "name": "Durian",
        "family": "Malvaceae",
        "kind": "perennial",
        "months": 60,
        "temp": (22, 33),
        "rain": (120, 430),
        "cover": 0.80
    }
}


# ============================================
# 2. DATA VALIDATION
# ============================================

def valid(value):
    return (
        isinstance(value, (int, float))
        and not isinstance(value, bool)
        and math.isfinite(value)
    )


def safe_mean(values):
    numbers = [
        float(v)
        for v in values
        if valid(v)
    ]

    if not numbers:
        return None

    return round(mean(numbers), 2)


def closeness(value, low, high):
    """
    Experimental compatibility function.

    1.0: within assumed screening interval
    0.0: outside tolerance interval

    This is not a crop-success probability.
    """

    if not valid(value):
        return None

    if low <= value <= high:
        return 1.0

    margin = max(
        (high - low) * 0.5,
        1.0
    )

    distance = (
        low - value
        if value < low
        else value - high
    )

    return max(
        0.0,
        1.0 - distance / margin
    )


# ============================================
# 3. MONTHLY CLIMATE COMPATIBILITY
# ============================================

def month_climatology(history):
    """
    Accepts either:

    A. New climate_engine.py 6.4:
       month = 1 ... 12
       rainfall_mm = monthly climatology

    B. Older climate engine:
       month = '2025-01'
       rainfall_complete = True

    IMPORTANT:
    Aggregated monthly climatology must NOT be
    rejected because rainfall_complete is absent.
    """

    direct = history.get(
        "monthly_climatology"
    )

    if direct is None:
        direct = history.get("monthly", [])

    # New 12-month climatology.
    if (
        len(direct) == 12
        and all(
            isinstance(row.get("month"), int)
            and 1 <= row["month"] <= 12
            for row in direct
        )
    ):

        by_month = {
            row["month"]: row
            for row in direct
        }

        output = []

        for month in range(1, 13):

            row = by_month[month]

            rainfall = row.get("rainfall_mm")

            temperature = row.get(
                "temperature_c",
                row.get("t2m")
            )

            output.append({
                "month": month,
                "rainfall_mm": (
                    rainfall
                    if valid(rainfall)
                    else None
                ),
                "temperature_c": (
                    temperature
                    if valid(temperature)
                    else None
                ),
                "rainfall_years": row.get(
                    "rainfall_years",
                    row.get(
                        "rainfall_mm_years",
                        0
                    )
                ),
                "temperature_years": row.get(
                    "temperature_years",
                    row.get(
                        "temperature_c_years",
                        0
                    )
                )
            })

        return output

    # Older year-month observations.
    records = history.get(
        "historical_monthly",
        history.get("monthly", [])
    )

    grouped = {
        month: {
            "rain": [],
            "temp": []
        }
        for month in range(1, 13)
    }

    for row in records:

        raw_month = row.get("month")

        try:
            if isinstance(raw_month, str) and "-" in raw_month:
                year, month = map(
                    int,
                    raw_month.split("-")
                )
            else:
                month = int(raw_month)
                year = row.get("year")
        except (ValueError, TypeError):
            continue

        if month not in grouped:
            continue

        rainfall = row.get("rainfall_mm")
        temperature = row.get(
            "temperature_c",
            row.get("t2m")
        )

        rain_complete = row.get(
            "rainfall_complete"
        )

        # For historical year-month records,
        # rainfall completeness is required.
        if rain_complete is None and year is not None:

            valid_days = row.get(
                "rainfall_valid_days"
            )

            if valid_days is not None:
                rain_complete = (
                    valid_days
                    == monthrange(
                        int(year),
                        month
                    )[1]
                )

        if valid(rainfall) and rain_complete is True:
            grouped[month]["rain"].append(
                rainfall
            )

        if valid(temperature):
            grouped[month]["temp"].append(
                temperature
            )

    output = []

    for month in range(1, 13):

        rain = grouped[month]["rain"]
        temp = grouped[month]["temp"]

        output.append({
            "month": month,
            "rainfall_mm": safe_mean(rain),
            "temperature_c": safe_mean(temp),
            "rainfall_years": len(rain),
            "temperature_years": len(temp)
        })

    return output


# ============================================
# 4. CROP COMPATIBILITY SCREENING
# ============================================

def screen_crop(crop_id, monthly):

    crop = CROPS[crop_id]

    # Perennial and long-duration crops are
    # screened against a representative
    # annual climate cycle.
    duration = min(
        crop["months"],
        12
    )

    windows = []

    for start in range(12):

        monthly_scores = []
        rainfall_scores = []
        temperature_scores = []

        rainfall_values = []
        temperature_values = []

        valid_window = True

        for offset in range(duration):

            index = (start + offset) % 12
            row = monthly[index]

            rainfall = row.get("rainfall_mm")
            temperature = row.get(
                "temperature_c"
            )

            rain_score = closeness(
                rainfall,
                *crop["rain"]
            )

            temp_score = closeness(
                temperature,
                *crop["temp"]
            )

            if rain_score is None or temp_score is None:
                valid_window = False
                break

            rainfall_scores.append(rain_score)
            temperature_scores.append(temp_score)

            rainfall_values.append(rainfall)
            temperature_values.append(temperature)

            monthly_scores.append(
                0.55 * rain_score
                + 0.45 * temp_score
            )

        if not valid_window or not monthly_scores:
            continue

        windows.append({
            "start_month": start + 1,
            "climate_score": round(
                mean(monthly_scores) * 100,
                1
            ),
            "rainfall_component": round(
                mean(rainfall_scores) * 100,
                1
            ),
            "temperature_component": round(
                mean(temperature_scores) * 100,
                1
            ),
            "mean_rainfall_mm": safe_mean(
                rainfall_values
            ),
            "mean_temperature_c": safe_mean(
                temperature_values
            )
        })

    windows.sort(
        key=lambda item: item["climate_score"],
        reverse=True
    )

    best = windows[0] if windows else None

    return {
        "id": crop_id,
        "name": crop["name"],
        "family": crop["family"],
        "kind": crop["kind"],
        "approx_duration_months": crop["months"],

        "climate_score": (
            best["climate_score"]
            if best else None
        ),

        "rainfall_component": (
            best["rainfall_component"]
            if best else None
        ),

        "temperature_component": (
            best["temperature_component"]
            if best else None
        ),

        "suggested_start_month": (
            best["start_month"]
            if best else None
        ),

        "alternative_windows": windows[:3],

        "climate_evidence": {
            "mean_rainfall_mm": (
                best["mean_rainfall_mm"]
                if best else None
            ),
            "mean_temperature_c": (
                best["mean_temperature_c"]
                if best else None
            ),
            "rainfall_weight": 0.55,
            "temperature_weight": 0.45
        },

        "status": (
            "provisional climate screening"
            if best
            else "insufficient climate data"
        ),

        "thresholds": {
            "monthly_rainfall_mm": crop["rain"],
            "mean_temperature_c": crop["temp"]
        }
    }


# ============================================
# 5. PRELIMINARY ROTATION COMPARISON
# ============================================

ROTATION_SEQUENCES = [
    ["rice", "mung_bean", "rice"],
    ["rice", "groundnut", "rice"],
    ["rice", "maize", "rice"],
    ["maize", "soybean", "maize"],
    ["maize", "sweet_potato", "mung_bean"]
]


def evaluate_rotations(crop_results):

    by_id = {
        crop["id"]: crop
        for crop in crop_results
    }

    rotations = []

    for sequence in ROTATION_SEQUENCES:

        scores = [
            by_id[crop_id]["climate_score"]
            for crop_id in sequence
        ]

        if any(
            score is None
            for score in scores
        ):
            continue

        climate_component = mean(scores)

        families = {
            CROPS[crop_id]["family"]
            for crop_id in sequence
        }

        diversity_component = (
            len(families) / len(sequence)
        ) * 100

        includes_legume = any(
            CROPS[crop_id]["family"] == "Fabaceae"
            for crop_id in sequence
        )

        screening_index = (
            0.8 * climate_component
            + 0.2 * diversity_component
        )

        rotations.append({
            "id": "-".join(sequence),
            "crop_ids": sequence,
            "crops": [
                CROPS[crop_id]["name"]
                for crop_id in sequence
            ],
            "screening_index": round(
                screening_index,
                1
            ),
            "climate_component": round(
                climate_component,
                1
            ),
            "diversity_component": round(
                diversity_component,
                1
            ),
            "includes_legume": includes_legume,
            "approx_total_months": sum(
                CROPS[crop_id]["months"]
                for crop_id in sequence
            ),
            "note": (
                "Experimental rotation screening. "
                "Calendar, soil and economic "
                "feasibility require further review."
            )
        })

    rotations.sort(
        key=lambda item: item["screening_index"],
        reverse=True
    )

    return rotations


# ============================================
# 6. FARMING ACTIVITIES
# ============================================

def generate_activities(rotations):

    activities = []

    if not rotations:
        return activities

    best = rotations[0]

    activities.append({
        "category": "Crop rotation",
        "title": "Review the proposed crop sequence",
        "reason": (
            "Explore "
            + " → ".join(best["crops"])
            + " and compare its climate screening "
            "with your current cropping practice."
        )
    })

    activities.append({
        "category": "Planting schedule",
        "title": "Review seasonal planting windows",
        "reason": (
            "Compare historical NASA rainfall "
            "and temperature patterns with "
            "the proposed crop sequence."
        )
    })

    if best["includes_legume"]:

        activities.append({
            "category": "Nutrient management",
            "title": "Review legume establishment",
            "reason": (
                "The selected sequence contains a legume. "
                "Check nodulation, residue handling "
                "and local growing conditions."
            )
        })

    activities.append({
        "category": "Soil protection",
        "title": "Plan soil-cover management",
        "reason": (
            "Review mulch, crop residues or "
            "appropriate ground-cover practices "
            "during transitions between crops."
        )
    })

    return activities


# ============================================
# 7. MAIN RECOMMENDATION FUNCTION
# ============================================

def build_recommendations(
    latitude,
    longitude,
    history
):

    monthly = month_climatology(history)

    if len(monthly) != 12:
        raise ValueError(
            "Expected 12 monthly climate records."
        )

    crop_results = [
        screen_crop(crop_id, monthly)
        for crop_id in CROPS
    ]

    crop_results.sort(
        key=lambda item: (
            item["climate_score"]
            if item["climate_score"] is not None
            else -1
        ),
        reverse=True
    )

    rotations = evaluate_rotations(
        crop_results
    )

    return {
        "region": "Sarawak, Malaysia",
        "latitude": latitude,
        "longitude": longitude,
        "generated_on": date.today().isoformat(),

        "climate_period": [
            history.get("start_year"),
            history.get("end_year")
        ],

        "source": history.get("source"),

        "monthly_climatology": monthly,

        "crop_recommendations": crop_results,

        "rotation_options": rotations,

        "suggested_activities": (
            generate_activities(rotations)
        ),

        "summary": history.get(
            "summary",
            {}
        ),

        "limitations": [
            "Crop climate thresholds are provisional assumptions.",
            "Scores are not probabilities of cultivation success.",
            "Historical climate is not a future forecast.",
            "Soil pH and field drainage are not measured.",
            "Rotation and economic feasibility need local review."
        ]
    }
