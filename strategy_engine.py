
"""
BUMI SHIFT 7.0
Personalized Farming Strategy Engine

HANOVA | Sarawak, Malaysia

Purpose
-------
Generate explainable farming strategies using:

1. NASA POWER historical climate observations
2. Crop characteristics from crop_engine.py
3. Farmer's current crop
4. Farmer's preferred crop
5. Farmer's farming priority
6. Optional farmer-reported drainage conditions

Outputs
-------
- Baseline strategy
- Alternative annual crop rotations
- Preferred crop strategy
- Long-term crop transition scenarios
- Climate and soil-management screening
- Personalized reasoning
- Crop-specific farming actions
- Practical risks and local verification

Scientific limitations
----------------------
Climate compatibility is provisional.
Historical observations are not forecasts.
Soil-health indicators are management proxies.
Drainage is farmer-reported, not NASA-measured.
Market prices, crop yields and profits are not predicted.
"""

from statistics import mean

from crop_engine import CROPS, closeness


# ============================================
# 1. CONSTANTS
# ============================================

MONTHS = [
    "Jan", "Feb", "Mar", "Apr",
    "May", "Jun", "Jul", "Aug",
    "Sep", "Oct", "Nov", "Dec"
]

PRIORITIES = {
    "soil",
    "water",
    "resilience",
    "income"
}

DRAINAGE_OPTIONS = {
    "unknown",
    "poor",
    "moderate",
    "good"
}

ANNUAL_CROPS = {
    crop_id
    for crop_id, crop in CROPS.items()
    if crop["kind"] == "annual"
}

LONG_TERM_CROPS = {
    crop_id
    for crop_id, crop in CROPS.items()
    if crop["kind"] != "annual"
}

LEGUMES = {
    crop_id
    for crop_id, crop in CROPS.items()
    if crop["family"] == "Fabaceae"
}


# ============================================
# 2. CROP MANAGEMENT LIBRARY
# ============================================

CROP_MANAGEMENT = {

    "rice": {
        "water": "Review paddy bunds, water control and field drainage.",
        "soil": "Manage rice residues and avoid unnecessary bare-soil periods.",
        "risk": "Flooding, inadequate water control and wet harvest conditions.",
        "market": "Check local paddy purchasing arrangements, grain quality and drying facilities."
    },

    "maize": {
        "water": "Review drainage and moisture availability during flowering.",
        "soil": "Review nutrient management, residues and crop-family diversification.",
        "risk": "Waterlogging, nutrient losses and pest pressure.",
        "market": "Check whether buyers require grain maize or fresh sweet corn and confirm grading requirements."
    },

    "mung_bean": {
        "water": "Avoid prolonged waterlogging during establishment.",
        "soil": "Check effective nodulation and plan residue management after harvest.",
        "risk": "Heavy rainfall, disease pressure and poor establishment.",
        "market": "Check demand for dry mung beans, drying facilities and acceptable grain quality."
    },

    "groundnut": {
        "water": "Check drainage and soil conditions for pegging and pod development.",
        "soil": "Review legume nodulation, residue management and soil structure.",
        "risk": "Waterlogging and unsuitable soil texture.",
        "market": "Confirm demand for fresh or dried groundnuts and post-harvest drying requirements."
    },

    "soybean": {
        "water": "Review drainage and moisture conditions during flowering and pod filling.",
        "soil": "Check rhizobia compatibility, nodulation and residue management.",
        "risk": "Excessive rainfall, disease and photoperiod sensitivity.",
        "market": "Confirm soybean buyers, required quality standards and drying arrangements."
    },

    "sweet_potato": {
        "water": "Consider raised beds and adequate drainage for storage-root development.",
        "soil": "Manage vine cover and avoid unnecessary soil exposure.",
        "risk": "Waterlogging, root damage and pest pressure.",
        "market": "Review fresh-market demand, root grading, storage and transport requirements."
    },

    "cassava": {
        "water": "Review drainage and avoid prolonged saturated soil conditions.",
        "soil": "Consider erosion control and soil-cover management during establishment.",
        "risk": "Root disease, erosion and extended land occupation.",
        "market": "Confirm whether local buyers require fresh roots or processing varieties and check delivery arrangements."
    },

    "pineapple": {
        "water": "Review drainage and field preparation before establishment.",
        "soil": "Consider mulching, residue management and erosion control.",
        "risk": "Waterlogging, disease and long crop duration.",
        "market": "Check fruit grading, harvest scheduling, transport and fresh or processing market access."
    },

    "banana": {
        "water": "Check drainage, wind exposure and moisture management.",
        "soil": "Manage crop residues and maintain appropriate ground cover.",
        "risk": "Wind damage, waterlogging and banana diseases.",
        "market": "Check local banana buyers, bunch quality, ripening and transport requirements."
    },

    "coconut": {
        "water": "Assess drainage, soil depth and long-term water availability.",
        "soil": "Review inter-row vegetation and long-term ground-cover management.",
        "risk": "Long establishment period, unsuitable soil and wind exposure.",
        "market": "Compare local opportunities for fresh coconuts and processed coconut products."
    },

    "durian": {
        "water": "Assess deep drainage and avoid prolonged root-zone saturation.",
        "soil": "Review orchard ground cover, erosion control and soil management.",
        "risk": "Root disease, waterlogging and long orchard establishment.",
        "market": "Check cultivar demand, fruit handling, harvest logistics and reliable buyers."
    }
}


# ============================================
# 3. BASIC HELPERS
# ============================================

def valid_number(value):
    return (
        isinstance(value, (int, float))
        and not isinstance(value, bool)
        and value == value
        and abs(value) != float("inf")
    )


def safe_mean(values):
    numbers = [
        value
        for value in values
        if valid_number(value)
    ]

    if not numbers:
        return None

    return round(mean(numbers), 2)


def crop_name(crop_id):
    return CROPS[crop_id]["name"]


def crop_family(crop_id):
    return CROPS[crop_id]["family"]


def crop_duration(crop_id):
    return CROPS[crop_id]["months"]


def month_name(index):
    return MONTHS[index % 12]


def unique_sequences(sequences):
    output = []
    seen = set()

    for sequence in sequences:
        key = tuple(sequence)

        if key not in seen:
            seen.add(key)
            output.append(sequence)

    return output


# ============================================
# 4. DRAINAGE ASSESSMENT
# ============================================

def drainage_assessment(
    crop_id,
    drainage
):
    """
    Interpret farmer-reported drainage.

    This is a qualitative field-feasibility
    screening, not a measured soil-water model.
    """

    sensitive = {
        "maize",
        "mung_bean",
        "groundnut",
        "soybean",
        "sweet_potato",
        "cassava",
        "pineapple",
        "banana",
        "durian"
    }

    if drainage == "unknown":
        return {
            "status": "not_verified",
            "penalty": 0,
            "reason": (
                "Field drainage has not been reported. "
                "Check local waterlogging conditions "
                "before changing crops."
            )
        }

    if drainage == "poor":

        if crop_id in sensitive:
            return {
                "status": "requires_management_review",
                "penalty": 12,
                "reason": (
                    f"{crop_name(crop_id)} may be sensitive "
                    "to prolonged waterlogging. "
                    "Drainage improvements or alternative "
                    "field arrangements should be assessed."
                )
            }

        return {
            "status": "review",
            "penalty": 0,
            "reason": (
                "Poor drainage was reported. "
                "Review the existing water-management "
                "system and crop requirements."
            )
        }

    if drainage == "moderate":
        return {
            "status": "review",
            "penalty": 0,
            "reason": (
                "Moderate drainage was reported. "
                "Confirm that drainage is adequate "
                "during heavy rainfall."
            )
        }

    return {
        "status": "reported_good",
        "penalty": 0,
        "reason": (
            "The farmer reports relatively good drainage. "
            "This should still be verified for "
            "the proposed crop."
        )
    }


# ============================================
# 5. NASA CLIMATE SCREENING
# ============================================

def evaluate_sequence(
    sequence,
    monthly,
    start_month
):
    """
    Evaluate crop requirements against
    historical monthly NASA climatology.

    start_month is zero-based.

    Scores are provisional compatibility
    indices, not probabilities.
    """

    offset = 0

    combined_scores = []
    rainfall_scores = []
    temperature_scores = []

    rainfall_values = []
    temperature_values = []

    stages = []

    for crop_id in sequence:

        crop = CROPS[crop_id]
        duration = crop["months"]

        stage_scores = []
        stage_rainfall = []
        stage_temperature = []

        # Perennial and long-duration crops
        # use one representative annual cycle
        # for climate screening.
        screening_duration = min(
            duration,
            12
        )

        for step in range(screening_duration):

            index = (
                start_month
                + offset
                + step
            ) % 12

            row = monthly[index]

            rain = row.get("rainfall_mm")
            temp = row.get("temperature_c")

            rain_score = closeness(
                rain,
                *crop["rain"]
            )

            temp_score = closeness(
                temp,
                *crop["temp"]
            )

            if (
                rain_score is None
                or temp_score is None
            ):
                return None

            score = (
                0.55 * rain_score
                + 0.45 * temp_score
            )

            combined_scores.append(score)
            rainfall_scores.append(rain_score)
            temperature_scores.append(temp_score)

            rainfall_values.append(rain)
            temperature_values.append(temp)

            stage_scores.append(score)
            stage_rainfall.append(rain)
            stage_temperature.append(temp)

        stages.append({
            "crop_id": crop_id,
            "crop": crop_name(crop_id),
            "kind": crop["kind"],
            "start_month": month_name(
                start_month + offset
            ),
            "end_month": month_name(
                start_month + offset + duration - 1
            ),
            "duration_months": duration,
            "climate_score": round(
                100 * mean(stage_scores),
                1
            ),
            "mean_rainfall_mm": safe_mean(
                stage_rainfall
            ),
            "mean_temperature_c": safe_mean(
                stage_temperature
            )
        })

        offset += duration

    return {
        "climate_score": round(
            100 * mean(combined_scores),
            1
        ),
        "rainfall_component": round(
            100 * mean(rainfall_scores),
            1
        ),
        "temperature_component": round(
            100 * mean(temperature_scores),
            1
        ),
        "mean_monthly_rain_mm": safe_mean(
            rainfall_values
        ),
        "mean_temperature_c": safe_mean(
            temperature_values
        ),
        "duration_months": offset,
        "stages": stages
    }


# ============================================
# 6. SOIL-MANAGEMENT PROXIES
# ============================================

def soil_management_assessment(sequence):

    families = [
        crop_family(crop_id)
        for crop_id in sequence
    ]

    diversity = len(set(families))

    ground_cover = round(
        mean(
            CROPS[crop_id].get("cover", 0.5)
            for crop_id in sequence
        ) * 100
    )

    family_changes = sum(
        families[i] != families[i - 1]
        for i in range(1, len(families))
    )

    possible_changes = max(
        len(sequence) - 1,
        1
    )

    diversity_fraction = (
        diversity / max(len(sequence), 1)
    )

    change_fraction = (
        family_changes / possible_changes
    )

    soil_proxy = round(
        40 * diversity_fraction
        + 35 * ground_cover / 100
        + 25 * change_fraction,
        1
    )

    legume_included = any(
        crop_id in LEGUMES
        for crop_id in sequence
    )

    return {
        "soil_management_proxy": soil_proxy,
        "crop_family_count": diversity,
        "ground_cover_proxy": ground_cover,
        "legume_included": legume_included,
        "family_changes": family_changes
    }


# ============================================
# 7. FARMING PRIORITY SCREENING
# ============================================

def priority_assessment(
    climate_score,
    soil_proxy,
    priority
):
    """
    Experimental priority-weighted ranking.

    Income is intentionally not quantified
    because comparable market and cost data
    are not yet integrated.
    """

    if priority == "soil":
        return round(
            0.45 * climate_score
            + 0.55 * soil_proxy,
            1
        )

    if priority == "water":
        return round(
            0.85 * climate_score
            + 0.15 * soil_proxy,
            1
        )

    if priority == "resilience":
        return round(
            0.75 * climate_score
            + 0.25 * soil_proxy,
            1
        )

    return None


# ============================================
# 8. GENERATE CANDIDATE STRATEGIES
# ============================================

def build_sequences(
    baseline,
    preferred_crop
):

    sequences = [
        [baseline, baseline, baseline]
    ]

    alternatives = [
        "mung_bean",
        "groundnut",
        "sweet_potato",
        "maize",
        "soybean",
        "rice"
    ]

    if preferred_crop in ANNUAL_CROPS:

        sequences.append([
            baseline,
            preferred_crop,
            baseline
        ])

    for crop_id in alternatives:

        if crop_id == baseline:
            continue

        sequences.append([
            baseline,
            crop_id,
            baseline
        ])

    return unique_sequences(sequences)


# ============================================
# 9. GENERATE A STRATEGY
# ============================================

def build_strategy(
    sequence,
    monthly,
    priority,
    baseline,
    drainage,
    strategy_type="alternative"
):

    windows = []

    for start in range(12):

        evaluation = evaluate_sequence(
            sequence,
            monthly,
            start
        )

        if evaluation is not None:
            windows.append((
                start,
                evaluation
            ))

    if not windows:
        return None

    start, climate = max(
        windows,
        key=lambda item: item[1]["climate_score"]
    )

    soil = soil_management_assessment(
        sequence
    )

    drainage_checks = [
        drainage_assessment(
            crop_id,
            drainage
        )
        for crop_id in sequence
    ]

    drainage_penalty = max(
        check["penalty"]
        for check in drainage_checks
    )

    climate_score = climate["climate_score"]

    priority_index = priority_assessment(
        climate_score,
        soil["soil_management_proxy"],
        priority
    )

    # This adjustment represents a qualitative
    # drainage-management concern. It does not
    # alter the underlying NASA climate score.
    if priority_index is not None:
        priority_index = round(
            max(
                0,
                priority_index - drainage_penalty
            ),
            1
        )

    risks = []

    if (
        climate["mean_monthly_rain_mm"]
        is not None
        and climate["mean_monthly_rain_mm"] > 230
    ):
        risks.append(
            "Historical wet-season rainfall exposure "
            "warrants a drainage and waterlogging review."
        )

    if drainage == "poor":

        sensitive_crops = [
            crop_id
            for crop_id in sequence
            if drainage_assessment(
                crop_id,
                drainage
            )["penalty"] > 0
        ]

        if sensitive_crops:
            names = ", ".join(
                crop_name(crop_id)
                for crop_id in dict.fromkeys(
                    sensitive_crops
                )
            )

            risks.append(
                "Farmer-reported poor drainage may "
                f"affect {names}. Review drainage "
                "feasibility before planting."
            )

    elif drainage == "unknown":
        risks.append(
            "Field drainage has not been verified."
        )

    if soil["legume_included"]:
        risks.append(
            "Legume nitrogen benefits depend on "
            "effective nodulation, biomass and "
            "residue management."
        )

    risks.append(
        "Soil pH, pests, market access and "
        "field-level conditions require local review."
    )

    benefits = []

    if soil["crop_family_count"] > 1:
        benefits.append(
            "Introducing different crop families "
            "may diversify rooting patterns and "
            "management practices."
        )
    else:
        benefits.append(
            "Provides a baseline reference for "
            "comparing diversified alternatives."
        )

    if soil["legume_included"]:
        benefits.append(
            "A legume phase may create opportunities "
            "for nutrient cycling under appropriate "
            "nodulation and residue management."
        )

    if soil["ground_cover_proxy"] >= 70:
        benefits.append(
            "The crop sequence has a relatively "
            "high experimental ground-cover proxy."
        )

    evidence = (
        "NASA historical monthly rainfall and "
        "mean temperature were compared with "
        "provisional crop requirements. "
        f"The candidate sequence starts in "
        f"{month_name(start)}. "
        f"Mean rainfall across screened months "
        f"is {climate['mean_monthly_rain_mm']} mm/month."
    )

    strategy_id = "-".join(sequence)

    if strategy_type == "long_term":
        strategy_id = (
            "transition-" + strategy_id
        )

    return {
        "id": strategy_id,
        "type": strategy_type,
        "crop_ids": sequence,
        "crops": [
            crop_name(crop_id)
            for crop_id in sequence
        ],
        "start_month": month_name(start),
        "stages": climate["stages"],
        "climate_score": climate_score,
        "rainfall_component": climate[
            "rainfall_component"
        ],
        "temperature_component": climate[
            "temperature_component"
        ],
        "mean_monthly_rain_mm": climate[
            "mean_monthly_rain_mm"
        ],
        "mean_temperature_c": climate[
            "mean_temperature_c"
        ],
        "soil_management_proxy": soil[
            "soil_management_proxy"
        ],
        "priority_index": priority_index,
        "duration_months": climate[
            "duration_months"
        ],
        "crop_family_count": soil[
            "crop_family_count"
        ],
        "legume_included": soil[
            "legume_included"
        ],
        "ground_cover_proxy": soil[
            "ground_cover_proxy"
        ],
        "family_changes": soil[
            "family_changes"
        ],
        "drainage": drainage,
        "drainage_assessment": drainage_checks,
        "evidence": evidence,
        "potential_benefits": benefits,
        "risks": risks,
        "market_status": (
            "Market references require "
            "independent verification."
        )
    }


# ============================================
# 10. LONG-TERM CROP TRANSITIONS
# ============================================

def build_long_term_strategy(
    baseline,
    preferred_crop,
    monthly,
    priority,
    drainage
):
    """
    Long-duration and perennial crops are
    treated as land-use transitions.

    They are not inserted into a three-stage
    annual crop rotation.
    """

    if preferred_crop not in LONG_TERM_CROPS:
        return None

    # Only the proposed long-term crop is
    # screened, not a fictitious annual cycle.
    strategy = build_strategy(
        [preferred_crop],
        monthly,
        priority,
        baseline,
        drainage,
        strategy_type="long_term"
    )

    if strategy is None:
        return None

    strategy["id"] = (
        f"transition-{baseline}-to-{preferred_crop}"
    )

    strategy["baseline_crop"] = baseline
    strategy["preferred_crop"] = preferred_crop

    strategy["comparison_to_baseline"] = (
        f"Transition from {crop_name(baseline)} "
        f"to {crop_name(preferred_crop)}. "
        "This represents a longer-term land-use "
        "decision rather than a short annual rotation."
    )

    strategy["risks"].append(
        "Long-term land commitment, establishment "
        "costs, market arrangements and field "
        "suitability require local assessment."
    )

    return strategy


# ============================================
# 11. BASELINE COMPARISON
# ============================================

def compare_to_baseline(
    strategies
):

    baseline = next(
        (
            strategy
            for strategy in strategies
            if strategy["type"] == "baseline"
        ),
        None
    )

    for strategy in strategies:

        if strategy.get(
            "comparison_to_baseline"
        ):
            continue

        if baseline is None:
            strategy["comparison_to_baseline"] = (
                "Baseline comparison unavailable."
            )
            continue

        difference = (
            strategy["climate_score"]
            - baseline["climate_score"]
        )

        strategy["comparison_to_baseline"] = (
            f"Climate screening difference "
            f"{difference:+.1f} points; "
            f"{strategy['crop_family_count']} "
            "crop families compared with "
            f"{baseline['crop_family_count']} "
            "in the baseline. "
            "These are exploratory indicators."
        )


# ============================================
# 12. CUSTOMIZED FARMING ACTIONS
# ============================================

def generate_actions(
    strategy,
    priority,
    drainage
):

    if strategy is None:
        return []

    actions = []

    for index, stage in enumerate(
        strategy["stages"]
    ):

        crop_id = stage["crop_id"]
        crop = CROPS[crop_id]

        actions.append({
            "category": "Planting calendar",
            "title": (
                f"Stage {index + 1}: "
                f"prepare for {crop['name']}"
            ),
            "reason": (
                f"Candidate period "
                f"{stage['start_month']}–"
                f"{stage['end_month']} "
                f"({stage['duration_months']} months). "
                "Confirm planting material, "
                "field readiness and local timing."
            ),
            "crop_id": crop_id
        })

        management = CROP_MANAGEMENT[
            crop_id
        ]

        if priority == "soil":
            focus = management["soil"]

        elif priority == "water":
            focus = management["water"]

        elif priority == "resilience":
            focus = (
                management["water"]
                + " "
                + management["risk"]
            )

        else:
            focus = management["market"]

        actions.append({
            "category": "Priority action",
            "title": (
                f"{crop['name']}: "
                "review management priorities"
            ),
            "reason": focus,
            "crop_id": crop_id
        })

    if drainage == "poor":
        actions.append({
            "category": "Drainage",
            "title": "Assess drainage improvements",
            "reason": (
                "The farmer reports poor drainage. "
                "Inspect waterlogging after heavy rain "
                "and evaluate field preparation "
                "before introducing sensitive crops."
            )
        })

    elif drainage == "unknown":
        actions.append({
            "category": "Field verification",
            "title": "Check drainage conditions",
            "reason": (
                "Drainage was not reported. "
                "Observe whether water remains "
                "after rainfall before switching crops."
            )
        })

    if strategy["legume_included"]:
        actions.append({
            "category": "Nutrient cycling",
            "title": "Review legume establishment",
            "reason": (
                "Check effective nodulation, "
                "crop residues and local soil "
                "management before assuming "
                "nitrogen benefits."
            )
        })

    if strategy["ground_cover_proxy"] < 70:
        actions.append({
            "category": "Soil protection",
            "title": "Reduce bare-soil intervals",
            "reason": (
                "Consider suitable mulch, "
                "residue retention or cover crops "
                "between cultivation stages."
            )
        })

    actions.append({
        "category": "Decision",
        "title": "Compare the proposed SHIFT",
        "reason": strategy[
            "comparison_to_baseline"
        ]
    })

    return actions


# ============================================
# 13. MAIN PERSONALIZATION FUNCTION
# ============================================

def enrich(
    result,
    history,
    priority="soil",
    baseline="rice",
    preferred_crop="auto",
    drainage="unknown"
):
    """
    Main function called by backend.py.

    Preserves existing response keys while
    adding personalized farming strategies.
    """

    if priority not in PRIORITIES:
        priority = "soil"

    if drainage not in DRAINAGE_OPTIONS:
        drainage = "unknown"

    if baseline not in ANNUAL_CROPS:
        baseline = "rice"

    if (
        preferred_crop != "auto"
        and preferred_crop not in CROPS
    ):
        preferred_crop = "auto"

    monthly = result.get(
        "monthly_climatology", []
    )

    if len(monthly) != 12:
        raise ValueError(
            "Expected 12 monthly climate records."
        )

    sequences = build_sequences(
        baseline,
        preferred_crop
    )

    strategies = []

    for index, sequence in enumerate(
        sequences
    ):

        strategy_type = (
            "baseline"
            if index == 0
            else "alternative"
        )

        strategy = build_strategy(
            sequence,
            monthly,
            priority,
            baseline,
            drainage,
            strategy_type
        )

        if strategy is not None:
            strategies.append(strategy)

    if preferred_crop in LONG_TERM_CROPS:

        long_term = build_long_term_strategy(
            baseline,
            preferred_crop,
            monthly,
            priority,
            drainage
        )

        if long_term is not None:
            strategies.append(long_term)

    compare_to_baseline(strategies)

    # Keep the baseline first.
    baseline_strategies = [
        s for s in strategies
        if s["type"] == "baseline"
    ]

    alternative_strategies = [
        s for s in strategies
        if s["type"] != "baseline"
    ]

    # Preferred crop strategies appear first.
    def strategy_sort_key(strategy):

        preferred_match = (
            preferred_crop != "auto"
            and preferred_crop in strategy[
                "crop_ids"
            ]
        )

        ranking = strategy[
            "priority_index"
        ]

        if ranking is None:
            ranking = strategy[
                "climate_score"
            ]

        return (
            not preferred_match,
            -ranking
        )

    alternative_strategies.sort(
        key=strategy_sort_key
    )

    strategies = (
        baseline_strategies
        + alternative_strategies
    )

    # Select the first alternative as the
    # recommended candidate strategy.
    recommended = next(
        (
            strategy
            for strategy in strategies
            if strategy["type"] != "baseline"
        ),
        None
    )

    # Prepare personalized actions.
    actions = generate_actions(
        recommended,
        priority,
        drainage
    )

    # Add preferred-crop interpretation.
    preferred_evidence = None

    if preferred_crop != "auto":

        crop = next(
            (
                crop
                for crop in result.get(
                    "crop_recommendations", []
                )
                if crop["id"] == preferred_crop
            ),
            None
        )

        if crop:
            preferred_evidence = {
                "crop_id": preferred_crop,
                "crop": crop["name"],
                "kind": crop["kind"],
                "climate_score": crop[
                    "climate_score"
                ],
                "suggested_start_month": crop[
                    "suggested_start_month"
                ],
                "status": crop["status"],
                "management": CROP_MANAGEMENT[
                    preferred_crop
                ],
                "drainage": drainage_assessment(
                    preferred_crop,
                    drainage
                )
            }

    # ========================================
    # 14. PRESERVE EXISTING API FIELDS
    # ========================================

    result["strategies"] = strategies

    result["rotation_options"] = [
        {
            "id": strategy["id"],
            "crop_ids": strategy["crop_ids"],
            "crops": strategy["crops"],
            "screening_index": (
                strategy["priority_index"]
                if strategy["priority_index"] is not None
                else strategy["climate_score"]
            ),
            "approx_total_months": strategy[
                "duration_months"
            ]
        }
        for strategy in strategies
    ]

    result["suggested_activities"] = actions

    result["priority"] = priority
    result["baseline"] = baseline
    result["preferred_crop"] = preferred_crop
    result["drainage"] = drainage

    result["preferred_crop_evidence"] = (
        preferred_evidence
    )

    result["recommended_strategy_id"] = (
        recommended["id"]
        if recommended
        else None
    )

    result["summary"] = history.get(
        "summary", {}
    )

    result["limitations"] = [
        "NASA POWER values are historical gridded environmental estimates.",
        "Crop climate thresholds and ranking weights are provisional.",
        "Compatibility indices are not crop-success probabilities.",
        "Farmer-reported drainage is not a measured soil-water parameter.",
        "Soil-management proxies are not measurements of soil health.",
        "Long-term crop transitions require local feasibility review.",
        "Market prices, yields, revenues and profits are not predicted.",
        "Local soil, pests, infrastructure and buyer conditions require verification."
    ]

    return result
