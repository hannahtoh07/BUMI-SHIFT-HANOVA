
"""
BUMI SHIFT 7.1
NASA Historical Environmental Engine
HANOVA | Sarawak, Malaysia

Source: NASA POWER Daily Point API

Provides:
- 10 complete historical calendar years
- 8 environmental indicators
- 120 monthly historical summaries
- 12-month climatology
- Annual observations
- Historical trends and variability
- Data completeness diagnostics
- Compatible crop and strategy inputs

NASA POWER provides gridded estimates,
not field measurements or future forecasts.
"""

import math
import logging
from calendar import monthrange
from datetime import date, timedelta
from functools import lru_cache
from statistics import mean, pstdev

import requests

logger = logging.getLogger("bumi_shift.climate")

NASA_POWER_URL = (
    "https://power.larc.nasa.gov/"
    "api/temporal/daily/point"
)

CORE_PARAMETERS = [
    "PRECTOTCORR",
    "T2M",
    "T2M_MAX",
    "T2M_MIN",
    "RH2M",
    "ALLSKY_SFC_SW_DWN"
]

OPTIONAL_PARAMETERS = ["WS2M", "PS"]
PARAMETERS = CORE_PARAMETERS + OPTIONAL_PARAMETERS

FIELD_NAMES = {
    "PRECTOTCORR": "rainfall_mm",
    "T2M": "temperature_c",
    "T2M_MAX": "maximum_temperature_c",
    "T2M_MIN": "minimum_temperature_c",
    "RH2M": "humidity_percent",
    "ALLSKY_SFC_SW_DWN": "solar_kwh_m2_day",
    "WS2M": "wind_speed_m_s",
    "PS": "pressure_kpa"
}

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
    },
    "WS2M": {
        "name": "Wind speed",
        "unit": "m/s"
    },
    "PS": {
        "name": "Surface pressure",
        "unit": "kPa"
    }
}

MIN_COMPLETENESS = 0.90


# ============================================
# 1. VALIDATION AND STATISTICS
# ============================================

def valid_number(value):
    return (
        isinstance(value, (int, float))
        and not isinstance(value, bool)
        and math.isfinite(value)
        and value != -999
    )


def safe_average(values):
    numbers = [
        float(v) for v in values
        if valid_number(v)
    ]
    return round(mean(numbers), 2) if numbers else None


def safe_std(values):
    numbers = [
        float(v) for v in values
        if valid_number(v)
    ]
    return (
        round(pstdev(numbers), 2)
        if len(numbers) >= 2 else None
    )


def coverage(count, expected):
    return (
        round(count / expected, 4)
        if expected > 0 else 0.0
    )


def linear_trend(rows, field):
    points = [
        (row["year"], row[field])
        for row in rows
        if valid_number(row.get(field))
    ]

    if len(points) < 3:
        return None

    x_mean = mean(x for x, _ in points)
    y_mean = mean(y for _, y in points)

    denominator = sum(
        (x - x_mean) ** 2 for x, _ in points
    )

    if denominator == 0:
        return None

    slope = sum(
        (x - x_mean) * (y - y_mean)
        for x, y in points
    ) / denominator

    return round(slope, 4)


# ============================================
# 2. NASA POWER RETRIEVAL
# ============================================

def request_nasa(
    latitude, longitude,
    start_year, end_year,
    parameters
):
    params = {
        "parameters": ",".join(parameters),
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
    data = payload.get(
        "properties", {}
    ).get("parameter", {})

    if not isinstance(data, dict):
        raise ValueError(
            "Invalid NASA POWER parameter response."
        )

    return data


def retrieve_parameters(
    latitude, longitude,
    start_year, end_year
):
    # Retrieve essential parameters first.
    data = request_nasa(
        latitude, longitude,
        start_year, end_year,
        CORE_PARAMETERS
    )

    for parameter in CORE_PARAMETERS:
        if parameter not in data:
            raise ValueError(
                f"Missing NASA parameter: {parameter}"
            )

    optional_status = {}

    # Optional failures must not erase core data.
    for parameter in OPTIONAL_PARAMETERS:
        try:
            extra = request_nasa(
                latitude, longitude,
                start_year, end_year,
                [parameter]
            )

            if parameter in extra:
                data[parameter] = extra[parameter]
                optional_status[parameter] = "retrieved"
            else:
                optional_status[parameter] = "not_returned"

        except (requests.RequestException, ValueError):
            logger.warning(
                "Optional NASA parameter unavailable: %s",
                parameter
            )
            optional_status[parameter] = "not_retrieved"

    return data, optional_status


# ============================================
# 3. BUILD DAILY RECORDS
# ============================================

def build_daily_records(
    parameter_data,
    start_year,
    end_year
):
    records = []
    current = date(start_year, 1, 1)
    final = date(end_year, 12, 31)

    while current <= final:
        key = current.strftime("%Y%m%d")

        row = {
            "date": key,
            "year": current.year,
            "month": current.month
        }

        for parameter in PARAMETERS:
            raw = parameter_data.get(
                parameter, {}
            ).get(key)

            if not valid_number(raw):
                value = None
            else:
                value = float(raw)

                if parameter in {
                    "PRECTOTCORR",
                    "ALLSKY_SFC_SW_DWN",
                    "WS2M"
                } and value < 0:
                    value = None

                elif parameter == "RH2M" and not (
                    0 <= value <= 100
                ):
                    value = None

                elif parameter == "PS" and value <= 0:
                    value = None

                # NASA POWER solar irradiation:
                # MJ/m2/day -> kWh/m2/day.
                elif parameter == "ALLSKY_SFC_SW_DWN":
                    value = value / 3.6

            row[parameter] = value

        records.append(row)
        current += timedelta(days=1)

    return records


# ============================================
# 4. PERIOD SUMMARIZATION
# ============================================

def summarize_days(days, expected_days):
    result = {
        "expected_days": expected_days,
        "valid_days": {},
        "completeness": {}
    }

    for parameter in PARAMETERS:
        values = [
            row[parameter]
            for row in days
            if valid_number(row.get(parameter))
        ]

        count = len(values)
        field = FIELD_NAMES[parameter]

        result["valid_days"][parameter] = count
        result["completeness"][parameter] = coverage(
            count, expected_days
        )

        if parameter == "PRECTOTCORR":
            # Never estimate missing rainfall days.
            result[field] = (
                round(sum(values), 2)
                if count == expected_days
                else None
            )
        else:
            result[field] = (
                safe_average(values)
                if coverage(count, expected_days)
                >= MIN_COMPLETENESS
                else None
            )

    result["rainfall_valid_days"] = (
        result["valid_days"]["PRECTOTCORR"]
    )
    result["rainfall_complete"] = (
        result["rainfall_valid_days"] == expected_days
    )

    return result


# ============================================
# 5. HISTORICAL MONTHLY DATA
# ============================================

def build_historical_monthly(
    daily, start_year, end_year
):
    groups = {}

    for row in daily:
        key = (row["year"], row["month"])
        groups.setdefault(key, []).append(row)

    output = []

    for year in range(start_year, end_year + 1):
        for month in range(1, 13):
            days = groups.get((year, month), [])

            summary = summarize_days(
                days,
                monthrange(year, month)[1]
            )

            output.append({
                "year": year,
                "month": month,
                "period": f"{year}-{month:02d}",
                **summary
            })

    return output


# ============================================
# 6. ANNUAL DATA
# ============================================

def build_annual(daily, start_year, end_year):
    groups = {}

    for row in daily:
        groups.setdefault(
            row["year"], []
        ).append(row)

    output = []

    for year in range(start_year, end_year + 1):
        days = groups.get(year, [])

        expected = (
            date(year + 1, 1, 1)
            - date(year, 1, 1)
        ).days

        summary = summarize_days(days, expected)

        output.append({
            "year": year,
            **summary,
            "mean_temperature_c": summary[
                "temperature_c"
            ]
        })

    return output


# ============================================
# 7. TWELVE-MONTH CLIMATOLOGY
# ============================================

def build_monthly_climatology(
    historical_monthly
):
    output = []

    for month in range(1, 13):
        rows = [
            r for r in historical_monthly
            if r["month"] == month
        ]

        result = {
            "month": month,
            "years_requested": len(rows)
        }

        for parameter, field in FIELD_NAMES.items():
            values = [
                r[field] for r in rows
                if valid_number(r.get(field))
            ]

            result[field] = safe_average(values)
            result[field + "_years"] = len(values)

        # Compatibility with existing crop engine.
        result["t2m"] = result["temperature_c"]
        result["rainfall_years"] = result[
            "rainfall_mm_years"
        ]
        result["temperature_years"] = result[
            "temperature_c_years"
        ]

        output.append(result)

    return output


# ============================================
# 8. DATA QUALITY REPORT
# ============================================

def build_quality(
    historical_monthly,
    annual,
    optional_status
):
    incomplete_months = [
        r["period"]
        for r in historical_monthly
        if not r["rainfall_complete"]
    ]

    complete_years = [
        r["year"]
        for r in annual
        if r["rainfall_complete"]
    ]

    return {
        "minimum_completeness_fraction":
            MIN_COMPLETENESS,
        "rainfall_requires_complete_period": True,
        "complete_rainfall_years": complete_years,
        "incomplete_rainfall_months":
            incomplete_months,
        "incomplete_rainfall_month_count":
            len(incomplete_months),
        "optional_parameter_status":
            optional_status
    }


# ============================================
# 9. HISTORICAL VARIABILITY
# ============================================

def build_variability(annual):
    rain = [
        r["rainfall_mm"] for r in annual
        if valid_number(r.get("rainfall_mm"))
    ]

    temp = [
        r["temperature_c"] for r in annual
        if valid_number(r.get("temperature_c"))
    ]

    rain_mean = safe_average(rain)
    rain_std = safe_std(rain)

    cv = (
        round(100 * rain_std / rain_mean, 2)
        if rain_mean and rain_std is not None
        else None
    )

    return {
        "rainfall_standard_deviation_mm": rain_std,
        "rainfall_coefficient_variation_percent": cv,
        "temperature_standard_deviation_c":
            safe_std(temp),
        "rainfall_trend_mm_per_year":
            linear_trend(annual, "rainfall_mm"),
        "temperature_trend_c_per_year":
            linear_trend(annual, "temperature_c"),
        "complete_rainfall_years": len(rain)
    }


# ============================================
# 10. ENVIRONMENTAL SUMMARY
# ============================================

def build_summary(annual, climatology):
    rain = [
        r["rainfall_mm"] for r in annual
        if valid_number(r.get("rainfall_mm"))
    ]

    temp = [
        r["temperature_c"] for r in annual
        if valid_number(r.get("temperature_c"))
    ]

    def climatology_mean(field):
        return safe_average([
            r[field] for r in climatology
            if valid_number(r.get(field))
        ])

    mean_temp = safe_average(temp)

    return {
        "mean_annual_rainfall_mm":
            safe_average(rain),
        "mean_temperature_c": mean_temp,
        "mean_annual_temperature_c": mean_temp,
        "mean_maximum_temperature_c":
            climatology_mean("maximum_temperature_c"),
        "mean_minimum_temperature_c":
            climatology_mean("minimum_temperature_c"),
        "mean_humidity_percent":
            climatology_mean("humidity_percent"),
        "mean_solar_kwh_m2_day":
            climatology_mean("solar_kwh_m2_day"),
        "mean_wind_speed_m_s":
            climatology_mean("wind_speed_m_s"),
        "mean_pressure_kpa":
            climatology_mean("pressure_kpa"),
        "complete_rainfall_years": len(rain),
        "years_requested": len(annual)
    }


# ============================================
# 11. CHART DATA
# ============================================

def build_charts(monthly, annual):
    def monthly_chart(field):
        return [
            {
                "month": r["month"],
                "value": r.get(field)
            }
            for r in monthly
        ]

    def annual_chart(field):
        return [
            {
                "year": r["year"],
                "value": r.get(field)
            }
            for r in annual
        ]

    return {
        "monthly_rainfall":
            monthly_chart("rainfall_mm"),
        "monthly_temperature": [
            {
                "month": r["month"],
                "mean": r["temperature_c"],
                "maximum": r["maximum_temperature_c"],
                "minimum": r["minimum_temperature_c"]
            }
            for r in monthly
        ],
        "monthly_humidity":
            monthly_chart("humidity_percent"),
        "monthly_solar":
            monthly_chart("solar_kwh_m2_day"),
        "monthly_wind":
            monthly_chart("wind_speed_m_s"),
        "monthly_pressure":
            monthly_chart("pressure_kpa"),
        "annual_rainfall":
            annual_chart("rainfall_mm"),
        "annual_temperature":
            annual_chart("temperature_c")
    }


# ============================================
# 12. MAIN NASA ENGINE
# ============================================

@lru_cache(maxsize=64)
def _get_historical_climate(
    latitude, longitude, end_year
):
    start_year = end_year - 9

    data, optional_status = retrieve_parameters(
        latitude,
        longitude,
        start_year,
        end_year
    )

    daily = build_daily_records(
        data, start_year, end_year
    )

    historical_monthly = build_historical_monthly(
        daily, start_year, end_year
    )

    annual = build_annual(
        daily, start_year, end_year
    )

    monthly = build_monthly_climatology(
        historical_monthly
    )

    summary = build_summary(annual, monthly)
    variability = build_variability(annual)

    latest = next(
        (
            r["date"]
            for r in reversed(daily)
            if any(
                valid_number(r.get(p))
                for p in CORE_PARAMETERS
            )
        ),
        None
    )

    quality = build_quality(
        historical_monthly,
        annual,
        optional_status
    )

    return {
        "source": "NASA POWER Daily Point API",
        "source_url": NASA_POWER_URL,
        "latitude": latitude,
        "longitude": longitude,
        "start_year": start_year,
        "end_year": end_year,
        "latest_observation": latest,
        "parameters": PARAMETER_INFO,
        "optional_parameter_status":
            optional_status,
        "summary": summary,
        "variability": variability,
        "annual": annual,
        "monthly": monthly,
        "monthly_climatology": monthly,
        "historical_monthly": historical_monthly,
        "charts": build_charts(monthly, annual),
        "data_quality": quality,
        "limitations": [
            "NASA POWER values are gridded estimates.",
            "Historical observations are not forecasts.",
            "Missing rainfall days are never imputed.",
            "Incomplete rainfall totals are excluded.",
            "Non-rainfall averages require at least 90% coverage.",
            "Crop thresholds are provisional assumptions.",
            "Farm-level soil and drainage are not measured.",
            "Climate screening is not a yield prediction."
        ]
    }


# ============================================
# 13. PUBLIC FUNCTION
# ============================================

def get_historical_climate(latitude, longitude):
    latitude = float(latitude)
    longitude = float(longitude)

    if not (
        math.isfinite(latitude)
        and math.isfinite(longitude)
        and -90 <= latitude <= 90
        and -180 <= longitude <= 180
    ):
        raise ValueError("Invalid coordinates.")

    latitude = round(latitude, 4)
    longitude = round(longitude, 4)

    end_year = date.today().year - 1

    return _get_historical_climate(
        latitude,
        longitude,
        end_year
    )
