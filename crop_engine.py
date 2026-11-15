
"""
BUMI SHIFT 7.0
Crop Intelligence and Environmental Screening Engine

HANOVA | Sarawak, Malaysia

This engine:
- Screens 11 crops against NASA POWER climate data.
- Evaluates historical monthly rainfall and temperature.
- Identifies candidate planting windows.
- Produces explainable crop-specific evidence.
- Preserves compatibility with strategy_engine.py.
- Separates annual crops from long-duration and perennial crops.

Scientific limitations:
- Crop thresholds are provisional screening assumptions.
- Compatibility scores are not probabilities of crop success.
- Historical observations are not weather forecasts.
- Field drainage, soil pH, pests and market conditions
  require additional evidence.
"""

from datetime import date
from calendar import monthrange
from statistics import mean
import math


# ============================================
# 1. CROP LIBRARY
# ============================================

CROPS = {
    "rice": {
        "name": "Rice",
        "family": "Poaceae",
        "kind": "annual",
        "months": 4,
        "temp": (22, 34),
        "rain": (130, 450),
        "cover": 0.60,
        "water_sensitivity": "managed_paddy",
        "planting_system": "paddy",
        "description": (
            "Rice may be cultivated in managed paddy "
            "systems where water control is available."
        )
    },

    "maize": {
        "name": "Maize",
        "family": "Poaceae",
        "kind": "annual",
        "months": 4,
        "temp": (20, 33),
        "rain": (65, 240),
        "cover": 0.50,
        "water_sensitivity": "waterlogging_sensitive",
        "planting_system": "upland_rows",
        "description": (
            "Maize requires suitable drainage and "
            "adequate moisture during key growth stages."
        )
    },

    "mung_bean": {
        "name": "Mung Bean",
        "family": "Fabaceae",
        "kind": "annual",
        "months": 3,
        "temp": (23, 33),
        "rain": (45, 180),
        "cover": 0.65,
        "water_sensitivity": "waterlogging_sensitive",
        "planting_system": "upland_rows",
        "description": (
            "Mung bean is a short-duration legume. "
            "Potential nitrogen benefits depend on "
            "effective nodulation and residue management."
        )
    },

    "groundnut": {
        "name": "Groundnut",
        "family": "Fabaceae",
        "kind": "annual",
        "months": 4,
        "temp": (22, 32),
        "rain": (55, 220),
        "cover": 0.60,
        "water_sensitivity": "waterlogging_sensitive",
        "planting_system": "raised_beds",
        "description": (
            "Groundnut requires suitable soil conditions "
            "for pegging and pod development."
        )
    },

    "soybean": {
        "name": "Soybean",
        "family": "Fabaceae",
        "kind": "annual",
        "months": 4,
        "temp": (20, 32),
        "rain": (65, 240),
        "cover": 0.65,
        "water_sensitivity": "waterlogging_sensitive",
        "planting_system": "upland_rows",
        "description": (
            "Soybean can diversify a crop rotation, "
            "but effective nodulation, drainage and "
            "local cultivar suitability must be checked."
        )
    },

    "sweet_potato": {
        "name": "Sweet Potato",
        "family": "Convolvulaceae",
        "kind": "annual",
        "months": 4,
        "temp": (21, 34),
        "rain": (55, 260),
        "cover": 0.85,
        "water_sensitivity": "waterlogging_sensitive",
        "planting_system": "raised_beds",
        "description": (
            "Sweet potato develops storage roots and "
            "generally benefits from well-drained soil "
            "and appropriate bed preparation."
        )
    },

    "cassava": {
        "name": "Cassava",
        "family": "Euphorbiaceae",
        "kind": "long_duration",
        "months": 10,
        "temp": (21, 34),
        "rain": (65, 280),
        "cover": 0.55,
        "water_sensitivity": "waterlogging_sensitive",
        "planting_system": "upland_rows",
        "description": (
            "Cassava is a longer-duration root crop. "
            "Drainage, soil conservation and planting "
            "material quality require attention."
        )
    },

    "pineapple": {
        "name": "Pineapple",
        "family": "Bromeliaceae",
        "kind": "long_duration",
        "months": 16,
        "temp": (20, 33),
        "rain": (65, 300),
        "cover": 0.65,
        "water_sensitivity": "waterlogging_sensitive",
        "planting_system": "raised_beds",
        "description": (
            "Pineapple requires longer-term field planning "
            "and suitable drainage during establishment."
        )
    },

    "banana": {
        "name": "Banana",
        "family": "Musaceae",
        "kind": "perennial",
        "months": 12,
        "temp": (23, 34),
        "rain": (110, 380),
        "cover": 0.80,
        "water_sensitivity": "waterlogging_sensitive",
        "planting_system": "plantation",
        "description": (
            "Banana requires appropriate drainage, "
            "planting material, wind protection "
            "and disease management."
        )
    },

    "coconut": {
        "name": "Coconut",
        "family": "Arecaceae",
        "kind": "perennial",
        "months": 36,
        "temp": (23, 34),
        "rain": (100, 400),
        "cover": 0.80,
        "water_sensitivity": "site_dependent",
        "planting_system": "orchard",
        "description": (
            "Coconut requires long-term land commitment, "
            "suitable soil conditions and plantation "
            "management."
        )
    },

    "durian": {
        "name": "Durian",
        "family": "Malvaceae",
        "kind": "perennial",
        "months": 60,
        "temp": (22, 33),
        "rain": (120, 430),
        "cover": 0.80,
        "water_sensitivity": "waterlogging_sensitive",
        "planting_system": "orchard",
        "description": (
            "Durian is a long-term orchard crop. "
            "Root-zone drainage, soil conditions "
            "and orchard establishment are critical."
        )
    }
}


# ============================================
# 2. VALIDATION HELPERS
# ============================================

def valid(value):
    return (
        isinstance(value, (int, float))
        and not isinstance(value, bool)
        and math.isfinite(value)
        and value != -999
    )


def safe_mean(values):
    numbers = [
        float(value)
        for value in values
        if valid(value)
    ]

    if not numbers:
        return None

    return round(mean(numbers), 2)


def closeness(value, low, high):
    """
    Experimental compatibility function.

    1.0 = within assumed screening interval.
    0.0 = outside tolerance interval.

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
# 3. MONTHLY NASA CLIMATOLOGY
# ============================================

def month_climatology(history):
    """
    Supports:

    A. climate_engine.py with 12 monthly
       climatology records.

    B. Older climate engines with year-month
       historical records.

    Incomplete rainfall months are excluded
    when processing raw historical records.
    """

    direct = history.get("monthly_climatology")

    if direct is None:
        direct = history.get("monthly", [])

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
                    row.get("rainfall_mm_years", 0)
                ),
                "temperature_years": row.get(
                    "temperature_years",
                    row.get("temperature_c_years", 0)
                )
            })

        return output

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
            if (
                isinstance(raw_month, str)
                and "-" in raw_month
            ):
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

        if (
            rain_complete is None
            and year is not None
        ):
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

        if (
            valid(rainfall)
            and rain_complete is True
        ):
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
# 4. MONTHLY CROP SCREENING
# ============================================

def screen_month(
    crop_id,
    month_data
):

    crop = CROPS[crop_id]

    rainfall = month_data.get(
        "rainfall_mm"
    )

    temperature = month_data.get(
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

    if (
        rain_score is None
        or temp_score is None
    ):
        return {
            "month": month_data["month"],
            "rainfall_mm": rainfall,
            "temperature_c": temperature,
            "rainfall_score": None,
            "temperature_score": None,
            "combined_score": None,
            "rainfall_status": "insufficient_data",
            "temperature_status": "insufficient_data"
        }

    combined = (
        0.55 * rain_score
        + 0.45 * temp_score
    )

    rain_status = (
        "within_range"
        if crop["rain"][0]
        <= rainfall
        <= crop["rain"][1]
        else (
            "below_range"
            if rainfall < crop["rain"][0]
            else "above_range"
        )
    )

    temp_status = (
        "within_range"
        if crop["temp"][0]
        <= temperature
        <= crop["temp"][1]
        else (
            "below_range"
            if temperature < crop["temp"][0]
            else "above_range"
        )
    )

    return {
        "month": month_data["month"],
        "rainfall_mm": rainfall,
        "temperature_c": temperature,
        "rainfall_score": round(
            rain_score * 100,
            1
        ),
        "temperature_score": round(
            temp_score * 100,
            1
        ),
        "combined_score": round(
            combined * 100,
            1
        ),
        "rainfall_status": rain_status,
        "temperature_status": temp_status
    }


# ============================================
# 5. PLANTING WINDOW EVALUATION
# ============================================

def evaluate_window(
    crop_id,
    monthly,
    start_index
):

    crop = CROPS[crop_id]

    duration = min(
        crop["months"],
        12
    )

    screened_months = []

    for offset in range(duration):

        index = (
            start_index + offset
        ) % 12

        row = screen_month(
            crop_id,
            monthly[index]
        )

        if row["combined_score"] is None:
            return None

        screened_months.append(row)

    return {
        "start_month": start_index + 1,
        "climate_score": safe_mean([
            row["combined_score"]
            for row in screened_months
        ]),
        "rainfall_component": safe_mean([
            row["rainfall_score"]
            for row in screened_months
        ]),
        "temperature_component": safe_mean([
            row["temperature_score"]
            for row in screened_months
        ]),
        "mean_rainfall_mm": safe_mean([
            row["rainfall_mm"]
            for row in screened_months
        ]),
        "mean_temperature_c": safe_mean([
            row["temperature_c"]
            for row in screened_months
        ]),
        "months_evaluated": duration,
        "monthly_evidence": screened_months
    }


# ============================================
# 6. CROP-SPECIFIC REASONING
# ============================================

def build_crop_reasoning(
    crop_id,
    best_window
):

    crop = CROPS[crop_id]

    if best_window is None:
        return {
            "headline": (
                "Insufficient climate evidence "
                "for a complete assessment."
            ),
            "supporting_evidence": [],
            "concerns": [
                "A complete historical rainfall "
                "and temperature series is required."
            ],
            "management_implications": [
                crop["description"]
            ]
        }

    monthly = best_window[
        "monthly_evidence"
    ]

    rainfall_above = sum(
        row["rainfall_status"] == "above_range"
        for row in monthly
    )

    rainfall_below = sum(
        row["rainfall_status"] == "below_range"
        for row in monthly
    )

    temp_above = sum(
        row["temperature_status"] == "above_range"
        for row in monthly
    )

    temp_below = sum(
        row["temperature_status"] == "below_range"
        for row in monthly
    )

    evidence = [
        (
            "Mean historical monthly rainfall "
            f"during the screened period is "
            f"{best_window['mean_rainfall_mm']} mm."
        ),
        (
            "Mean historical temperature "
            f"during the screened period is "
            f"{best_window['mean_temperature_c']} °C."
        ),
        (
            "The provisional rainfall component "
            f"is {best_window['rainfall_component']}/100."
        ),
        (
            "The provisional temperature component "
            f"is {best_window['temperature_component']}/100."
        )
    ]

    concerns = []

    if rainfall_above:
        concerns.append(
            f"Rainfall exceeds the assumed crop "
            f"screening range in {rainfall_above} "
            "screened month(s)."
        )

    if rainfall_below:
        concerns.append(
            f"Rainfall falls below the assumed crop "
            f"screening range in {rainfall_below} "
            "screened month(s)."
        )

    if temp_above:
        concerns.append(
            f"Mean temperature exceeds the assumed "
            f"screening range in {temp_above} "
            "screened month(s)."
        )

    if temp_below:
        concerns.append(
            f"Mean temperature falls below the assumed "
            f"screening range in {temp_below} "
            "screened month(s)."
        )

    if not concerns:
        concerns.append(
            "Rainfall and mean temperature fall "
            "within the assumed screening ranges "
            "throughout this candidate window. "
            "Other field conditions remain unverified."
        )

    if crop["kind"] == "annual":
        headline = (
            f"{crop['name']} has a candidate "
            "seasonal planting window based on "
            "historical climate screening."
        )
    else:
        headline = (
            f"{crop['name']} requires a longer-term "
            "planting assessment. The climate "
            "screening uses a representative "
            "annual cycle."
        )

    return {
        "headline": headline,
        "supporting_evidence": evidence,
        "concerns": concerns,
        "management_implications": [
            crop["description"],
            (
                "Confirm soil conditions, drainage, "
                "planting material and local crop "
                "management before implementation."
            )
        ]
    }


# ============================================
# 7. MAIN CROP SCREENING
# ============================================

def screen_crop(
    crop_id,
    monthly
):

    crop = CROPS[crop_id]

    windows = []

    for start in range(12):

        window = evaluate_window(
            crop_id,
            monthly,
            start
        )

        if window is not None:
            windows.append(window)

    windows.sort(
        key=lambda item: (
            -item["climate_score"],
            item["start_month"]
        )
    )

    best = windows[0] if windows else None

    reasoning = build_crop_reasoning(
        crop_id,
        best
    )

    return {
        "id": crop_id,
        "name": crop["name"],
        "family": crop["family"],
        "kind": crop["kind"],
        "approx_duration_months": crop["months"],
        "planting_system": crop["planting_system"],
        "water_sensitivity": crop["water_sensitivity"],
        "description": crop["description"],

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

        "alternative_windows": [
            {
                "start_month": window[
                    "start_month"
                ],
                "climate_score": window[
                    "climate_score"
                ],
                "rainfall_component": window[
                    "rainfall_component"
                ],
                "temperature_component": window[
                    "temperature_component"
                ]
            }
            for window in windows[:3]
        ],

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
            "temperature_weight": 0.45,
            "monthly_evidence": (
                best["monthly_evidence"]
                if best else []
            )
        },

        "reasoning": reasoning,

        "status": (
            "provisional climate screening"
            if best
            else "insufficient climate data"
        ),

        "thresholds": {
            "monthly_rainfall_mm": list(
                crop["rain"]
            ),
            "mean_temperature_c": list(
                crop["temp"]
            )
        }
    }


# ============================================
# 8. ROTATION COMPATIBILITY
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
            len(families)
            / len(sequence)
        ) * 100

        includes_legume = any(
            CROPS[crop_id]["family"]
            == "Fabaceae"
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
                "feasibility require local review."
            )
        })

    rotations.sort(
        key=lambda item: (
            -item["screening_index"]
        )
    )

    return rotations


# ============================================
# 9. PRELIMINARY FARMING ACTIVITIES
# ============================================

def generate_activities(rotations):

    if not rotations:
        return []

    best = rotations[0]

    activities = [
        {
            "category": "Crop rotation",
            "title": (
                "Review the proposed crop sequence"
            ),
            "reason": (
                "Explore "
                + " → ".join(best["crops"])
                + " and compare its climate screening "
                "with your current cropping practice."
            )
        },
        {
            "category": "Planting schedule",
            "title": (
                "Review seasonal planting windows"
            ),
            "reason": (
                "Compare historical NASA rainfall "
                "and temperature with the proposed "
                "crop sequence."
            )
        }
    ]

    if best["includes_legume"]:
        activities.append({
            "category": "Nutrient management",
            "title": (
                "Review legume establishment"
            ),
            "reason": (
                "Check nodulation, residue handling "
                "and local growing conditions."
            )
        })

    activities.append({
        "category": "Soil protection",
        "title": (
            "Plan soil-cover management"
        ),
        "reason": (
            "Review mulch, crop residues or "
            "appropriate ground-cover practices "
            "during crop transitions."
        )
    })

    return activities


# ============================================
# 10. MAIN RECOMMENDATION FUNCTION
# ============================================

def build_recommendations(
    latitude,
    longitude,
    history
):

    monthly = month_climatology(
        history
    )

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

        "suggested_activities": generate_activities(
            rotations
        ),

        "summary": history.get(
            "summary", {}
        ),

        "limitations": [
            "Crop climate thresholds are provisional assumptions.",
            "Compatibility scores are not probabilities of cultivation success.",
            "Historical climate is not a future weather forecast.",
            "Soil pH and field drainage are not measured by this engine.",
            "Rotation and economic feasibility require local review."
        ]
    }
