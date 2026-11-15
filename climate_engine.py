
"""
BUMI SHIFT 6.4 — NASA Environmental Data Engine
HANOVA | Sarawak, Malaysia

NASA POWER Daily Point API

Features:
- Ten complete historical calendar years
- Rainfall, temperature, humidity and solar radiation
- Wind speed and atmospheric pressure
- Monthly and annual environmental summaries
- Twelve-month climatology for dashboard charts
- Historical variability and trends
- Data completeness and quality checks
- Compatible output for crop and rotation screening

Historical environmental estimates are not
field measurements or future weather forecasts.
"""

import math
from calendar import monthrange
from datetime import date
from functools import lru_cache
from statistics import mean, pstdev

import requests


NASA_POWER_URL = (
    "https://power.larc.nasa.gov/"
    "api/temporal/daily/point"
)

# Core variables required for crop screening.
CORE_PARAMETERS = [
    "PRECTOTCORR",
    "T2M",
    "T2M_MAX",
    "T2M_MIN",
    "RH2M",
    "ALLSKY_SFC_SW_DWN"
]

# Supplementary environmental indicators.
OPTIONAL_PARAMETERS = [
    "WS2M",
    "PS"
]

PARAMETERS = CORE_PARAMETERS + OPTIONAL_PARAMETERS

PARAMETER_INFO = {
    "PRECTOTCORR": {
        "name": "Precipitation",
        "unit": "mm/day",
        "role": "Crop climate screening"
    },
    "T2M": {
        "name": "Mean temperature",
        "unit": "deg C",
        "role": "Crop climate screening"
    },
    "T2M_MAX": {
        "name": "Maximum temperature",
        "unit": "deg C",
        "role": "Environmental context"
    },
    "T2M_MIN": {
        "name": "Minimum temperature",
        "unit": "deg C",
        "role": "Environmental context"
    },
    "RH2M": {
        "name": "Relative humidity",
        "unit": "%",
        "role": "Environmental context"
    },
    "ALLSKY_SFC_SW_DWN": {
        "name": "Solar irradiation",
        "unit": "kWh/m2/day",
        "role": "Environmental context"
    },
    "WS2M": {
        "name": "Wind speed at 2 m",
        "unit": "m/s",
        "role": "Environmental context"
    },
    "PS": {
        "name": "Surface pressure",
        "unit": "kPa",
        "role": "Environmental context"
    }
}

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

MIN_COMPLETENESS = 0.90


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

    values = [
        float(value)
        for value in values
        if valid_number(value)
    ]

    if not values:
        return None

    return round(mean(values), 2)


def safe_std(values):

    values = [
        float(value)
        for value in values
        if valid_number(value)
    ]

    if len(values) < 2:
        return None

    return round(pstdev(values), 2)


def safe_round(value, digits=2):

    if not valid_number(value):
        return None

    return round(float(value), digits)


def completeness(valid_days, expected_days):

    if expected_days <= 0:
        return 0.0

    return round(valid_days / expected_days, 4)


def acceptable(valid_days, expected_days):

    return (
        completeness(valid_days, expected_days)
        >= MIN_COMPLETENESS
    )


# ============================================
# 2. NASA POWER REQUEST
# ============================================

def request_nasa(
    latitude,
    longitude,
    start_year,
    end_year,
    parameters
):

    query = {
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
        params=query,
        timeout=120
    )

    response.raise_for_status()

    payload = response.json()

    if "properties" not in payload:
        raise ValueError(
            "NASA POWER returned an invalid response."
        )

    data = payload["properties"].get(
        "parameter",
        {}
    )

    if not isinstance(data, dict):
        raise ValueError(
            "NASA parameter data is invalid."
        )

    return data


def retrieve_parameters(
    latitude,
    longitude,
    start_year,
    end_year
):

    # Core parameters are essential.
    core = request_nasa(
        latitude,
        longitude,
        start_year,
        end_year,
        CORE_PARAMETERS
    )

    for parameter in CORE_PARAMETERS:

        if parameter not in core:
            raise ValueError(
                "Missing required NASA parameter: "
                + parameter
            )

    # Retrieve supplementary parameters separately.
    # Failure of an optional request must not erase
    # the successfully retrieved core dataset.

    available = dict(core)
    optional_status = {}

    for parameter in OPTIONAL_PARAMETERS:

        try:

            extra = request_nasa(
                latitude,
                longitude,
                start_year,
                end_year,
                [parameter]
            )

            if parameter in extra:
                available[parameter] = extra[parameter]
                optional_status[parameter] = "retrieved"
            else:
                optional_status[parameter] = "not_returned"

        except (requests.RequestException, ValueError):
            optional_status[parameter] = "not_retrieved"

    return available, optional_status


# ============================================
# 3. BUILD DAILY RECORDS
# ============================================

def build_daily_records(
    parameter_data,
    start_year,
    end_year
):

    records = []

    for year in range(start_year, end_year + 1):

        current = date(year, 1, 1)
        last = date(year, 12, 31)

        while current <= last:

            day_key = current.strftime("%Y%m%d")

            row = {
                "date": day_key,
                "year": current.year,
                "month": current.month
            }

            for parameter in PARAMETERS:

                values = parameter_data.get(
                    parameter,
                    {}
                )

                value = values.get(day_key)

                if valid_number(value):

                    if (
                        parameter == "PRECTOTCORR"
                        and value < 0
                    ):
                        value = None

                    else:
                        value = float(value)

                else:
                    value = None

                row[parameter] = value

            records.append(row)

            current = date.fromordinal(
                current.toordinal() + 1
            )

    return records


# ============================================
# 4. AGGREGATE OBSERVATIONS
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

        result["valid_days"][parameter] = count

        result["completeness"][parameter] = (
            completeness(count, expected_days)
        )

        field = FIELD_NAMES[parameter]

        # Rainfall is a total and must have
        # complete daily coverage.

        if parameter == "PRECTOTCORR":

            result[field] = (
                round(sum(values), 2)
                if count == expected_days
                else None
            )

        else:

            result[field] = (
                safe_average(values)
                if acceptable(count, expected_days)
                else None
            )

    result["rainfall_valid_days"] = (
        result["valid_days"]["PRECTOTCORR"]
    )

    result["rainfall_complete"] = (
        result["rainfall_valid_days"]
        == expected_days
    )

    return result


# ============================================
# 5. HISTORICAL MONTHLY SUMMARIES
# ============================================

def build_historical_monthly(daily, start_year, end_year):

    output = []

    for year in range(start_year, end_year + 1):

        for month in range(1, 13):

            days = [
                row
                for row in daily
                if row["year"] == year
                and row["month"] == month
            ]

            expected = monthrange(
                year,
                month
            )[1]

            summary = summarize_days(
                days,
                expected
            )

            output.append({
                "year": year,
                "month": month,
                "period": f"{year}-{month:02d}",
                **summary
            })

    return output


# ============================================
# 6. ANNUAL SUMMARIES
# ============================================

def build_annual(daily, start_year, end_year):

    output = []

    for year in range(start_year, end_year + 1):

        days = [
            row
            for row in daily
            if row["year"] == year
        ]

        expected = (
            date(year + 1, 1, 1)
            - date(year, 1, 1)
        ).days

        summary = summarize_days(
            days,
            expected
        )

        output.append({
            "year": year,
            **summary,

            # Compatibility with older dashboards.
            "mean_temperature_c": summary.get(
                "temperature_c"
            ),
            "solar_kwh_m2_day": summary.get(
                "solar_kwh_m2_day"
            )
        })

    return output


# ============================================
# 7. TWELVE-MONTH CLIMATOLOGY
# ============================================

def build_monthly_climatology(historical_monthly):

    output = []

    for month in range(1, 13):

        rows = [
            row
            for row in historical_monthly
            if row["month"] == month
        ]

        result = {
            "month": month,
            "years_requested": len(rows)
        }

        for parameter, field in FIELD_NAMES.items():

            values = [
                row[field]
                for row in rows
                if valid_number(row.get(field))
            ]

            result[field] = safe_average(values)

            result[field + "_years"] = len(values)

        # Crop-engine compatibility.
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
# 8. HISTORICAL VARIABILITY
# ============================================

def linear_trend(rows, field):

    points = [
        (
            row["year"],
            row[field]
        )
        for row in rows
        if valid_number(row.get(field))
    ]

    if len(points) < 3:
        return None

    xs = [p[0] for p in points]
    ys = [p[1] for p in points]

    x_mean = mean(xs)
    y_mean = mean(ys)

    denominator = sum(
        (x - x_mean) ** 2
        for x in xs
    )

    if denominator == 0:
        return None

    slope = sum(
        (x - x_mean) * (y - y_mean)
        for x, y in points
    ) / denominator

    return round(slope, 4)


def build_variability(annual):

    rainfall = [
        row["rainfall_mm"]
        for row in annual
        if valid_number(row.get("rainfall_mm"))
    ]

    temperatures = [
        row["temperature_c"]
        for row in annual
        if valid_number(row.get("temperature_c"))
    ]

    rain_mean = safe_average(rainfall)
    rain_std = safe_std(rainfall)

    coefficient = None

    if (
        rain_mean is not None
        and rain_std is not None
        and rain_mean > 0
    ):
        coefficient = round(
            100 * rain_std / rain_mean,
            2
        )

    return {
        "rainfall_standard_deviation_mm": rain_std,
        "rainfall_coefficient_variation_percent": coefficient,
        "temperature_standard_deviation_c": safe_std(
            temperatures
        ),
        "rainfall_trend_mm_per_year": linear_trend(
            annual,
            "rainfall_mm"
        ),
        "temperature_trend_c_per_year": linear_trend(
            annual,
            "temperature_c"
        ),
        "complete_rainfall_years": len(rainfall)
    }


# ============================================
# 9. ENVIRONMENTAL SUMMARY
# ============================================

def build_summary(annual, climatology):

    rainfall = [
        row["rainfall_mm"]
        for row in annual
        if valid_number(row.get("rainfall_mm"))
    ]

    temperature = [
        row["temperature_c"]
        for row in annual
        if valid_number(row.get("temperature_c"))
    ]

    def monthly_average(field):

        values = [
            row[field]
            for row in climatology
            if valid_number(row.get(field))
        ]

        return safe_average(values)

    mean_temp = safe_average(temperature)

    return {
        "mean_annual_rainfall_mm": safe_average(
            rainfall
        ),
        "mean_temperature_c": mean_temp,

        # Alias for compatibility.
        "mean_annual_temperature_c": mean_temp,

        "mean_maximum_temperature_c": monthly_average(
            "maximum_temperature_c"
        ),
        "mean_minimum_temperature_c": monthly_average(
            "minimum_temperature_c"
        ),
        "mean_humidity_percent": monthly_average(
            "humidity_percent"
        ),
        "mean_solar_kwh_m2_day": monthly_average(
            "solar_kwh_m2_day"
        ),
        "mean_wind_speed_m_s": monthly_average(
            "wind_speed_m_s"
        ),
        "mean_pressure_kpa": monthly_average(
            "pressure_kpa"
        ),
        "complete_rainfall_years": len(rainfall),
        "years_requested": len(annual)
    }


# ============================================
# 10. MAIN CLIMATE FUNCTION
# ============================================

@lru_cache(maxsize=64)
def _get_historical_climate(latitude, longitude, end_year):

    start_year = end_year - 9

    parameter_data, optional_status = retrieve_parameters(
        latitude,
        longitude,
        start_year,
        end_year
    )

    daily = build_daily_records(
        parameter_data,
        start_year,
        end_year
    )

    historical_monthly = build_historical_monthly(
        daily,
        start_year,
        end_year
    )

    annual = build_annual(
        daily,
        start_year,
        end_year
    )

    climatology = build_monthly_climatology(
        historical_monthly
    )

    summary = build_summary(
        annual,
        climatology
    )

    variability = build_variability(
        annual
    )

    latest_available = None

    for row in reversed(daily):

        if any(
            valid_number(row.get(parameter))
            for parameter in CORE_PARAMETERS
        ):
            latest_available = row["date"]
            break

    return {
        "source": "NASA POWER Daily Point API",
        "source_url": NASA_POWER_URL,
        "latitude": latitude,
        "longitude": longitude,
        "start_year": start_year,
        "end_year": end_year,
        "latest_observation": latest_available,
        "parameters": PARAMETER_INFO,
        "optional_parameter_status": optional_status,

        # Core outputs.
        "summary": summary,
        "variability": variability,
        "annual": annual,

        # Crop engine and 12-month charts.
        "monthly": climatology,
        "monthly_climatology": climatology,

        # Full 120-month historical dataset.
        "historical_monthly": historical_monthly,

        # Explicit chart-ready datasets.
        "charts": {
            "monthly_rainfall": [
                {
                    "month": row["month"],
                    "value": row["rainfall_mm"]
                }
                for row in climatology
            ],
            "monthly_temperature": [
                {
                    "month": row["month"],
                    "mean": row["temperature_c"],
                    "maximum": row[
                        "maximum_temperature_c"
                    ],
                    "minimum": row[
                        "minimum_temperature_c"
                    ]
                }
                for row in climatology
            ],
            "monthly_humidity": [
                {
                    "month": row["month"],
                    "value": row["humidity_percent"]
                }
                for row in climatology
            ],
            "monthly_solar": [
                {
                    "month": row["month"],
                    "value": row["solar_kwh_m2_day"]
                }
                for row in climatology
            ],
            "monthly_wind": [
                {
                    "month": row["month"],
                    "value": row["wind_speed_m_s"]
                }
                for row in climatology
            ],
            "monthly_pressure": [
                {
                    "month": row["month"],
                    "value": row["pressure_kpa"]
                }
                for row in climatology
            ],
            "annual_rainfall": [
                {
                    "year": row["year"],
                    "value": row["rainfall_mm"]
                }
                for row in annual
            ],
            "annual_temperature": [
                {
                    "year": row["year"],
                    "value": row["temperature_c"]
                }
                for row in annual
            ]
        },

        "data_quality": {
            "minimum_completeness_fraction": (
                MIN_COMPLETENESS
            ),
            "rainfall_requires_complete_period": True,
            "optional_parameter_status": optional_status
        },

        "limitations": [
            "NASA POWER values are gridded estimates.",
            "Historical observations are not forecasts.",
            "Incomplete rainfall periods are excluded.",
            "Non-rainfall averages require at least 90% daily coverage.",
            "Farm-level soil properties are not measured.",
            "Crop suitability requires independent agronomic evidence."
        ]
    }


def get_historical_climate(latitude, longitude):

    if not (
        -90 <= latitude <= 90
        and -180 <= longitude <= 180
    ):
        raise ValueError(
            "Invalid coordinates."
        )

    latitude = round(float(latitude), 4)
    longitude = round(float(longitude), 4)

    # Last complete calendar year.
    end_year = date.today().year - 1

    return _get_historical_climate(
        latitude,
        longitude,
        end_year
    )
