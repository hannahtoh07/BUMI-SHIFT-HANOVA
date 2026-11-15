
"""
BUMI SHIFT — Rotation Strategy Engine

Compares baseline and alternative crop rotations
using historical NASA climate screening and
experimental soil-management indicators.
"""

from statistics import mean
from crop_engine import CROPS, closeness

MONTHS = [
    "Jan", "Feb", "Mar", "Apr",
    "May", "Jun", "Jul", "Aug",
    "Sep", "Oct", "Nov", "Dec"
]


def enrich(
    result,
    history,
    priority="soil",
    baseline="rice"
):

    if (
        baseline not in CROPS
        or CROPS[baseline]["kind"] != "annual"
    ):
        baseline = "rice"

    monthly = result["monthly_climatology"]

    sequences = [[baseline] * 3]

    for second in [
        "mung_bean",
        "groundnut",
        "sweet_potato",
        "maize",
        "soybean"
    ]:

        sequence = [
            baseline,
            second,
            baseline
        ]

        if sequence not in sequences:
            sequences.append(sequence)

    def score_sequence(sequence, start):

        offset = 0
        scores = []
        rainfall = []

        for crop_id in sequence:

            crop = CROPS[crop_id]

            for step in range(crop["months"]):

                row = monthly[
                    (start + offset + step) % 12
                ]

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
                    return None

                scores.append(
                    0.55 * rain_score
                    + 0.45 * temp_score
                )

                rainfall.append(
                    row["rainfall_mm"]
                )

            offset += crop["months"]

        return {
            "climate_score": round(
                100 * mean(scores),
                1
            ),
            "duration_months": offset,
            "mean_monthly_rain_mm": round(
                mean(rainfall),
                1
            )
        }

    strategies = []

    for sequence in sequences:

        windows = [
            (
                start,
                score_sequence(sequence, start)
            )
            for start in range(12)
        ]

        windows = [
            (start, value)
            for start, value in windows
            if value is not None
        ]

        if not windows:
            continue

        start, detail = max(
            windows,
            key=lambda item: item[1]["climate_score"]
        )

        families = [
            CROPS[crop_id]["family"]
            for crop_id in sequence
        ]

        diversity = len(set(families))

        cover = round(
            mean(
                CROPS[crop_id].get("cover", 0.5)
                for crop_id in sequence
            ) * 100
        )

        legume = any(
            family == "Fabaceae"
            for family in families
        )

        changes = sum(
            families[i] != families[i - 1]
            for i in range(1, len(families))
        )

        soil_proxy = round(
            40 * diversity / 3
            + 35 * cover / 100
            + 25 * changes / 2,
            1
        )

        climate = detail["climate_score"]

        if priority == "soil":

            ranking = round(
                0.55 * soil_proxy
                + 0.45 * climate,
                1
            )

        elif priority == "water":

            ranking = round(
                0.85 * climate
                + 0.15 * soil_proxy,
                1
            )

        elif priority == "resilience":

            ranking = round(
                0.75 * climate
                + 0.25 * soil_proxy,
                1
            )

        else:
            ranking = None

        stages = []
        offset = 0

        for crop_id in sequence:

            duration = CROPS[crop_id]["months"]

            stages.append({
                "crop_id": crop_id,
                "crop": CROPS[crop_id]["name"],
                "start_month": MONTHS[
                    (start + offset) % 12
                ],
                "end_month": MONTHS[
                    (start + offset + duration - 1) % 12
                ],
                "duration_months": duration
            })

            offset += duration

        risks = []

        if detail["mean_monthly_rain_mm"] > 230:

            risks.append(
                "Wet-season exposure: review "
                "drainage and waterlogging sensitivity."
            )

        if legume:

            risks.append(
                "Legume nitrogen benefits depend "
                "on nodulation, residues and management."
            )

        risks.append(
            "Soil pH, pests, market demand and "
            "field drainage are not verified."
        )

        benefits = []

        if diversity > 1:

            benefits.append(
                "Crop-family diversification may "
                "interrupt repeated-crop management patterns."
            )

        else:

            benefits.append(
                "Provides a reference for comparing "
                "alternative crop sequences."
            )

        if legume:

            benefits.append(
                "A legume phase may support nutrient "
                "cycling under suitable management."
            )

        strategies.append({
            "id": "-".join(sequence),
            "type": (
                "baseline"
                if sequence == sequences[0]
                else "alternative"
            ),
            "crop_ids": sequence,
            "crops": [
                CROPS[crop_id]["name"]
                for crop_id in sequence
            ],
            "start_month": MONTHS[start],
            "stages": stages,
            "climate_score": climate,
            "soil_management_proxy": soil_proxy,
            "priority_index": ranking,
            "duration_months": detail[
                "duration_months"
            ],
            "crop_family_count": diversity,
            "legume_included": legume,
            "ground_cover_proxy": cover,
            "evidence": (
                "NASA historical monthly rainfall "
                "and mean temperature; sequence "
                f"starting {MONTHS[start]}; "
                "mean rainfall across occupied months "
                f"{detail['mean_monthly_rain_mm']} mm/month."
            ),
            "potential_benefits": benefits,
            "risks": risks
        })

    baseline_result = next(
        (
            strategy
            for strategy in strategies
            if strategy["type"] == "baseline"
        ),
        None
    )

    for strategy in strategies:

        if baseline_result:

            difference = (
                strategy["climate_score"]
                - baseline_result["climate_score"]
            )

            strategy["comparison_to_baseline"] = (
                f"Climate index difference {difference:+.1f} "
                "points; crop-family count "
                f"{strategy['crop_family_count']} versus "
                f"{baseline_result['crop_family_count']}. "
                "Indices are exploratory."
            )

        else:

            strategy["comparison_to_baseline"] = (
                "Baseline unavailable."
            )

    strategies.sort(
        key=lambda strategy: (
            strategy["type"] != "baseline",
            -(
                strategy["priority_index"]
                if strategy["priority_index"] is not None
                else strategy["climate_score"]
            )
        )
    )

    best = next(
        (
            strategy
            for strategy in strategies
            if strategy["type"] == "alternative"
        ),
        None
    )

    actions = []

    if best:

        for i, stage in enumerate(best["stages"]):

            actions.append({
                "title": (
                    f"Stage {i+1}: prepare for "
                    f"{stage['crop']}"
                ),
                "reason": (
                    f"Candidate window "
                    f"{stage['start_month']}–"
                    f"{stage['end_month']} "
                    f"({stage['duration_months']} months). "
                    "Check seed availability and "
                    "field suitability."
                ),
                "category": "Crop calendar"
            })

        if best["legume_included"]:

            actions.append({
                "title": (
                    "Review legume establishment "
                    "and residue management"
                ),
                "reason": (
                    "Check nodulation, wet-season "
                    "sensitivity and how crop residues "
                    "will be managed after harvest."
                ),
                "category": "Nutrient cycling"
            })

        if best["ground_cover_proxy"] < 70:

            actions.append({
                "title": "Reduce bare-soil intervals",
                "reason": (
                    "Consider suitable ground cover "
                    "or residue retention between crops."
                ),
                "category": "Soil cover"
            })

        if any(
            "Wet-season" in risk
            for risk in best["risks"]
        ):

            actions.append({
                "title": (
                    "Inspect drainage before "
                    "wet-season planting"
                ),
                "reason": (
                    "Historical rainfall exposure "
                    "is elevated for this candidate "
                    "sequence; field drainage still "
                    "requires local checking."
                ),
                "category": "Water management"
            })

        actions.append({
            "title": "Compare against your baseline",
            "reason": best[
                "comparison_to_baseline"
            ],
            "category": "Decision"
        })

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
    result["summary"] = history.get("summary", {})

    result["limitations"] = [
        "Crop climate envelopes and scoring weights are prototype assumptions.",
        "Soil-health proxies are not predictions of organic carbon, nitrogen or yield.",
        "The baseline is an assumed reference unless the farmer confirms their actual rotation.",
        "Historical averages do not forecast future weather.",
        "Calendar, market and field-level soil feasibility need local review."
    ]

    return result
