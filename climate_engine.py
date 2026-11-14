
"""
BUMI SHIFT 5.0 — NASA Historical Climate Engine
HANOVA | Sarawak, Malaysia

Source:
NASA POWER Daily Point API

Purpose:
- Retrieve 10 complete calendar years of climate data
- Calculate monthly and annual climate summaries
- Identify incomplete observations
- Prepare environmental evidence for crop screening

Historical climate screening is not a weather
forecast or a validated crop-yield prediction.
"""

import math
from calendar import monthrange
from datetime import date
from statistics import mean

import requests


NASA_POWER_URL = (
    "https://power.larc.nasa.gov/"
    "api/temporal/daily/point"
)

PARAMETERS = [
    "PRECTOTCORR",
    "T2M",
    "T2M_MAX",
    "T2M_MIN",
    "RH2M",
    "ALLSKY_SFC_SW_DWN"
]

PARAMETER_INFO = {
    "PRECTOTCORR": {
        "name": "Precipitation",
        "unit": "mm/day"
    },
    "T2M": {
        "name": "Mean temperature",
        "unit": "deg C"
    },
    "T2M_MAX": {
        "name": "Maximum temperature",
        "unit": "deg C"
    },
    "T2M_MIN": {
        "name": "Minimum temperature",
        "unit": "deg C"
    },
    "RH2M": {
        "name": "Relative humidity",
        "unit": "%"
    },
    "ALLSKY_SFC_SW_DWN": {
        "name": "Solar irradiation",
        "unit": "kWh/m2/day"
    }
}


# ============================================
# 1. DATA VALIDATION
# ============================================

def valid_number(value):
    return (
        isinstance(value, (int, float))
        and not isinstance(value, bool)
        and math.isfinite(value)
        and value != -999
    )


def safe_average(values):
    if not values:
        return None

    return round(mean(values), 2)


# ============================================
# 2. NASA DATA RETRIEVAL
# ============================================

def get_historical_climate(latitude, longitude):

    if not (
        -90 <= latitude <= 90
        and -180 <= longitude <= 180
    ):
        raise ValueError("Invalid coordinates.")

    # Exclude the current incomplete year.
    end_year = date.today().year - 1
    start_year = end_year - 9

    params = {
        "parameters": ",".join(PARAMETERS),
        "community": "AG",
        "latitude": latitude,
        "longitude": longitude,
        "start": f"{start_year}0101",
        "end": f"{end_year}1231",
        "format": "JSON",
        "time-standard": "UTC"
    }

    response = requests.get(
        NASA_POWER_URL,
        params=params,
        timeout=120
    )

    response.raise_for_status()

    payload = response.json()

    parameter_data = payload[
        "properties"
    ]["parameter"]

    for parameter in PARAMETERS:
        if parameter not in parameter_data:
            raise ValueError(
                f"Missing NASA parameter: {parameter}"
            )

    # ========================================
    # 3. BUILD DAILY RECORDS
    # ========================================

    monthly_groups = {}
    annual_groups = {}

    for parameter in PARAMETERS:

        for day, value in parameter_data[
            parameter
        ].items():

            if not valid_number(value):
                continue

            if (
                parameter == "PRECTOTCORR"
                and value < 0
            ):
                continue

            year = int(day[:4])
            month = int(day[4:6])

            month_key = f"{year}-{month:02d}"
            year_key = str(year)

            monthly_groups.setdefault(
                month_key, {}
            )

            monthly_groups[
                month_key
            ].setdefault(parameter, []).append(value)

            annual_groups.setdefault(
                year_key, {}
            )

            annual_groups[
                year_key
            ].setdefault(parameter, []).append(value)

    # ========================================
    # 4. MONTHLY SUMMARIES
    # ========================================

    monthly_results = []

    for month_key in sorted(monthly_groups):

        values = monthly_groups[month_key]

        year, month = map(
            int,
            month_key.split("-")
        )

        expected_days = monthrange(
            year, month
        )[1]

        rainfall_values = values.get(
            "PRECTOTCORR", []
        )

        complete_rainfall = (
            len(rainfall_values) == expected_days
        )

        monthly_results.append({
            "month": month_key,
            "rainfall_mm": (
                round(sum(rainfall_values), 2)
                if complete_rainfall
                else None
            ),
            "rainfall_valid_days": len(
                rainfall_values
            ),
            "rainfall_complete": complete_rainfall,
            "temperature_c": safe_average(
                values.get("T2M", [])
            ),
            "maximum_temperature_c": safe_average(
                values.get("T2M_MAX", [])
            ),
            "minimum_temperature_c": safe_average(
                values.get("T2M_MIN", [])
            ),
            "humidity_percent": safe_average(
                values.get("RH2M", [])
            ),
            "solar_kwh_m2_day": safe_average(
                values.get("ALLSKY_SFC_SW_DWN", [])
            ),
            "expected_days": expected_days
        })

    # ========================================
    # 5. ANNUAL SUMMARIES
    # ========================================

    annual_results = []

    for year_key in sorted(annual_groups):

        values = annual_groups[year_key]

        year = int(year_key)

        expected_days = (
            date(year + 1, 1, 1)
            - date(year, 1, 1)
        ).days

        rainfall_values = values.get(
            "PRECTOTCORR", []
        )

        complete_rainfall = (
            len(rainfall_values) == expected_days
        )

        annual_results.append({
            "year": year,
            "rainfall_mm": (
                round(sum(rainfall_values), 2)
                if complete_rainfall
                else None
            ),
            "rainfall_valid_days": len(
                rainfall_values
            ),
            "rainfall_complete": complete_rainfall,
            "mean_temperature_c": safe_average(
                values.get("T2M", [])
            ),
            "humidity_percent": safe_average(
                values.get("RH2M", [])
            ),
            "solar_kwh_m2_day": safe_average(
                values.get("ALLSKY_SFC_SW_DWN", [])
            )
        })

    # ========================================
    # 6. CLIMATE SUMMARY
    # ========================================

    complete_years = [
        row for row in annual_results
        if row["rainfall_complete"]
    ]

    rainfall_totals = [
        row["rainfall_mm"]
        for row in complete_years
    ]

    temperature_values = [
        row["mean_temperature_c"]
        for row in annual_results
        if row["mean_temperature_c"] is not None
    ]

    return {
        "source": "NASA POWER Daily Point API",
        "source_url": NASA_POWER_URL,
        "latitude": latitude,
        "longitude": longitude,
        "start_year": start_year,
        "end_year": end_year,
        "parameters": PARAMETER_INFO,
        "summary": {
            "mean_annual_rainfall_mm": (
                safe_average(rainfall_totals)
            ),
            "mean_temperature_c": (
                safe_average(temperature_values)
            ),
            "complete_rainfall_years": len(
                complete_years
            ),
            "years_requested": 10
        },
        "monthly": monthly_results,
        "annual": annual_results,
        "limitations": [
            "NASA POWER values are gridded estimates.",
            "Historical observations are not forecasts.",
            "Incomplete rainfall periods are excluded.",
            "Some temperature means may use incomplete records.",
            "Farm-level soil conditions are not measured.",
            "Crop-specific suitability requires additional evidence."
        ]
    }
