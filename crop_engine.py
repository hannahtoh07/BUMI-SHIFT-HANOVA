
"""
BUMI SHIFT 5.0
Sarawak Crop Intelligence Engine
Developed by HANOVA

Purpose:
- Generate locally relevant crop candidates
- Explore annual crop rotation sequences
- Suggest practical management activities
- Interpret available NASA climate indicators
- Identify important missing evidence

This is an exploratory decision-support engine.
It does not predict crop yield, profit, or measured
soil-health improvement.
"""

from datetime import date
from typing import Optional


# ==================================================
# 1. CROP LIBRARY
# ==================================================

# Crop categories and broad agronomic characteristics.
# Numerical suitability thresholds will be added
# only from documented crop-specific references.

CROPS = {
    "rice": {
        "name": "Rice",
        "scientific_name": "Oryza sativa",
        "family": "Poaceae",
        "category": "annual",
        "rotation_role": "cereal",
        "water_note": (
            "Water requirements depend on the rice "
            "production system and cultivar."
        ),
        "soil_health_role": (
            "Rice residues can contribute organic "
            "material when appropriately managed."
        ),
        "activities": [
            "Review field water management.",
            "Monitor drainage and standing water.",
            "Consider residue retention where appropriate.",
            "Plan the next crop after harvest."
        ]
    },

    "maize": {
        "name": "Maize",
        "scientific_name": "Zea mays",
        "family": "Poaceae",
        "category": "annual",
        "rotation_role": "cereal",
        "water_note": (
            "Moisture availability during crop growth "
            "is important."
        ),
        "soil_health_role": (
            "Crop residues may provide soil cover "
            "when retained."
        ),
        "activities": [
            "Monitor soil moisture.",
            "Maintain suitable drainage.",
            "Consider residue management.",
            "Review nutrient requirements."
        ]
    },

    "mung_bean": {
        "name": "Mung Bean",
        "scientific_name": "Vigna radiata",
        "family": "Fabaceae",
        "category": "annual",
        "rotation_role": "legume",
        "water_note": (
            "Poor drainage and waterlogging can "
            "limit establishment."
        ),
        "soil_health_role": (
            "A legume rotation may support nitrogen "
            "management when effective nodulation "
            "and appropriate residue management occur."
        ),
        "activities": [
            "Check field drainage before planting.",
            "Consider appropriate inoculation where needed.",
            "Monitor crop establishment.",
            "Plan residue management after harvest."
        ]
    },

    "groundnut": {
        "name": "Groundnut",
        "scientific_name": "Arachis hypogaea",
        "family": "Fabaceae",
        "category": "annual",
        "rotation_role": "legume",
        "water_note": (
            "Good drainage is important for "
            "successful production."
        ),
        "soil_health_role": (
            "Can diversify a cereal-based rotation "
            "and potentially contribute to nitrogen cycling."
        ),
        "activities": [
            "Assess drainage and soil conditions.",
            "Monitor moisture during establishment.",
            "Review nutrient and nodulation requirements.",
            "Manage residues after harvest."
        ]
    },

    "soybean": {
        "name": "Soybean",
        "scientific_name": "Glycine max",
        "family": "Fabaceae",
        "category": "annual",
        "rotation_role": "legume",
        "water_note": (
            "Adequate moisture and drainage are important."
        ),
        "soil_health_role": (
            "Can diversify crop families and contribute "
            "to biological nitrogen fixation under "
            "suitable conditions."
        ),
        "activities": [
            "Review locally adapted varieties.",
            "Check drainage conditions.",
            "Monitor crop establishment.",
            "Consider residue and nutrient management."
        ]
    },

    "sweet_potato": {
        "name": "Sweet Potato",
        "scientific_name": "Ipomoea batatas",
        "family": "Convolvulaceae",
        "category": "annual",
        "rotation_role": "root_crop",
        "water_note": (
            "Drainage and soil conditions influence "
            "root development."
        ),
        "soil_health_role": (
            "Ground-covering growth may help reduce "
            "exposed soil during cultivation."
        ),
        "activities": [
            "Check soil structure and drainage.",
            "Maintain suitable soil cover.",
            "Monitor water availability.",
            "Plan harvesting and residue management."
        ]
    },

    "cassava": {
        "name": "Cassava",
        "scientific_name": "Manihot esculenta",
        "family": "Euphorbiaceae",
        "category": "long_duration",
        "rotation_role": "root_crop",
        "water_note": (
            "Water availability and drainage should "
            "be assessed during establishment."
        ),
        "soil_health_role": (
            "Soil-cover management is important, "
            "especially during early establishment."
        ),
        "activities": [
            "Review the longer growing period.",
            "Maintain soil cover where possible.",
            "Monitor erosion exposure.",
            "Plan nutrient replacement after harvest."
        ]
    },

    "pineapple": {
        "name": "Pineapple",
        "scientific_name": "Ananas comosus",
        "family": "Bromeliaceae",
        "category": "long_duration",
        "rotation_role": "establishment",
        "water_note": (
            "Drainage and waterlogging exposure "
            "require attention."
        ),
        "soil_health_role": (
            "Mulching and ground-cover management "
            "may help protect exposed soil."
        ),
        "activities": [
            "Assess drainage suitability.",
            "Review planting material and establishment.",
            "Consider mulching.",
            "Monitor soil exposure and erosion."
        ]
    },

    "banana": {
        "name": "Banana",
        "scientific_name": "Musa spp.",
        "family": "Musaceae",
        "category": "perennial",
        "rotation_role": "perennial_management",
        "water_note": (
            "Requires appropriate water availability "
            "and drainage."
        ),
        "soil_health_role": (
            "Mulch and plant residues can contribute "
            "to soil-cover management."
        ),
        "activities": [
            "Assess drainage and water availability.",
            "Maintain appropriate mulch.",
            "Monitor plant health.",
            "Plan nutrient and residue management."
        ]
    },

    "coconut": {
        "name": "Coconut",
        "scientific_name": "Cocos nucifera",
        "family": "Arecaceae",
        "category": "perennial",
        "rotation_role": "intercropping",
        "water_note": (
            "Site water conditions influence "
            "long-term establishment."
        ),
        "soil_health_role": (
            "Suitable intercrops and ground cover "
            "may contribute to soil protection."
        ),
        "activities": [
            "Assess long-term site suitability.",
            "Review possible intercrops.",
            "Maintain soil cover.",
            "Monitor water and nutrient availability."
        ]
    },

    "durian": {
        "name": "Durian",
        "scientific_name": "Durio zibethinus",
        "family": "Malvaceae",
        "category": "perennial",
        "rotation_role": "orchard_management",
        "water_note": (
            "Drainage and waterlogging exposure "
            "are important considerations."
        ),
        "soil_health_role": (
            "Orchard ground cover and mulch may "
            "help protect soil."
        ),
        "activities": [
            "Assess site drainage.",
            "Plan orchard ground-cover management.",
            "Review long-term water requirements.",
            "Monitor soil and plant health."
        ]
    }
}


# ==================================================
# 2. CROP DATA
# ==================================================

def get_crop_library():
    return [
        {
            "id": crop_id,
            **crop
        }
        for crop_id, crop in CROPS.items()
    ]


# ==================================================
# 3. CLIMATE INTERPRETATION
# ==================================================

def interpret_climate(climate):
    """
    Interpret actual NASA climate summary values.

    This does not apply crop-specific thresholds
    or claim to measure field-level soil conditions.
    """

    summary = climate.get("summary", {})

    rainfall = summary.get(
        "mean_annual_rainfall_mm"
    )

    temperature = summary.get(
        "mean_temperature_c"
    )

    observations = []

    if rainfall is not None:
        observations.append({
            "indicator": "Historical rainfall",
            "value": rainfall,
            "unit": "mm/year",
            "interpretation": (
                "Use the monthly rainfall distribution "
                "to investigate crop planting windows."
            )
        })

    if temperature is not None:
        observations.append({
            "indicator": "Historical temperature",
            "value": temperature,
            "unit": "deg C",
            "interpretation": (
                "Compare temperature patterns with "
                "crop-specific requirements before "
                "determining suitability."
            )
        })

    return observations


# ==================================================
# 4. ROTATION CANDIDATES
# ==================================================

def generate_rotation_candidates():
    """
    Generate illustrative annual crop sequences.

    These are planning candidates, not validated
    farm-specific recommendations.
    """

    sequences = [
        {
            "id": "rice_mung_rice",
            "name": "Rice - Mung Bean - Rice",
            "crops": [
                "rice",
                "mung_bean",
                "rice"
            ]
        },
        {
            "id": "rice_groundnut_rice",
            "name": "Rice - Groundnut - Rice",
            "crops": [
                "rice",
                "groundnut",
                "rice"
            ]
        },
        {
            "id": "rice_maize_rice",
            "name": "Rice - Maize - Rice",
            "crops": [
                "rice",
                "maize",
                "rice"
            ]
        },
        {
            "id": "maize_mung_maize",
            "name": "Maize - Mung Bean - Maize",
            "crops": [
                "maize",
                "mung_bean",
                "maize"
            ]
        },
        {
            "id": "maize_groundnut_maize",
            "name": "Maize - Groundnut - Maize",
            "crops": [
                "maize",
                "groundnut",
                "maize"
            ]
        }
    ]

    results = []

    for sequence in sequences:

        crop_ids = sequence["crops"]

        families = {
            CROPS[crop_id]["family"]
            for crop_id in crop_ids
        }

        includes_legume = any(
            CROPS[crop_id]["rotation_role"]
            == "legume"
            for crop_id in crop_ids
        )

        results.append({
            **sequence,
            "crop_names": [
                CROPS[crop_id]["name"]
                for crop_id in crop_ids
            ],
            "crop_family_count": len(families),
            "includes_legume": includes_legume,
            "potential_benefits": [
                "Crop-family diversification"
                if len(families) > 1
                else "Single crop-family sequence",
                (
                    "Potential biological nitrogen "
                    "fixation under suitable conditions"
                    if includes_legume
                    else "No legume included"
                )
            ],
            "status": "Requires local feasibility screening"
        })

    return results


# ==================================================
# 5. ACTIVITY SUGGESTIONS
# ==================================================

def generate_activities():
    """
    General agricultural planning activities.

    These are not automatically validated
    field-specific prescriptions.
    """

    return [
        {
            "category": "Planting",
            "title": "Review the planting window",
            "description": (
                "Use historical rainfall and "
                "temperature patterns to identify "
                "periods worth investigating."
            )
        },
        {
            "category": "Soil Health",
            "title": "Maintain soil cover",
            "description": (
                "Consider appropriate cover crops, "
                "mulch or crop residues to reduce "
                "periods of exposed soil."
            )
        },
        {
            "category": "Crop Rotation",
            "title": "Diversify crop families",
            "description": (
                "Investigate compatible crop "
                "sequences that avoid repeated "
                "cultivation of the same crop family."
            )
        },
        {
            "category": "Water Management",
            "title": "Review drainage and water access",
            "description": (
                "Check field conditions before "
                "adopting crops sensitive to "
                "waterlogging or water shortages."
            )
        },
        {
            "category": "Nutrient Management",
            "title": "Plan residue management",
            "description": (
                "Consider how harvest residues "
                "will be retained, removed or "
                "incorporated into the soil."
            )
        }
    ]


# ==================================================
# 6. COMPLETE PRELIMINARY ASSESSMENT
# ==================================================

def build_crop_assessment(
    latitude,
    longitude,
    climate
):
    """
    Combine NASA climate summaries with
    the preliminary crop library.

    No fabricated suitability percentages.
    No fabricated yield or profit estimates.
    """

    return {
        "region": "Sarawak, Malaysia",
        "latitude": latitude,
        "longitude": longitude,
        "generated_on": date.today().isoformat(),
        "assessment_type": (
            "Preliminary regional crop planning"
        ),
        "climate_source": climate.get("source"),
        "climate_period": {
            "start_year": climate.get("start_year"),
            "end_year": climate.get("end_year")
        },
        "climate_indicators": interpret_climate(
            climate
        ),
        "crop_candidates": get_crop_library(),
        "rotation_candidates": (
            generate_rotation_candidates()
        ),
        "suggested_activities": (
            generate_activities()
        ),
        "soil_health_note": (
            "Crop diversification and soil-cover "
            "management may offer benefits, but "
            "actual soil-health improvements "
            "cannot be quantified without "
            "additional field evidence."
        ),
        "profit_note": (
            "Profit cannot be estimated reliably "
            "without local prices, input costs "
            "and yield information."
        ),
        "limitations": [
            "NASA climate data are gridded estimates.",
            "Crop candidates are not ranked by suitability.",
            "No field-level soil test is available.",
            "Planting calendars require local verification.",
            "Rotation benefits depend on management.",
            "No crop yield prediction is provided."
        ]
    }
