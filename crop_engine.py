
"""
BUMI SHIFT 5.0 — Crop Intelligence Engine
HANOVA | Sarawak, Malaysia

Compatible with:
backend.py
climate_engine.py
static/index.html

IMPORTANT:
Crop thresholds are provisional prototype assumptions.
Scores are climate screening indices, not predictions
of crop success, yield, profit or soil improvement.
"""

from datetime import date
from calendar import monthrange
from statistics import mean


# ============================================
# 1. SARAWAK CROP CANDIDATES
# ============================================

# temp: monthly mean temperature (C)
# rain: monthly precipitation total (mm)
# months: approximate growing duration
#
# Numerical ranges below are NOT verified FAO
# requirements. They are prototype assumptions.

CROPS = {
    "rice": {
        "name": "Rice",
        "family": "Poaceae",
        "kind": "annual",
        "months": 4,
        "temp": (22, 34),
        "rain": (130, 450)
    },
    "maize": {
        "name": "Maize",
        "family": "Poaceae",
        "kind": "annual",
        "months": 4,
        "temp": (20, 33),
        "rain": (65, 240)
    },
    "mung_bean": {
        "name": "Mung Bean",
        "family": "Fabaceae",
        "kind": "annual",
        "months": 3,
        "temp": (23, 33),
        "rain": (45, 180)
    },
    "groundnut": {
        "name": "Groundnut",
        "family": "Fabaceae",
        "kind": "annual",
        "months": 4,
        "temp": (22, 32),
        "rain": (55, 220)
    },
    "soybean": {
        "name": "Soybean",
        "family": "Fabaceae",
        "kind": "annual",
        "months": 4,
        "temp": (20, 32),
        "rain": (65, 240)
    },
    "sweet_potato": {
        "name": "Sweet Potato",
        "family": "Convolvulaceae",
        "kind": "annual",
        "months": 4,
        "temp": (21, 34),
        "rain": (55, 260)
    },
    "cassava": {
        "name": "Cassava",
        "family": "Euphorbiaceae",
        "kind": "long_duration",
        "months": 10,
        "temp": (21, 34),
        "rain": (65, 280)
    },
    "pineapple": {
        "name": "Pineapple",
        "family": "Bromeliaceae",
        "kind": "long_duration",
        "months": 16,
        "temp": (20, 33),
        "rain": (65, 300)
    },
    "banana": {
        "name": "Banana",
        "family": "Musaceae",
        "kind": "perennial",
        "months": 12,
        "temp": (23, 34),
        "rain": (110, 380)
    },
    "coconut": {
        "name": "Coconut",
        "family": "Arecaceae",
        "kind": "perennial",
        "months": 36,
        "temp": (23, 34),
        "rain": (100, 400)
    },
    "durian": {
        "name": "Durian",
        "family": "Malvaceae",
        "kind": "perennial",
        "months": 60,
        "temp": (22, 33),
        "rain": (120, 430)
    }
}


# ============================================
# 2. CLIMATE SCREENING FUNCTION
# ============================================

def closeness(value, low, high):

    if value is None:
        return None

    if low <= value <= high:
        return 1.0

    margin = max((high - low) * 0.5, 1.0)

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
# 3. HISTORICAL MONTHLY CLIMATE
# ============================================

def month_climatology(history):

    grouped = {
        month: {"rain": [], "temp": []}
        for month in range(1, 13)
    }

    for row in history.get("monthly", []):

        month_text = str(row["month"])

        if "-" in month_text:
            year, month = map(
                int, month_text.split("-")
            )
        else:
            year = None
            month = int(month_text)

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

        if rain_complete is None and year:
            valid_days = row.get(
                "rainfall_valid_days"
            )
            rain_complete = (
                valid_days == monthrange(
                    year, month
                )[1]
                if valid_days is not None
                else False
            )

        if rainfall is not None and rain_complete:
            grouped[month]["rain"].append(
                rainfall
            )

        if temperature is not None:
            grouped[month]["temp"].append(
                temperature
            )

    results = []

    for month in range(1, 13):

        rain = grouped[month]["rain"]
        temp = grouped[month]["temp"]

        results.append({
            "month": month,
            "rainfall_mm": (
                round(mean(rain), 2)
                if rain else None
            ),
            "temperature_c": (
                round(mean(temp), 2)
                if temp else None
            ),
            "rainfall_years": len(rain),
            "temperature_years": len(temp)
        })

    return results


# ============================================
# 4. CROP COMPATIBILITY SCREENING
# ============================================

def screen_crop(crop_id, monthly):

    crop = CROPS[crop_id]

    # For perennial crops, this examines only
    # a representative 12-month climate cycle.
    duration = min(crop["months"], 12)

    windows = []

    for start in range(12):

        scores = []
        valid = True

        for offset in range(duration):

            month_index = (start + offset) % 12
            row = monthly[month_index]

            rain_score = closeness(
                row["rainfall_mm"],
                *crop["rain"]
            )

            temp_score = closeness(
                row["temperature_c"],
                *crop["temp"]
            )

            if (
                rain_score is None
                or temp_score is None
            ):
                valid = False
                break

            scores.append(
                0.55 * rain_score
                + 0.45 * temp_score
            )

        if valid and scores:

            windows.append({
                "start_month": start + 1,
                "climate_score": round(
                    mean(scores) * 100, 1
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
        "suggested_start_month": (
            best["start_month"]
            if best else None
        ),
        "alternative_windows": windows[:3],
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
# 5. ROTATION COMPARISON
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

        if any(score is None for score in scores):
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

        # Experimental index.
        # NOT a prediction of soil-health change.
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
                screening_index, 1
            ),
            "climate_component": round(
                climate_component, 1
            ),
            "diversity_component": round(
                diversity_component, 1
            ),
            "includes_legume": includes_legume,
            "approx_total_months": sum(
                CROPS[crop_id]["months"]
                for crop_id in sequence
            ),
            "note": (
                "Experimental comparison only. "
                "Continuous planting-calendar, "
                "soil and economic feasibility "
                "are not yet validated."
            )
        })

    rotations.sort(
        key=lambda item: item["screening_index"],
        reverse=True
    )

    return rotations


# ============================================
# 6. FARMING ACTIVITY SUGGESTIONS
# ============================================

def generate_activities(rotations):

    activities = [
        {
            "category": "Planting",
            "title": "Review planting windows",
            "reason": (
                "Compare historical rainfall and "
                "temperature patterns with crop needs."
            )
        },
        {
            "category": "Soil Health",
            "title": "Maintain soil cover",
            "reason": (
                "Appropriate mulch and crop residues "
                "may reduce exposed-soil periods."
            )
        },
        {
            "category": "Water Management",
            "title": "Check drainage conditions",
            "reason": (
                "Regional rainfall does not establish "
                "field-level drainage performance."
            )
        },
        {
            "category": "Nutrient Management",
            "title": "Plan residue management",
            "reason": (
                "Residue handling affects nutrient "
                "cycling and soil organic matter."
            )
        }
    ]

    if rotations and rotations[0]["includes_legume"]:

        activities.append({
            "category": "Crop Rotation",
            "title": "Explore legume integration",
            "reason": (
                "Legumes may support nitrogen "
                "management when nodulation and "
                "residue practices are appropriate."
            )
        })

    return activities


# ============================================
# 7. MAIN BACKEND FUNCTION
# ============================================

def build_recommendations(
    latitude,
    longitude,
    history
):

    monthly = month_climatology(history)

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
        "limitations": [
            "Crop thresholds are prototype assumptions.",
            "Scores are not probabilities of success.",
            "Historical climate is not a forecast.",
            "Rotation calendar feasibility is not validated.",
            "Soil conditions are not measured at field scale.",
            "Yield, profit and soil improvement are not predicted."
        ]
    }
