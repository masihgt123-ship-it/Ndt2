# -*- coding: utf-8 -*-
"""Numerical estimates only; not radiation-safety authorization."""

import math


# Inherited data: NOT independently verified.
# Check against source certificates and authoritative references.
ISOTOPES = {
    "Ir-192": {
        "gamma": 0.48,
        "hvl_pb": 4.8,
        "hvl_fe": 12.5,
        "half_life": 73.83,
        "name": "ایریدیوم ۱۹۲",
        "energy": "0.38 MeV",
    },
    "Se-75": {
        "gamma": 0.20,
        "hvl_pb": 2.0,
        "hvl_fe": 8.0,
        "half_life": 119.78,
        "name": "سلنیوم ۷۵",
        "energy": "0.32 MeV",
    },
    "Co-60": {
        "gamma": 1.32,
        "hvl_pb": 12.5,
        "hvl_fe": 21.0,
        "half_life": 1925.0,
        "name": "کبالت ۶۰",
        "energy": "1.25 MeV",
    },
    "Cs-137": {
        "gamma": 0.33,
        "hvl_pb": 6.5,
        "hvl_fe": 16.0,
        "half_life": 11000.0,
        "name": "سزیوم ۱۳۷",
        "energy": "0.66 MeV",
    },
}


_DIGITS = str.maketrans(
    "۰۱۲۳۴۵۶۷۸۹٠١٢٣٤٥٦٧٨٩٫",
    "01234567890123456789.",
)


def number(text, title, positive=False):
    """Accept English, Persian and Arabic digits."""
    try:
        value = float(
            str(text).strip().translate(_DIGITS)
        )
    except (ValueError, TypeError, OverflowError):
        raise ValueError(
            f"{title}: عدد معتبر وارد کنید"
        ) from None

    if not math.isfinite(value):
        raise ValueError(
            f"{title}: مقدار باید متناهی باشد"
        )

    if value < 0 or (positive and value == 0):
        requirement = (
            "بزرگ‌تر از صفر"
            if positive
            else "صفر یا مثبت"
        )

        raise ValueError(
            f"{title}: مقدار باید {requirement} باشد"
        )

    return value


def isotope(source):
    if source not in ISOTOPES:
        raise ValueError(
            "ایزوتوپ نامعتبر است"
        )

    return ISOTOPES[source]


def checked_result(value, positive=False):
    if (
        not math.isfinite(value)
        or value < 0
        or (positive and value == 0)
    ):
        raise ValueError(
            "نتیجه خارج از محدوده یا دقت عددی محاسبه است"
        )

    return value


def boundary_estimate(
    source,
    activity,
    dose_limit,
    lead_mm,
):
    """Point-source estimate with fixed lead HVL.

    Inputs:
        activity: Ci
        dose_limit: µSv/h
        lead_mm: mm of lead in the beam path

    Returns:
        Estimated distance in metres, transmission factor.

    Does not account for scattering, buildup, leakage
    or actual site geometry. Not a safety authorization.
    """
    iso = isotope(source)

    activity = number(
        activity,
        "اکتیویته",
    )

    dose_limit = number(
        dose_limit,
        "نرخ دوز هدف",
        positive=True,
    )

    lead_mm = number(
        lead_mm,
        "ضخامت سرب",
    )

    transmission = 2.0 ** (
        -lead_mm / iso["hvl_pb"]
    )

    if transmission == 0:
        raise ValueError(
            "تضعیف خارج از دقت عددی است؛ "
            "نتیجه قابل نمایش نیست"
        )

    # Approximate R/h -> µSv/h conversion
    # inherited from the original code.
    dose_1m = checked_result(
        iso["gamma"]
        * activity
        * 10000.0
        * transmission,
        positive=activity > 0,
    )

    distance = checked_result(
        math.sqrt(dose_1m / dose_limit),
        positive=activity > 0,
    )

    return distance, transmission


def decay(source, initial, days):
    """Return remaining activity in Ci and reduction percent."""
    data = isotope(source)

    initial = number(
        initial,
        "اکتیویته اولیه",
    )

    days = number(
        days,
        "روزهای سپری‌شده",
    )

    fraction = 2.0 ** (
        -days / data["half_life"]
    )

    activity = checked_result(
        initial * fraction,
        positive=initial > 0,
    )

    return (
        activity,
        100.0 * (1.0 - fraction),
    )
