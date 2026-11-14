
"""
BUMI SHIFT — Historical NASA Climate Engine
HANOVA | Sarawak pilot

Source: NASA POWER Daily Point API
Uses the last 10 complete calendar years.

This module analyzes historical climate.
It does NOT predict crop yield or soil health.
"""

import math
from datetime import date, datetime
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
        "name": "Mean air temperature",
        "unit": "deg C"
    },
    "T2M_MAX": {
        "name": "Maximum air temperature",
        "unit": "deg C"
    },
    "T2M_MIN": {
        "name": "Minimum air temperature",
        "unit": "deg C"
    },
    "RH2M": {
        "name": "Relative humidity",
        "unit": "%"
    },
    "ALLSKY_SFC_SW_DWN": {
        "name": "Daily solar irradiation",
        "unit": "kWh/m2/day"
    }
}


def valid_number(value):
    return (
        isinstance(value, (int, float))
        and not isinstance(value, bool)
        and math.isfinite(value)
        and value != -999
    )


def average(values):
    return round(mean(values), 2) if values else None


def get_historical_climate(latitude, longitude):
    """
    Retrieve historical NASA POWER observations
    and calculate monthly and annual summaries.
    """

    if not (
        -90 <= latitude <= 90
        and -180 <= longitude <= 180
    ):
        raise ValueError("Invalid coordinates.")

    # Exclude the current incomplete calendar year.
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

    data = payload["properties"]["parameter"]

    if not all(p in data for p in PARAMETERS):
        raise ValueError(
            "NASA response is missing required parameters."
        )

    # Store monthly observations.
    monthly = {}

    # Store annual observations.
    annual = {}

    for parameter in PARAMETERS:
        for day, value in data[parameter].items():

            if not valid_number(value):
                continue

            if parameter == "PRECTOTCORR" and value < 0:
                continue

            day_date = datetime.strptime(
                day, "%Y%m%d"
            ).date()

            month_key = day_date.strftime("%Y-%m")
            year_key = str(day_date.year)

            monthly.setdefault(month_key, {})
            monthly[month_key].setdefault(parameter, [])
            monthly[month_key][parameter].append(value)

            annual.setdefault(year_key, {})
            annual[year_key].setdefault(parameter, [])
            annual[year_key][parameter].append(value)

    monthly_results = []

    for month_key in sorted(monthly):
        values = monthly[month_key]

        rain_values = values.get("PRECTOTCORR", [])

        monthly_results.append({
            "month": month_key,
            "rainfall_mm": (
                round(sum(rain_values), 2)
                if rain_values else None
            ),
            "rainfall_valid_days": len(rain_values),
            "temperature_c": average(
                values.get("T2M", [])
            ),
            "maximum_temperature_c": average(
                values.get("T2M_MAX", [])
            ),
            "minimum_temperature_c": average(
                values.get("T2M_MIN", [])
            ),
            "humidity_percent": average(
                values.get("RH2M", [])
            ),
            "solar_kwh_m2_day": average(
                values.get("ALLSKY_SFC_SW_DWN", [])
            )
        })

    annual_results = []

    for year_key in sorted(annual):
        values = annual[year_key]

        rain_values = values.get("PRECTOTCORR", [])

        expected_days = (
            date(int(year_key) + 1, 1, 1)
            - date(int(year_key), 1, 1)
        ).days

        complete_rainfall = (
            len(rain_values) == expected_days
        )

        annual_results.append({
            "year": int(year_key),
            "rainfall_mm": (
                round(sum(rain_values), 2)
                if complete_rainfall else None
            ),
            "rainfall_valid_days": len(rain_values),
            "expected_days": expected_days,
            "rainfall_complete": complete_rainfall,
            "mean_temperature_c": average(
                values.get("T2M", [])
            ),
            "humidity_percent": average(
                values.get("RH2M", [])
            ),
            "solar_kwh_m2_day": average(
                values.get("ALLSKY_SFC_SW_DWN", [])
            )
        })

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
            "mean_annual_rainfall_mm": average(
                rainfall_totals
            ),
            "mean_temperature_c": average(
                temperature_values
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
            "They are not measurements at individual farms.",
            "Missing rainfall days invalidate annual totals.",
            "Temperature means may use incomplete records.",
            "Historical observations are not future forecasts.",
            "Crop suitability requires crop-specific evidence."
        ]
    }
