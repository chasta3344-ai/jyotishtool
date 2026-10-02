from flask import Flask, request, jsonify
from flask_cors import CORS
import swisseph as swe
import datetime as dt
import pytz
import ephem
import math
import urllib.parse
import urllib.request
import json
import os
import calendar

app = Flask(__name__)
CORS(app)

# ============================================================
# CONFIG
# ============================================================
IST = pytz.timezone("Asia/Kolkata")
DEFAULT_CITY = "Ujjain"
DEFAULT_LAT = 23.1765
DEFAULT_LON = 75.7885

RASHI_NAMES = [
    "मेष", "वृषभ", "मिथुन", "कर्क", "सिंह", "कन्या",
    "तुला", "वृश्चिक", "धनु", "मकर", "कुंभ", "मीन"
]

NAKSHATRA_NAMES = [
    "अश्विनी", "भरणी", "कृत्तिका", "रोहिणी", "मृगशिरा", "आर्द्रा",
    "पुनर्वसु", "पुष्य", "आश्लेषा", "मघा", "पूर्वा फाल्गुनी",
    "उत्तरा फाल्गुनी", "हस्त", "चित्रा", "स्वाती", "विशाखा",
    "अनुराधा", "ज्येष्ठा", "मूल", "पूर्वाषाढ़ा", "उत्तराषाढ़ा",
    "श्रवण", "धनिष्ठा", "शतभिषा", "पूर्वा भाद्रपद",
    "उत्तरा भाद्रपद", "रेवती"
]

TITHI_NAMES = [
    "प्रतिपदा", "द्वितीया", "तृतीया", "चतुर्थी", "पंचमी", "षष्ठी",
    "सप्तमी", "अष्टमी", "नवमी", "दशमी", "एकादशी", "द्वादशी",
    "त्रयोदशी", "चतुर्दशी", "पूर्णिमा",
    "प्रतिपदा", "द्वितीया", "तृतीया", "चतुर्थी", "पंचमी", "षष्ठी",
    "सप्तमी", "अष्टमी", "नवमी", "दशमी", "एकादशी", "द्वादशी",
    "त्रयोदशी", "चतुर्दशी", "अमावस्या"
]

YOGA_NAMES = [
    "विष्कुम्भ", "प्रीति", "आयुष्मान", "सौभाग्य", "शोभन", "अतिगण्ड",
    "सुकर्मा", "धृति", "शूल", "गण्ड", "वृद्धि", "ध्रुव", "व्याघात",
    "हर्षण", "वज्र", "सिद्धि", "व्यतीपात", "वरीयान", "परिघ", "शिव",
    "सिद्ध", "साध्य", "शुभ", "शुक्ल", "ब्रह्म", "ऐन्द्र", "वैधृति"
]

KARANA_FIXED = {
    0: "किंस्तुघ्न",
    57: "शकुनि",
    58: "चतुष्पाद",
    59: "नाग"
}
KARANA_MOVING = ["बव", "बालव", "कौलव", "तैतिल", "गर", "वणिज", "विष्टि"]

WEEKDAYS = ["सोमवार", "मंगलवार", "बुधवार", "गुरुवार", "शुक्रवार", "शनिवार", "रविवार"]

HINDI_MONTHS = [
    "चैत्र", "वैशाख", "ज्येष्ठ", "आषाढ़", "श्रावण", "भाद्रपद",
    "आश्विन", "कार्तिक", "मार्गशीर्ष", "पौष", "माघ", "फाल्गुन"
]

PLANET_IDS = {
    "सूर्य": swe.SUN,
    "चंद्र": swe.MOON,
    "मंगल": swe.MARS,
    "बुध": swe.MERCURY,
    "गुरु": swe.JUPITER,
    "शुक्र": swe.VENUS,
    "शनि": swe.SATURN,
    "राहु": swe.MEAN_NODE,
}

DASHA_YEARS = {
    "केतु": 7.0,
    "शुक्र": 20.0,
    "सूर्य": 6.0,
    "चंद्र": 10.0,
    "मंगल": 7.0,
    "राहु": 18.0,
    "गुरु": 16.0,
    "शनि": 19.0,
    "बुध": 17.0,
}

DASHA_ORDER = ["केतु", "शुक्र", "सूर्य", "चंद्र", "मंगल", "राहु", "गुरु", "शनि", "बुध"]

NAKSHATRA_LORDS = [
    "केतु", "शुक्र", "सूर्य", "चंद्र", "मंगल", "राहु", "गुरु", "शनि", "बुध",
    "केतु", "शुक्र", "सूर्य", "चंद्र", "मंगल", "राहु", "गुरु", "शनि", "बुध",
    "केतु", "शुक्र", "सूर्य", "चंद्र", "मंगल", "राहु", "गुरु", "शनि", "बुध"
]

RASHI_LORDS = [
    "मंगल", "शुक्र", "बुध", "चंद्र", "सूर्य", "बुध",
    "शुक्र", "मंगल", "गुरु", "शनि", "शनि", "गुरु"
]

YONI = [
    "अश्व", "गज", "मेष", "सर्प", "सर्प", "श्वान", "मार्जार", "मेष", "मार्जार",
    "मूषक", "मूषक", "गौ", "महिष", "व्याघ्र", "महिष", "व्याघ्र", "मृग",
    "मृग", "श्वान", "वानर", "नकुल", "वानर", "अश्व", "गज", "अश्व",
    "सिंह", "गौ"
]

GANA = [
    "देव", "मनुष्य", "राक्षस", "मनुष्य", "देव", "मनुष्य", "देव", "देव", "राक्षस",
    "राक्षस", "मनुष्य", "मनुष्य", "देव", "राक्षस", "देव", "राक्षस", "देव",
    "राक्षस", "राक्षस", "मनुष्य", "मनुष्य", "देव", "राक्षस", "राक्षस", "मनुष्य",
    "मनुष्य", "देव"
]

NADI = [
    "आदि", "मध्य", "अन्त्य", "अन्त्य", "मध्य", "आदि", "आदि", "मध्य", "अन्त्य",
    "अन्त्य", "मध्य", "आदि", "आदि", "मध्य", "अन्त्य", "अन्त्य", "मध्य",
    "आदि", "आदि", "मध्य", "अन्त्य", "अन्त्य", "मध्य", "आदि", "आदि",
    "मध्य", "अन्त्य"
]

VARNA_BY_RASHI = {
    0: "क्षत्रिय", 1: "वैश्य", 2: "शूद्र", 3: "ब्राह्मण",
    4: "क्षत्रिय", 5: "वैश्य", 6: "शूद्र", 7: "ब्राह्मण",
    8: "क्षत्रिय", 9: "वैश्य", 10: "शूद्र", 11: "ब्राह्मण"
}

# ============================================================
# BASIC HELPERS
# ============================================================
def get_julian_day(local_dt):
    utc_dt = local_dt.astimezone(pytz.utc)
    return swe.julday(
        utc_dt.year, utc_dt.month, utc_dt.day,
        utc_dt.hour + utc_dt.minute / 60.0 + utc_dt.second / 3600.0
    )

def normalize(deg):
    return deg % 360.0

def parse_date_time(date_str, time_str):
    if not date_str:
        raise ValueError("Date is required")
    if not time_str:
        raise ValueError("Time is required")

    y, m, d = map(int, date_str.split("-"))
    parts = time_str.split(":")
    hh = int(parts[0])
    mm = int(parts[1]) if len(parts) > 1 else 0
    ss = int(parts[2]) if len(parts) > 2 else 0
    return IST.localize(dt.datetime(y, m, d, hh, mm, ss))

def parse_location(source):
    city = source.get("city") or DEFAULT_CITY
    try:
        lat = float(source.get("lat", DEFAULT_LAT))
        lon = float(source.get("lon", DEFAULT_LON))
    except (TypeError, ValueError):
        lat, lon = DEFAULT_LAT, DEFAULT_LON
    return city, lat, lon

def degree_text(lon):
    local = lon % 30.0
    deg = int(local)
    minute_float = (local - deg) * 60.0
    minute = int(minute_float)
    second = int(round((minute_float - minute) * 60))
    if second == 60:
        second = 0
        minute += 1
    if minute >= 60:
        minute = 0
        deg += 1
    return f"{deg}°{minute:02d}'{second:02d}\""

def nakshatra_info(lon):
    span = 360.0 / 27.0
    idx = min(26, int(normalize(lon) / span))
    within = normalize(lon) - idx * span
    pada = min(4, int(within / (span / 4.0)) + 1)
    return idx, NAKSHATRA_NAMES[idx], pada, NAKSHATRA_LORDS[idx]

def rashi_index(lon):
    return int(normalize(lon) / 30.0) % 12

def sidereal_position(jd, planet_id, with_speed=True):
    flags = swe.FLG_SIDEREAL
    if with_speed:
        flags |= swe.FLG_SPEED
    pos, _ = swe.calc_ut(jd, planet_id, flags)
    return normalize(pos[0]), pos[3]

def safe_date_text(value):
    return value.strftime("%d-%m-%Y")

# ============================================================
# PANCHANG HELPERS
# ============================================================
def karana_name(index):
    if index in KARANA_FIXED:
        return KARANA_FIXED[index]
    if 1 <= index <= 56:
        return KARANA_MOVING[(index - 1) % 7]
    return "--"

def find_sun_event(y, m, d, lat, lon, rising=True):
    observer = ephem.Observer()
    observer.lat = str(lat)
    observer.lon = str(lon)
    observer.date = IST.localize(dt.datetime(y, m, d, 0, 5)).astimezone(pytz.utc)

    sun = ephem.Sun()
    try:
        value = observer.next_rising(sun) if rising else observer.next_setting(sun)
        value_dt = value.datetime()
        if value_dt.tzinfo is None:
            value_dt = pytz.utc.localize(value_dt)
        return value_dt.astimezone(IST)
    except Exception:
        return None

def moon_event(y, m, d, lat, lon, rising=True):
    observer = ephem.Observer()
    observer.lat = str(lat)
    observer.lon = str(lon)
    observer.date = IST.localize(dt.datetime(y, m, d, 0, 5)).astimezone(pytz.utc)
    moon = ephem.Moon()
    try:
        value = observer.next_rising(moon) if rising else observer.next_setting(moon)
        value_dt = value.datetime()
        if value_dt.tzinfo is None:
            value_dt = pytz.utc.localize(value_dt)
        return value_dt.astimezone(IST)
    except Exception:
        return None

def event_time_text(value, base_date):
    if not value:
        return "--"
    suffix = "अगले दिन " if value.date() > base_date else ""
    return suffix + value.strftime("%I:%M %p")

def panchang_for_date(date_str, city, lat, lon):
    y, m, d = map(int, date_str.split("-"))
    local_dt = IST.localize(dt.datetime(y, m, d, 12, 0))
    jd = get_julian_day(local_dt)

    swe.set_sid_mode(swe.SIDM_LAHIRI)

    sun_lon, sun_speed = sidereal_position(jd, swe.SUN)
    moon_lon, moon_speed = sidereal_position(jd, swe.MOON)

    angle_diff = normalize(moon_lon - sun_lon)
    tithi_position = angle_diff / 12.0
    tithi_idx = min(29, int(tithi_position))
    paksha = "शुक्ल पक्ष" if tithi_idx < 15 else "कृष्ण पक्ष"

    rel_speed = moon_speed - sun_speed
    tithi_end = None
    if rel_speed > 0:
        degrees_left = ((tithi_idx + 1) * 12.0) - angle_diff
        end_jd = jd + degrees_left / rel_speed
        y2, m2, d2, h2 = swe.revjul(end_jd, swe.GREG_CAL)
        utc_end = pytz.utc.localize(
            dt.datetime(y2, m2, d2) + dt.timedelta(hours=h2)
        )
        tithi_end = utc_end.astimezone(IST)

    nak_idx, nak_name, nak_pada, nak_lord = nakshatra_info(moon_lon)
    yoga_idx = int(normalize(sun_lon + moon_lon) / (360.0 / 27.0))
    yoga_idx = min(26, yoga_idx)

    karana_position = angle_diff / 6.0
    karana_idx = int(karana_position)
    karan_1 = karana_name(karana_idx)
    karan_2 = karana_name((karana_idx + 1) % 60)

    sun_rashi_idx = rashi_index(sun_lon)
    moon_rashi_idx = rashi_index(moon_lon)

    vikram = y + 57
    shaka = y - 78
    kali = y + 3101

    sunrise_dt = find_sun_event(y, m, d, lat, lon, True)
    sunset_dt = find_sun_event(y, m, d, lat, lon, False)
    moonrise_dt = moon_event(y, m, d, lat, lon, True)
    moonset_dt = moon_event(y, m, d, lat, lon, False)

    ayan = "उत्तरायण" if sun_rashi_idx in [9, 10, 11, 0, 1, 2] else "दक्षिणायन"
    ritu_map = {
        11: "वसंत", 0: "वसंत", 1: "ग्रीष्म", 2: "ग्रीष्म",
        3: "वर्षा", 4: "वर्षा", 5: "शरद", 6: "शरद",
        7: "हेमंत", 8: "हेमंत", 9: "शिशिर", 10: "शिशिर"
    }

    ishta_kaal = "--"
    if sunrise_dt:
        noon_dt = IST.localize(dt.datetime(y, m, d, 12, 0))
        minutes = max(0, int((noon_dt - sunrise_dt).total_seconds() / 60))
        ghati = minutes // 24
        pala = int((minutes % 24) * 2.5)
        ishta_kaal = f"{ghati} घटी {pala} पल"

    return {
        "success": True,
        "data": {
            "location": {
                "city": city,
                "latitude": lat,
                "longitude": lon
            },
            "summary_header": f"{TITHI_NAMES[tithi_idx]}, {nak_name} नक्षत्र",
            "details": {
                "tithi": TITHI_NAMES[tithi_idx],
                "tithi_end_time": event_time_text(tithi_end, local_dt.date()),
                "paksha": paksha,
                "nakshatra": nak_name,
                "nakshatra_pada": nak_pada,
                "nakshatra_lord": nak_lord,
                "yog": YOGA_NAMES[yoga_idx],
                "karan_1": karan_1,
                "karan_2": karan_2,
                "var": WEEKDAYS[local_dt.weekday()],
                "chandra_rashi": RASHI_NAMES[moon_rashi_idx],
                "surya_rashi": RASHI_NAMES[sun_rashi_idx],
                "vikram_samvat": str(vikram),
                "shaka_samvat": str(shaka),
                "kali_samvat": str(kali),
                "ayan": ayan,
                "ritu": ritu_map.get(sun_rashi_idx, "--"),
                "maah_purnimant": HINDI_MONTHS[(sun_rashi_idx + 1) % 12],
                "ishta_kaal": ishta_kaal
            },
            "timings": {
                "sunrise": sunrise_dt.strftime("%I:%M %p") if sunrise_dt else "--",
                "sunset": sunset_dt.strftime("%I:%M %p") if sunset_dt else "--",
                "chandrodaya": moonrise_dt.strftime("%I:%M %p") if moonrise_dt else "--",
                "chandrast": moonset_dt.strftime("%I:%M %p") if moonset_dt else "--"
            }
        }
    }

# ============================================================
# KUNDALI HELPERS
# ============================================================
def planet_record(name, lon, speed, sun_lon):
    r_idx = rashi_index(lon)
    n_idx, n_name, n_pada, n_lord = nakshatra_info(lon)

    is_asta = False
    if name not in ["सूर्य", "चंद्र", "राहु", "केतु"]:
        diff = abs(lon - sun_lon)
        if diff > 180:
            diff = 360 - diff
        is_asta = diff <= 8.5

    return {
        "name": name,
        "longitude": round(lon, 6),
        "rashi": RASHI_NAMES[r_idx],
        "rashi_num": r_idx + 1,
        "degree": degree_text(lon),
        "nakshatra": n_name,
        "nakshatra_pada": n_pada,
        "nakshatra_lord": n_lord,
        "is_vakri": bool(speed < 0),
        "is_asta": bool(is_asta)
    }

def calculate_houses(jd, lat, lon):
    swe.set_sid_mode(swe.SIDM_LAHIRI)
    try:
        cusps, ascmc = swe.houses_ex(
            jd, lat, lon, b"P", swe.FLG_SIDEREAL
        )
        asc = normalize(ascmc[0])
        cusp_list = [normalize(cusps[i]) for i in range(12)]
        return asc, cusp_list
    except Exception:
        cusps, ascmc = swe.houses(jd, lat, lon, b"P")
        ayan = swe.get_ayanamsa_ut(jd)
        asc = normalize(ascmc[0] - ayan)
        cusp_list = [normalize(c - ayan) for c in cusps[:12]]
        return asc, cusp_list

def house_from_equal_whole_sign(lon, asc_lon):
    return ((rashi_index(lon) - rashi_index(asc_lon)) % 12) + 1

def manglik_status(mars_rashi, asc_rashi):
    house = ((mars_rashi - asc_rashi) % 12) + 1
    is_manglik = house in [1, 4, 7, 8, 12]
    return {
        "is_manglik": is_manglik,
        "status": "मांगलिक है" if is_manglik else "मांगलिक नहीं",
        "mars_house_from_lagna": house
    }

# ============================================================
# VIMSHOTTARI DASHA
# ============================================================
def add_years(base_date, years):
    days = years * 365.2425
    return base_date + dt.timedelta(days=days)

def dasha_sequence(start_lord):
    idx = DASHA_ORDER.index(start_lord)
    return DASHA_ORDER[idx:] + DASHA_ORDER[:idx]

def build_antardashas(maha_lord, maha_start, maha_end, now):
    total_maha_days = (maha_end - maha_start).total_seconds() / 86400.0
    result = []
    cursor = maha_start

    for lord in dasha_sequence(maha_lord):
        duration_days = total_maha_days * DASHA_YEARS[lord] / 120.0
        end = cursor + dt.timedelta(days=duration_days)
        result.append({
            "planet": lord,
            "start": cursor.strftime("%d-%m-%Y"),
            "end": end.strftime("%d-%m-%Y"),
            "current": cursor <= now < end
        })
        cursor = end

    return result

def calculate_vimshottari(dob_local, moon_lon):
    nak_idx, nak_name, pada, nak_lord = nakshatra_info(moon_lon)
    span = 360.0 / 27.0
    nak_start = nak_idx * span
    travelled = normalize(moon_lon) - nak_start
    fraction_completed = max(0.0, min(1.0, travelled / span))

    first_lord = nak_lord
    first_years_remaining = DASHA_YEARS[first_lord] * (1.0 - fraction_completed)

    birth_date = dob_local
    cursor = birth_date
    now = dt.datetime.now(IST)

    mahadashas = []
    first = True

    while len(mahadashas) < 18:
        lord = first_lord if first else DASHA_ORDER[
            (DASHA_ORDER.index(first_lord) + len(mahadashas)) % 9
        ]
        years = first_years_remaining if first else DASHA_YEARS[lord]
        end = add_years(cursor, years)

        mahadashas.append({
            "planet": lord,
            "start": cursor.strftime("%d-%m-%Y"),
            "end": end.strftime("%d-%m-%Y"),
            "years": round(years, 4),
            "current": cursor <= now < end,
            "antardasha": build_antardashas(lord, cursor, end, now)
        })

        cursor = end
        first = False

    current_maha = next((x for x in mahadashas if x["current"]), None)

    return {
        "nakshatra": nak_name,
        "nakshatra_pada": pada,
        "starting_mahadasha": first_lord,
        "current_mahadasha": current_maha["planet"] if current_maha else None,
        "mahadasha": mahadashas
    }

# ============================================================
# MUHURT SEARCH ENGINE
# ============================================================
MUHURT_TITHI_GOOD = {2, 3, 5, 7, 10, 11, 15}
MUHURT_TITHI_AVOID = {4, 9, 14, 30}
MUHURT_TITHI_SPECIAL = {1, 6, 8, 12, 13, 28}

CHOGHADIYA_DAY = {
    0: ["उद्वेग", "चर", "लाभ", "अमृत", "काल", "शुभ", "रोग", "उद्वेग"],
    1: ["अमृत", "काल", "शुभ", "रोग", "उद्वेग", "चर", "लाभ", "अमृत"],
    2: ["लाभ", "अमृत", "काल", "शुभ", "रोग", "उद्वेग", "चर", "लाभ"],
    3: ["शुभ", "रोग", "उद्वेग", "चर", "लाभ", "अमृत", "काल", "शुभ"],
    4: ["रोग", "उद्वेग", "चर", "लाभ", "अमृत", "काल", "शुभ", "रोग"],
    5: ["काल", "शुभ", "रोग", "उद्वेग", "चर", "लाभ", "अमृत", "काल"],
    6: ["उद्वेग", "चर", "लाभ", "अमृत", "काल", "शुभ", "रोग", "उद्वेग"],
}
CHOGADIYA_NIGHT = {
    wd: seq[4:] + seq[:4] for wd, seq in CHOGHADIYA_DAY.items()
}
CHOGADIYA_GOOD = {"शुभ", "लाभ", "अमृत", "चर"}

BUSINESS_TITHI_AVOID = {4, 9, 14, 30}
BUSINESS_VAR_AVOID = {1}
BUSINESS_MRDU = {"अनुराधा", "रेवती", "मृगशिरा"}
BUSINESS_KSHIPRA = {"अश्विनी", "हस्त", "पुष्य"}
BUSINESS_DHRUVA = {"रोहिणी", "उत्तराफाल्गुनी", "उत्तराषाढ़ा", "उत्तराभाद्रपदा"}
BUSINESS_YOGA_AVOID = {"व्यतीपात", "वैधृति", "गण्ड", "अतिगण्ड", "वज्र", "शूल", "परिघ"}
BUSINESS_KARANA_AVOID = {"विष्टि", "भद्रा"}
CHANDRA_BALA_GOOD = {1, 3, 6, 7, 10, 11}

def _business_tithi_rule(tithi_no, paksha):
    if tithi_no in BUSINESS_TITHI_AVOID:
        return "avoid", "रिक्ता तिथि/अमावस्या व्यवसायिक मुहूर्त में वर्ज्य है"
    return "good", "धर्मसिन्धु के विपणि-क्रय-विक्रय नियम में यह तिथि वर्जित नहीं है"

def _business_var_rule(weekday):
    if weekday in BUSINESS_VAR_AVOID:
        return "avoid", "मंगलवार व्यवसायिक मुहूर्त में वर्ज्य है"
    return "good", "मंगलवार को छोड़कर वार स्वीकार्य है"

def _business_nakshatra_rule(name):
    if name in BUSINESS_DHRUVA:
        return "good", "ध्रुव नक्षत्र — व्यवसाय/विपणि आरम्भ के लिए शुभ"
    if name in BUSINESS_KSHIPRA:
        return "good", "क्षिप्र नक्षत्र — व्यवसाय/विपणि आरम्भ के लिए शुभ"
    if name in BUSINESS_MRDU:
        return "good", "मृदु नक्षत्र — व्यवसाय/विपणि आरम्भ के लिए शुभ"
    return "avoid", "विपणि-क्रय-विक्रय के लिए मृदु, क्षिप्र या ध्रुव नक्षत्र अपेक्षित है"

def _business_yoga_rule(name):
    if name in BUSINESS_YOGA_AVOID:
        return "avoid", "यह अशुभ योग व्यवसायिक मुहूर्त में त्याज्य है"
    return "good", "त्याज्य योगों में नहीं है"

def _business_karana_rule(name):
    if name in BUSINESS_KARANA_AVOID:
        return "avoid", "विष्टि/भद्रा व्यवसायिक मुहूर्त में वर्ज्य है"
    return "good", "करण वर्जित नहीं है"

def _chandra_bala_rule(current_rashi, target_rashi):
    if target_rashi is None:
        return "not_checked", "जन्म राशि उपलब्ध नहीं है"
    distance = (current_rashi - target_rashi) % 12 + 1
    if distance in CHANDRA_BALA_GOOD:
        return "good", f"चन्द्रबल अनुकूल — जन्म राशि से {distance}वाँ स्थान"
    return "special", f"चन्द्रबल में विशेष विचार — जन्म राशि से {distance}वाँ स्थान"

YATRA_TITHI_AVOID = {1, 4, 6, 8, 9, 12, 14, 15, 30}
YATRA_TITHI_GOOD = {2, 3, 5, 7, 10, 11, 13}
YATRA_VAR_AVOID = {1, 5, 6}
YATRA_NAKSHATRA_GOOD = {
    "अश्विनी", "मृगशिरा", "पुनर्वसु", "पुष्य", "हस्त",
    "अनुराधा", "श्रवण", "धनिष्ठा", "रेवती"
}
YATRA_NAKSHATRA_AVOID = {
    "भरणी", "कृत्तिका", "आर्द्रा", "आश्लेषा", "मघा",
    "पूर्वा फाल्गुनी", "स्वाती", "विशाखा", "ज्येष्ठा",
    "पूर्वाषाढ़ा", "पूर्वा भाद्रपद"
}
YATRA_YOGA_AVOID = {"व्यतीपात", "वैधृति", "गण्ड", "अतिगण्ड", "वज्र", "शूल", "परिघ"}
YATRA_KARANA_AVOID = {"विष्टि", "भद्रा"}
YATRA_DISHA_SHOOL = {
    0: "पूर्व", 1: "उत्तर", 2: "उत्तर", 3: "उत्तर",
    4: "दक्षिण", 5: "पश्चिम", 6: "पश्चिम"
}
YATRA_DIRECTIONS = {
    "पूर्व", "पश्चिम", "उत्तर", "दक्षिण",
    "उत्तर-पूर्व", "उत्तर-पश्चिम", "दक्षिण-पूर्व", "दक्षिण-पश्चिम"
}

def _yatra_tithi_rule(tithi_no, paksha):
    if tithi_no in YATRA_TITHI_AVOID:
        return "avoid", "यह तिथि यात्रा आरम्भ के लिए वर्ज्य मानी जाती है"
    if tithi_no in YATRA_TITHI_GOOD:
        return "good", "यात्रा के लिए अनुकूल तिथि"
    return "special", "तिथि के लिए अन्य यात्रा-अंगों के साथ विशेष विचार"

def _yatra_var_rule(weekday):
    if weekday in YATRA_VAR_AVOID:
        return "avoid", "यह वार यात्रा आरम्भ के लिए सामान्यतः वर्ज्य है"
    return "good", "यात्रा के लिए वार स्वीकार्य है"

def _yatra_nakshatra_rule(name):
    if name in YATRA_NAKSHATRA_GOOD:
        return "good", "यात्रा के लिए शुभ/चल नक्षत्र"
    if name in YATRA_NAKSHATRA_AVOID:
        return "avoid", "यात्रा के लिए वर्ज्य नक्षत्र"
    if name in {"रोहिणी", "उत्तरा फाल्गुनी", "उत्तराषाढ़ा", "उत्तराभाद्रपद"}:
        return "special", "स्थिर नक्षत्र — यात्रा में मध्यम/विशेष विचार"
    return "special", "नक्षत्र के लिए विशेष विचार"

def _yatra_yoga_rule(name):
    if name in YATRA_YOGA_AVOID:
        return "avoid", "यह योग यात्रा आरम्भ में त्याज्य है"
    return "good", "त्याज्य यात्रा-योगों में नहीं है"

def _yatra_karana_rule(name):
    if name in YATRA_KARANA_AVOID:
        return "avoid", "विष्टि/भद्रा यात्रा में वर्ज्य है"
    return "good", "करण वर्जित नहीं है"

def _yatra_disha_rule(weekday, direction):
    if not direction:
        return "not_checked", "यात्रा की दिशा उपलब्ध नहीं है"
    direction = direction.strip()
    blocked = YATRA_DISHA_SHOOL[weekday]
    if direction == blocked:
        return "avoid", f"आज {blocked} दिशा में दिशाशूल है"
    return "good", f"आज का दिशाशूल {blocked} दिशा में है; चुनी दिशा सुरक्षित है"

def _yatra_nakshatra_shool_rule(nakshatra, direction):
    if not direction:
        return "not_checked", "यात्रा की दिशा उपलब्ध नहीं है"
    return "special", "नक्षत्र-शूल परंपरा अनुसार अलग तालिकाएँ हैं; दिशा जाँच के लिए विशेष विचार"

def _yatra_chandra_bala_rule(current_rashi, target_rashi):
    if target_rashi is None:
        return "not_checked", "जन्म राशि उपलब्ध नहीं है"
    distance = (current_rashi - target_rashi) % 12 + 1
    if distance in {3, 6, 10, 11}:
        return "good", f"चन्द्रबल यात्रा के लिए अनुकूल — जन्म राशि से {distance}वाँ स्थान"
    if distance == 8:
        return "avoid", "जन्म राशि से 8वाँ चन्द्रमा — चन्द्राष्टम"
    return "special", f"चन्द्रबल में विशेष विचार — जन्म राशि से {distance}वाँ स्थान"

def _yatra_tara_bala_rule(current_nakshatra, janma_nakshatra):
    if not janma_nakshatra or janma_nakshatra not in NAKSHATRA_NAMES:
        return "not_checked", "जन्म नक्षत्र उपलब्ध नहीं है"
    if current_nakshatra not in NAKSHATRA_NAMES:
        return "not_checked", "गोचर नक्षत्र उपलब्ध नहीं है"
    d = (NAKSHATRA_NAMES.index(current_nakshatra) - NAKSHATRA_NAMES.index(janma_nakshatra)) % 27 + 1
    tara = ((d - 1) % 9) + 1
    if tara in {1, 3, 5, 7}:
        return "avoid", f"ताराबल में {tara}वीं तारा — यात्रा के लिए अशुभ"
    return "good", f"ताराबल अनुकूल — {tara}वीं तारा"

VEHICLE_TITHI_GOOD = {2, 3, 5, 7, 10, 11, 13}
VEHICLE_TITHI_AVOID = {4, 9, 14, 30}
VEHICLE_TITHI_SPECIAL = {1, 6, 8, 12, 15, 28}

VEHICLE_VAR_GOOD = {0, 2, 3, 4}
VEHICLE_VAR_AVOID = {1}
VEHICLE_VAR_SPECIAL = {5, 6}

VEHICLE_NAKSHATRA_GOOD = {
    "पुनर्वसु", "स्वाती", "श्रवण", "धनिष्ठा", "शतभिषा"
}

VEHICLE_YOGA_AVOID = {
    "व्यतीपात", "वैधृति", "गण्ड", "अतिगण्ड",
    "वज्र", "शूल", "परिघ"
}

VEHICLE_KARANA_GOOD = {
    "बव", "बालव", "कौलव", "तैतिल", "गर", "वणिज"
}
VEHICLE_KARANA_AVOID = {"विष्टि", "भद्रा"}
VEHICLE_KARANA_SPECIAL = {"शकुनि", "चतुष्पाद", "नाग", "किंस्तुघ्न"}

def _vehicle_tithi_rule(tithi_no, paksha):
    if tithi_no in VEHICLE_TITHI_AVOID:
        return "avoid", "यह तिथि वाहन मुहूर्त में वर्ज्य है"
    if tithi_no in VEHICLE_TITHI_GOOD:
        return "good", "वाहन मुहूर्त के लिए अनुकूल तिथि"
    if tithi_no == 28 and paksha == "कृष्ण पक्ष":
        return "special", "कृष्ण त्रयोदशी के लिए अन्य अंगों की विशेष जाँच"
    return "special", "तिथि के लिए अन्य वाहन-मुहूर्त अंगों के साथ विचार"

def _vehicle_var_rule(weekday):
    if weekday in VEHICLE_VAR_AVOID:
        return "avoid", "मंगलवार वाहन मुहूर्त के लिए वर्ज्य रखा गया है"
    if weekday in VEHICLE_VAR_GOOD:
        return "good", "सोम/बुध/गुरु/शुक्र वाहन मुहूर्त के लिए शुभ"
    return "special", "शनिवार/रविवार को अन्य अंगों के साथ विशेष विचार"

def _vehicle_nakshatra_rule(name):
    if name in VEHICLE_NAKSHATRA_GOOD:
        return "good", "चर नक्षत्र वाहन के लिए विशेष रूप से अनुकूल"
    return "special", "नक्षत्र मुख्य वाहन सूची में नहीं है; अन्य अंगों के साथ विचार"

def _vehicle_yoga_rule(name):
    if name in VEHICLE_YOGA_AVOID:
        return "avoid", "यह योग वाहन मुहूर्त में त्याज्य दोष है"
    return "good", "त्याज्य योगों में नहीं है"

def _vehicle_karana_rule(name):
    if name in VEHICLE_KARANA_AVOID:
        return "avoid", "विष्टि/भद्रा वाहन मुहूर्त में वर्ज्य है"
    if name in VEHICLE_KARANA_GOOD:
        return "good", "चर करण वाहन मुहूर्त के लिए स्वीकार्य है"
    if name in VEHICLE_KARANA_SPECIAL:
        return "special", "स्थिर करण सामान्य वाहन मुहूर्त के लिए विशेष विचार योग्य है"
    return "special", "करण के लिए विशेष जाँच आवश्यक है"

def _durmuhurt_periods(local_date, sunrise, sunset):
    if not sunrise or not sunset or sunset <= sunrise:
        return []
    day_duration = (sunset - sunrise).total_seconds()
    part = day_duration / 15.0
    slots = {
        0: [8],
        1: [1, 7],
        2: [5],
        3: [4, 6],
        4: [2],
        5: [1, 2],
        6: [4],
    }.get(local_date.weekday(), [8])
    return [
        (sunrise + dt.timedelta(seconds=(slot - 1) * part),
         sunrise + dt.timedelta(seconds=slot * part))
        for slot in slots
    ]

def _three_month_end(start_date):
    month = start_date.month - 1 + 3
    year = start_date.year + month // 12
    month = month % 12 + 1
    day = min(start_date.day, calendar.monthrange(year, month)[1])
    return dt.date(year, month, day)

PANCHAK_START_LON = (23 * 30.0) + (20.0 / 60.0)
PANCHAK_END_LON = 360.0

PANCHAK_TYPES = {
    6: "रोग पंचक",
    0: "राज पंचक",
    1: "अग्नि पंचक",
    2: "दोषरहित पंचक",
    3: "दोषरहित पंचक",
    4: "चोर पंचक",
    5: "मृत्यु पंचक",
}

def _moon_crossing_ut(longitude, start_jd):
    return swe.mooncross_ut(
        longitude % 360.0,
        start_jd,
        swe.FLG_SWIEPH | swe.FLG_SIDEREAL
    )

def _jd_to_ist(jd):
    y, m, d, h = swe.revjul(jd, swe.GREG_CAL)
    utc_value = pytz.utc.localize(
        dt.datetime(y, m, d) + dt.timedelta(hours=h)
    )
    return utc_value.astimezone(IST)

def _previous_moon_crossing(longitude, reference_jd):
    search_jd = reference_jd - 35.0
    last = None

    for _ in range(4):
        crossing = _moon_crossing_ut(longitude, search_jd)
        if crossing >= reference_jd:
            break
        last = crossing
        search_jd = crossing + (1.0 / 864000.0)

    return last

def _next_moon_crossing(longitude, reference_jd):
    return _moon_crossing_ut(
        longitude,
        reference_jd + (1.0 / 864000.0)
    )

def _panchak_window_for_date(date_obj):
    start_of_day = IST.localize(dt.datetime.combine(date_obj, dt.time(0, 0)))
    end_of_day = start_of_day + dt.timedelta(days=1)
    start_jd = get_julian_day(start_of_day)
    end_jd = get_julian_day(end_of_day)

    p_start = _previous_moon_crossing(PANCHAK_START_LON, end_jd)
    if p_start is None:
        return None

    p_end = _next_moon_crossing(PANCHAK_END_LON, p_start)
    if p_end is None:
        return None

    if p_end <= start_jd or p_start >= end_jd:
        next_start = _next_moon_crossing(PANCHAK_START_LON, start_jd - (1.0 / 864000.0))
        if next_start >= end_jd:
            return None
        next_end = _next_moon_crossing(PANCHAK_END_LON, next_start)
        if next_end <= start_jd:
            return None
        p_start, p_end = next_start, next_end

    start_dt = _jd_to_ist(p_start)
    end_dt = _jd_to_ist(p_end)
    p_type = PANCHAK_TYPES[start_dt.weekday()]

    return {
        "active": True,
        "type": p_type,
        "start": start_dt,
        "end": end_dt,
        "start_display": start_dt.strftime("%d-%m-%Y %I:%M %p"),
        "end_display": end_dt.strftime("%d-%m-%Y %I:%M %p"),
    }

def _panchak_status_for_date(date_obj):
    try:
        window = _panchak_window_for_date(date_obj)
    except Exception:
        window = None

    if not window:
        return {
            "name": "पंचक",
            "value": "नहीं",
            "status": "good",
            "reason": "पंचक अवधि सक्रिय नहीं है",
            "active": False,
            "type": None,
            "start": None,
            "end": None,
        }

    return {
        "name": "पंचक",
        "value": f"हाँ — {window['type']}",
        "status": "special",
        "reason": "पंचक अवधि सक्रिय है",
        "active": True,
        "type": window["type"],
        "start": window["start_display"],
        "end": window["end_display"],
    }

def _tithi_number(panchang):
    name = panchang["details"].get("tithi", "")
    paksha = panchang["details"].get("paksha", "")
    try:
        idx = TITHI_NAMES.index(name)
    except ValueError:
        return None
    if paksha == "कृष्ण पक्ष" and name == "अमावस्या":
        return 30
    if paksha == "शुक्ल पक्ष":
        return idx + 1
    return idx + 1 if idx >= 15 else idx + 16

def _tithi_rule(tithi_no, paksha):
    if tithi_no in MUHURT_TITHI_AVOID:
        return "avoid", "तिथि सामान्य मुहूर्त के लिए वर्जित है"
    if tithi_no == 15:
        return "good", "पूर्णिमा सामान्यतः स्वीकार्य है"
    if tithi_no == 13 and paksha == "शुक्ल पक्ष":
        return "good", "शुक्ल त्रयोदशी स्वीकार्य है"
    if tithi_no in MUHURT_TITHI_GOOD:
        return "good", "तिथि सामान्य मुहूर्त के लिए अनुकूल है"
    if tithi_no in MUHURT_TITHI_SPECIAL:
        return "special", "इस तिथि के लिए विशेष जाँच आवश्यक है"
    return "special", "तिथि के लिए विशेष जाँच आवश्यक है"

def _moon_position_rule(current_rashi, target_rashi):
    if target_rashi is None:
        return "not_checked", "लक्षित चंद्र राशि उपलब्ध नहीं है"
    distance = (current_rashi - target_rashi) % 12 + 1
    if distance in (4, 8, 12):
        return "avoid", f"चंद्रमा लक्षित राशि से {distance}वें स्थान में है"
    return "good", f"चंद्रमा लक्षित राशि से {distance}वें स्थान में है"

def _time_from_text(text_value, base_date):
    if not text_value or text_value == "--":
        return None
    value = text_value.replace("अगले दिन ", "")
    try:
        return dt.datetime.strptime(value, "%I:%M %p").time()
    except ValueError:
        return None

def _period_between(start, end, total_parts=8):
    if not start or not end or end <= start:
        return []
    seconds = (end - start).total_seconds() / total_parts
    return [(start + dt.timedelta(seconds=seconds*i),
             start + dt.timedelta(seconds=seconds*(i+1)))
            for i in range(total_parts)]

def _kaal_periods(local_date, sunrise, sunset):
    if not sunrise or not sunset or sunset <= sunrise:
        return {}
    parts = _period_between(sunrise, sunset, 8)
    rahu_slot = {0: 2, 1: 7, 2: 5, 3: 6, 4: 4, 5: 3, 6: 1}[local_date.weekday()]
    yama_slot = {0: 5, 1: 4, 2: 3, 3: 2, 4: 1, 5: 0, 6: 6}[local_date.weekday()]
    gulika_slot = {0: 6, 1: 5, 2: 4, 3: 3, 4: 2, 5: 1, 6: 0}[local_date.weekday()]
    return {
        "राहु काल": parts[rahu_slot],
        "यमगंड": parts[yama_slot],
        "गुलिक काल": parts[gulika_slot],
    }

def _choghadiya_intervals(local_date, sunrise, sunset):
    result = []
    if not sunrise or not sunset or sunset <= sunrise:
        return result
    day_parts = _period_between(sunrise, sunset, 8)
    day_names = CHOGHADIYA_DAY[local_date.weekday()]
    for i, (a, b) in enumerate(day_parts):
        result.append({"name": day_names[i], "start": a, "end": b, "period": "day"})
    next_sunrise = sunrise + dt.timedelta(days=1)
    night_parts = _period_between(sunset, next_sunrise, 8)
    night_names = CHOGADIYA_NIGHT[local_date.weekday()]
    for i, (a, b) in enumerate(night_parts):
        result.append({"name": night_names[i], "start": a, "end": b, "period": "night"})
    return result

def _in_interval(value, interval):
    return bool(interval and interval[0] <= value < interval[1])

def _format_range(start, end):
    return f"{start.strftime('%I:%M %p')} – {end.strftime('%I:%M %p')}"

def _julian_end_datetime(end_jd):
    y2, m2, d2, h2 = swe.revjul(end_jd, swe.GREG_CAL)
    base = dt.datetime(y2, m2, d2)
    utc_value = pytz.utc.localize(base + dt.timedelta(hours=h2))
    return utc_value.astimezone(IST)

def _abhijit_period(sunrise_dt, sunset_dt):
    if not sunrise_dt or not sunset_dt or sunset_dt <= sunrise_dt:
        return None
    part = (sunset_dt - sunrise_dt) / 15
    start = sunrise_dt + part * 7
    end = sunrise_dt + part * 8
    return (start, end)

def _muhurt_full_panchang(date_obj, p, choghadiya, kaal, durmuhurt):
    details = p["details"]
    timings = p["timings"]

    sunrise = _time_from_text(timings.get("sunrise"), date_obj)
    sunset = _time_from_text(timings.get("sunset"), date_obj)
    sunrise_dt = IST.localize(dt.datetime.combine(date_obj, sunrise)) if sunrise else None
    sunset_dt = IST.localize(dt.datetime.combine(date_obj, sunset)) if sunset else None

    abhijit = _abhijit_period(sunrise_dt, sunset_dt)

    def period_rows(items):
        return [
            {
                "name": item["name"],
                "period": item["period"],
                "time": _format_range(item["start"], item["end"])
            }
            for item in items
        ]

    kaal_rows = {
        name: _format_range(a, b)
        for name, (a, b) in kaal.items()
    }

    durmuhurt_rows = [
        _format_range(a, b) for a, b in durmuhurt
    ]

    y, m, d = map(int, date_obj.strftime("%Y-%m-%d").split("-"))
    noon_dt = IST.localize(dt.datetime(y, m, d, 12, 0))
    jd = get_julian_day(noon_dt)
    swe.set_sid_mode(swe.SIDM_LAHIRI)
    sun_lon, sun_speed = sidereal_position(jd, swe.SUN)
    moon_lon, moon_speed = sidereal_position(jd, swe.MOON)
    angle_diff = normalize(moon_lon - sun_lon)

    def next_boundary_end(position, span, speed):
        if speed <= 0:
            return None
        index = int(normalize(position) / span)
        boundary = (index + 1) * span
        left = boundary - normalize(position)
        if left <= 0:
            left += span
        return _julian_end_datetime(jd + left / speed)

    nak_end = next_boundary_end(moon_lon, 360.0 / 27.0, moon_speed)
    yoga_speed = moon_speed + sun_speed
    yoga_end = next_boundary_end(normalize(sun_lon + moon_lon), 360.0 / 27.0, yoga_speed)
    karana_end = next_boundary_end(angle_diff, 6.0, moon_speed - sun_speed)

    panchang_details = dict(details)
    panchang_details["nakshatra_end_time"] = event_time_text(nak_end, date_obj)
    panchang_details["yog_end_time"] = event_time_text(yoga_end, date_obj)
    panchang_details["karan_1_end_time"] = event_time_text(karana_end, date_obj)

    return {
        "date": date_obj.strftime("%Y-%m-%d"),
        "date_display": date_obj.strftime("%d-%m-%Y"),
        "weekday": details.get("var", "--"),
        "details": panchang_details,
        "timings": dict(timings),
        "muhurt_timings": {
            "abhijit": _format_range(*abhijit) if abhijit else "--",
            "rahu_kal": kaal_rows.get("राहु काल", "--"),
            "yamaganda": kaal_rows.get("यमगंड", "--"),
            "gulik_kal": kaal_rows.get("गुलिक काल", "--"),
            "durmuhurt": durmuhurt_rows,
            "choghadiya": period_rows(choghadiya)
        }
    }

def _candidate_windows(local_date, sunrise, sunset, choghadiya, blocked):
    """Create candidate windows.
    Prioritizes Day Choghadiya first; if no good day slots are found,
    it falls back to Night Choghadiya.
    """
    day_candidates = []
    night_candidates = []

    for item in choghadiya:
        if item["name"] not in CHOGADIYA_GOOD:
            continue
        start, end = item["start"], item["end"]
        cuts = [start, end]
        for bs, be in blocked:
            if be > start and bs < end:
                if start < bs < end:
                    cuts.append(bs)
                if start < be < end:
                    cuts.append(be)
        cuts = sorted(set(cuts))
        for a, b in zip(cuts, cuts[1:]):
            if (b - a).total_seconds() >= 20 * 60:
                if not any(_in_interval(a, x) or _in_interval(b - dt.timedelta(seconds=1), x)
                           for x in blocked):
                    window = {
                        "start": a, "end": b,
                        "choghadiya": item["name"]
                    }
                    if item.get("period") == "night":
                        night_candidates.append(window)
                    else:
                        day_candidates.append(window)

    day_candidates.sort(key=lambda x: (-((x["end"] - x["start"]).total_seconds()), x["start"]))
    night_candidates.sort(key=lambda x: (-((x["end"] - x["start"]).total_seconds()), x["start"]))

    chosen_pool = day_candidates if day_candidates else night_candidates
    chosen = chosen_pool[:3]
    chosen.sort(key=lambda x: x["start"])
    return chosen

def muhurt_day_record(date_obj, city, lat, lon, target_rashi_idx=None, muhurt_type="general", direction=None, janma_nakshatra=None):
    date_str = date_obj.strftime("%Y-%m-%d")
    p = panchang_for_date(date_str, city, lat, lon)["data"]
    details = p["details"]
    timings = p["timings"]

    moon_idx = RASHI_NAMES.index(details["chandra_rashi"])
    moon_status, moon_reason = _moon_position_rule(moon_idx, target_rashi_idx)

    tithi_no = _tithi_number(p)
    if muhurt_type == "vehicle":
        tithi_status, tithi_reason = _vehicle_tithi_rule(tithi_no, details["paksha"])
    elif muhurt_type == "business":
        tithi_status, tithi_reason = _business_tithi_rule(tithi_no, details["paksha"])
    elif muhurt_type == "yatra":
        tithi_status, tithi_reason = _yatra_tithi_rule(tithi_no, details["paksha"])
    else:
        tithi_status, tithi_reason = _tithi_rule(tithi_no, details["paksha"])

    factors = {
        "chandra_rashi": {
            "name": "चंद्र राशि", "value": details["chandra_rashi"],
            "status": moon_status, "reason": moon_reason
        },
        "tithi": {
            "name": "तिथि", "value": f"{details['paksha']} {details['tithi']}",
            "status": tithi_status, "reason": tithi_reason
        },
        "var": {
            "name": "वार", "value": details["var"],
            "status": (_vehicle_var_rule(date_obj.weekday())[0] if muhurt_type == "vehicle" else _business_var_rule(date_obj.weekday())[0] if muhurt_type == "business" else _yatra_var_rule(date_obj.weekday())[0] if muhurt_type == "yatra" else "good"),
            "reason": (_vehicle_var_rule(date_obj.weekday())[1] if muhurt_type == "vehicle" else _business_var_rule(date_obj.weekday())[1] if muhurt_type == "business" else _yatra_var_rule(date_obj.weekday())[1] if muhurt_type == "yatra" else "वार की सामान्य गणना उपलब्ध है")
        },
        "nakshatra": {
            "name": "नक्षत्र", "value": details["nakshatra"],
            "status": (_vehicle_nakshatra_rule(details["nakshatra"])[0] if muhurt_type == "vehicle" else _business_nakshatra_rule(details["nakshatra"])[0] if muhurt_type == "business" else _yatra_nakshatra_rule(details["nakshatra"])[0] if muhurt_type == "yatra" else "good"),
            "reason": (_vehicle_nakshatra_rule(details["nakshatra"])[1] if muhurt_type == "vehicle" else _business_nakshatra_rule(details["nakshatra"])[1] if muhurt_type == "business" else _yatra_nakshatra_rule(details["nakshatra"])[1] if muhurt_type == "yatra" else "नक्षत्र की गणना उपलब्ध है")
        },
        "yoga": {
            "name": "योग", "value": details["yog"],
            "status": (_vehicle_yoga_rule(details["yog"])[0] if muhurt_type == "vehicle" else _business_yoga_rule(details["yog"])[0] if muhurt_type == "business" else _yatra_yoga_rule(details["yog"])[0] if muhurt_type == "yatra" else "good"),
            "reason": (_vehicle_yoga_rule(details["yog"])[1] if muhurt_type == "vehicle" else _business_yoga_rule(details["yog"])[1] if muhurt_type == "business" else _yatra_yoga_rule(details["yog"])[1] if muhurt_type == "yatra" else "योग की गणना उपलब्ध है")
        },
        "karana": {
            "name": "करण", "value": details["karan_1"],
            "status": (_vehicle_karana_rule(details["karan_1"])[0] if muhurt_type == "vehicle" else _business_karana_rule(details["karan_1"])[0] if muhurt_type == "business" else _yatra_karana_rule(details["karan_1"])[0] if muhurt_type == "yatra" else ("good" if details["karan_1"] != "विष्टि" else "avoid")),
            "reason": (_vehicle_karana_rule(details["karan_1"])[1] if muhurt_type == "vehicle" else _business_karana_rule(details["karan_1"])[1] if muhurt_type == "business" else _yatra_karana_rule(details["karan_1"])[1] if muhurt_type == "yatra" else "विष्टि/भद्रा होने पर सामान्य मुहूर्त में वर्जित")
        }
    }

    if muhurt_type == "business":
        cb_status, cb_reason = _chandra_bala_rule(moon_idx, target_rashi_idx)
        factors["chandra_bala"] = {"name": "चन्द्रबल", "value": cb_reason, "status": cb_status, "reason": cb_reason}

    if muhurt_type == "yatra":
        cb_status, cb_reason = _yatra_chandra_bala_rule(moon_idx, target_rashi_idx)
        factors["chandra_bala"] = {"name": "चन्द्रबल", "value": cb_reason, "status": cb_status, "reason": cb_reason}
        ds_status, ds_reason = _yatra_disha_rule(date_obj.weekday(), direction)
        factors["disha_shool"] = {"name": "दिशाशूल", "value": YATRA_DISHA_SHOOL[date_obj.weekday()], "status": ds_status, "reason": ds_reason}
        ns_status, ns_reason = _yatra_nakshatra_shool_rule(details["nakshatra"], direction)
        factors["nakshatra_shool"] = {"name": "नक्षत्र शूल", "value": direction or "दिशा नहीं दी गई", "status": ns_status, "reason": ns_reason}
        tb_status, tb_reason = _yatra_tara_bala_rule(details["nakshatra"], janma_nakshatra)
        factors["tara_bala"] = {"name": "ताराबल", "value": janma_nakshatra or "जन्म नक्षत्र नहीं दिया", "status": tb_status, "reason": tb_reason}
        factors["yogini_shool"] = {"name": "योगिनी शूल", "value": "विशेष गणना", "status": "special", "reason": "योगिनी चक्र परंपरा अनुसार दिशा-आधारित जाँच"}

    sunrise = _time_from_text(timings.get("sunrise"), date_obj)
    sunset = _time_from_text(timings.get("sunset"), date_obj)
    sunrise_dt = IST.localize(dt.datetime.combine(date_obj, sunrise)) if sunrise else None
    sunset_dt = IST.localize(dt.datetime.combine(date_obj, sunset)) if sunset else None
    kaal = _kaal_periods(date_obj, sunrise_dt, sunset_dt)

    for key, label in [("राहु काल", "rahu_kal"), ("यमगंड", "yamaganda"), ("गुलिक काल", "gulika")]:
        factors[label] = {
            "name": key,
            "value": "लागू" if key in kaal else "उपलब्ध नहीं",
            "status": "good" if key in kaal else "special",
            "reason": "यह समय मुहूर्त विंडो में शामिल नहीं किया जाएगा" if key in kaal else "समय उपलब्ध नहीं"
        }

    factors["panchak"] = _panchak_status_for_date(date_obj)

    choghadiya = _choghadiya_intervals(date_obj, sunrise_dt, sunset_dt)
    durmuhurt = _durmuhurt_periods(date_obj, sunrise_dt, sunset_dt)
    full_panchang = _muhurt_full_panchang(date_obj, p, choghadiya, kaal, durmuhurt)

    factors["choghadiya"] = {
        "name": "चौघड़िया",
        "value": ", ".join(sorted({x["name"] for x in choghadiya if x["name"] in CHOGADIYA_GOOD})) or "उपलब्ध नहीं",
        "status": "good" if any(x["name"] in CHOGADIYA_GOOD for x in choghadiya) else "avoid",
        "reason": "अमृत, शुभ, लाभ और चर से वास्तविक समय चुना जाएगा"
    }

    if muhurt_type in ("vehicle", "business", "yatra"):
        factors["durmuhurt"] = {
            "name": "दुर्मुहूर्त",
            "value": ", ".join(_format_range(a, b) for a, b in durmuhurt) or "उपलब्ध नहीं",
            "status": "good",
            "reason": "इन समय-खंडों को candidate time से हटाया जाएगा"
        }
        blocked = list(kaal.values()) + durmuhurt
    else:
        blocked = list(kaal.values())

    hard_fail = any(f["status"] == "avoid" for f in factors.values())
    windows = [] if moon_status == "avoid" else _candidate_windows(date_obj, sunrise_dt, sunset_dt, choghadiya, blocked)

    complete = (not hard_fail and bool(windows))

    return {
        "date": date_str,
        "date_display": date_obj.strftime("%d-%m-%Y"),
        "factors": factors,
        "complete_match": complete,
        "time_frames": [
            {
                "time": _format_range(x["start"], x["end"]),
                "choghadiya": x["choghadiya"]
            } for x in windows
        ],
        "panchang": p,
        "full_panchang": full_panchang,
        "reasons": [
            f["reason"] for f in factors.values() if f["status"] in ("avoid", "special")
        ]
    }

def muhurt_search(start_date, city, lat, lon, target_rashi_idx=None, limit=5, muhurt_type="general", direction=None, janma_nakshatra=None):
    end_date = _three_month_end(start_date)
    all_records = []
    cursor = start_date
    
    while cursor <= end_date:
        record = muhurt_day_record(cursor, city, lat, lon, target_rashi_idx, muhurt_type, direction, janma_nakshatra)
        
        avoid_count = sum(1 for f in record.get("factors", {}).values() if isinstance(f, dict) and f.get("status") == "avoid")
        special_count = sum(1 for f in record.get("factors", {}).values() if isinstance(f, dict) and f.get("status") == "special")
        
        record["_score"] = (
            0 if record["complete_match"] else 1,
            avoid_count,
            special_count,
            cursor
        )
        all_records.append(record)
        cursor += dt.timedelta(days=1)

    all_records.sort(key=lambda x: x["_score"])

    results = all_records[:limit]
    complete_count = sum(1 for r in all_records if r["complete_match"])

    return {
        "success": True,
        "search": {
            "muhurt_type": muhurt_type,
            "start_date": start_date.strftime("%Y-%m-%d"),
            "end_date": end_date.strftime("%Y-%m-%d"),
            "location": {"city": city, "latitude": lat, "longitude": lon},
            "target_chandra_rashi": RASHI_NAMES[target_rashi_idx] if target_rashi_idx is not None else None,
            "yatra_direction": direction if muhurt_type == "yatra" else None,
            "janma_nakshatra": janma_nakshatra if muhurt_type == "yatra" else None,
            "max_results": limit,
            "complete_results_found": complete_count,
            "partial_results_included": len(results) > complete_count
        },
        "results": results
    }

# ============================================================
# LOCATION SEARCH
# ============================================================
def location_search(query):
    query = (query or "").strip()
    if not query:
        return []

    params = urllib.parse.urlencode({
        "q": query,
        "format": "jsonv2",
        "addressdetails": 1,
        "limit": 8,
        "countrycodes": "in"
    })
    url = "https://nominatim.openstreetmap.org/search?" + params
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "HindiPanchang-Kundali/1.0"}
    )

    with urllib.request.urlopen(req, timeout=10) as response:
        raw = response.read().decode("utf-8")
        items = json.loads(raw)

    result = []
    for item in items:
        address = item.get("address", {})
        result.append({
            "display_name": item.get("display_name", ""),
            "city": (
                address.get("city")
                or address.get("town")
                or address.get("village")
                or address.get("municipality")
                or address.get("county")
                or ""
            ),
            "district": address.get("state_district", ""),
            "state": address.get("state", ""),
            "pincode": address.get("postcode", ""),
            "country": address.get("country", ""),
            "latitude": float(item["lat"]),
            "longitude": float(item["lon"])
        })
    return result

# ============================================================
# ROUTES
# ============================================================
@app.get("/")
def home():
    return jsonify({
        "success": True,
        "service": "Hindi Panchang & Kundali API",
        "status": "online",
        "version": "2.0",
        "endpoints": [
            "/health",
            "/api/full-panchang-hindi?date=YYYY-MM-DD&city=Ujjain&lat=23.1765&lon=75.7885",
            "/api/generate-kundali?date=YYYY-MM-DD&time=HH:MM&city=Ujjain&lat=23.1765&lon=75.7885",
            "/api/location?q=Ujjain",
            "/api/dasha?date=YYYY-MM-DD&time=HH:MM&lat=23.1765&lon=75.7885",
            "/api/muhurt-search?date=YYYY-MM-DD&city=Ujjain&lat=23.1765&lon=75.7885&rashi=मेष",
            "/api/muhurt-search?date=YYYY-MM-DD&city=Ujjain&lat=23.1765&lon=75.7885&rashi=मेष&muhurt_type=vehicle",
            "/api/muhurt-search?date=YYYY-MM-DD&city=Ujjain&lat=23.1765&lon=75.7885&rashi=मेष&muhurt_type=business"
        ]
    })

@app.get("/health")
def health():
    return jsonify({"success": True, "status": "healthy"})

@app.get("/api/full-panchang-hindi")
@app.get("/api/full-panchang-hindi-fix")
def get_panchang():
    try:
        date_str = request.args.get("date")
        city, lat, lon = parse_location(request.args)
        if not date_str:
            return jsonify({"success": False, "error": "Date is required"}), 400
        return jsonify(panchang_for_date(date_str, city, lat, lon))
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/api/generate-kundali", methods=["GET", "POST"])
def generate_kundali():
    try:
        if request.method == "POST":
            data = request.get_json(silent=True) or {}
        else:
            data = request.args

        date_str = data.get("dob") or data.get("date")
        time_str = data.get("time")
        name = data.get("name", "")
        city, lat, lon = parse_location(data)

        birth_dt = parse_date_time(date_str, time_str)
        jd = get_julian_day(birth_dt)
        swe.set_sid_mode(swe.SIDM_LAHIRI)

        sun_lon, _ = sidereal_position(jd, swe.SUN)
        moon_lon, moon_speed = sidereal_position(jd, swe.MOON)

        planet_data = {}
        for name_key, p_id in PLANET_IDS.items():
            lon_value, speed = sidereal_position(jd, p_id)
            planet_data[name_key] = planet_record(
                name_key, lon_value, speed, sun_lon
            )

        ketu_lon = normalize(planet_data["राहु"]["longitude"] + 180.0)
        planet_data["केतु"] = planet_record(
            "केतु", ketu_lon, -1.0, sun_lon
        )

        asc_lon, cusp_list = calculate_houses(jd, lat, lon)
        asc_rashi = rashi_index(asc_lon)

        houses = []
        for house_num in range(1, 13):
            sign_idx = (asc_rashi + house_num - 1) % 12
            houses.append({
                "house": house_num,
                "rashi": RASHI_NAMES[sign_idx],
                "rashi_num": sign_idx + 1,
                "planets": []
            })

        for p_name, p in planet_data.items():
            h = house_from_equal_whole_sign(p["longitude"], asc_lon)
            houses[h - 1]["planets"].append({
                "name": p_name,
                "vakri": p["is_vakri"],
                "asta": p["is_asta"]
            })
            p["house"] = h

        nak_idx, nak_name, nak_pada, nak_lord = nakshatra_info(moon_lon)
        moon_rashi = rashi_index(moon_lon)

        panchang = panchang_for_date(date_str, city, lat, lon)["data"]

        mars_rashi = rashi_index(planet_data["मंगल"]["longitude"])
        manglik = manglik_status(mars_rashi, asc_rashi)

        birth_details = {
            "name": name,
            "date": date_str,
            "time": time_str,
            "city": city,
            "latitude": lat,
            "longitude": lon
        }

        dasha = calculate_vimshottari(birth_dt, moon_lon)

        paya_map = {0: "स्वर्ण", 1: "रजत", 2: "ताम्र", 3: "लोह"}
        paya = paya_map.get(moon_rashi % 4, "रजत")

        return jsonify({
            "success": True,
            "birth_details": birth_details,
            "lagna": {
                "rashi": RASHI_NAMES[asc_rashi],
                "rashi_num": asc_rashi + 1,
                "degree": degree_text(asc_lon),
                "longitude": round(asc_lon, 6)
            },
            "basic": {
                "rashi": RASHI_NAMES[moon_rashi],
                "rashi_lord": RASHI_LORDS[moon_rashi],
                "janma_nakshatra": nak_name,
                "nakshatra_pada": nak_pada,
                "nakshatra_lord": nak_lord,
                "paya": paya,
                "yoni": YONI[nak_idx],
                "gana": GANA[nak_idx],
                "nadi": NADI[nak_idx],
                "varna": VARNA_BY_RASHI[moon_rashi],
                "manglik": manglik
            },
            "panchang": panchang,
            "planets": planet_data,
            "houses": houses,
            "chart": {
                "type": "north_indian",
                "style": "whole_sign",
                "ascendant_house": 1,
                "houses": houses
            },
            "dasha": dasha
        })

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.get("/api/dasha")
def dasha_api():
    try:
        date_str = request.args.get("date") or request.args.get("dob")
        time_str = request.args.get("time")
        _, lat, lon = parse_location(request.args)

        birth_dt = parse_date_time(date_str, time_str)
        jd = get_julian_day(birth_dt)
        moon_lon, _ = sidereal_position(jd, swe.MOON)

        return jsonify({
            "success": True,
            "data": calculate_vimshottari(birth_dt, moon_lon)
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.get("/api/muhurt-search")
def muhurt_search_api():
    try:
        today = dt.datetime.now(IST).date()
        date_str = request.args.get("date")
        if date_str:
            start_date = dt.datetime.strptime(date_str, "%Y-%m-%d").date()
        else:
            start_date = today
        city, lat, lon = parse_location(request.args)

        rashi_value = request.args.get("rashi") or request.args.get("chandra_rashi")
        target_idx = None
        if rashi_value:
            if rashi_value.isdigit():
                n = int(rashi_value)
                if 1 <= n <= 12:
                    target_idx = n - 1
            elif rashi_value in RASHI_NAMES:
                target_idx = RASHI_NAMES.index(rashi_value)
            else:
                return jsonify({"success": False, "error": "Invalid Rashi"}), 400

        limit = min(5, max(1, int(request.args.get("limit", 5))))
        direction = (request.args.get("direction") or request.args.get("yatra_direction") or "").strip() or None
        janma_nakshatra = (request.args.get("janma_nakshatra") or request.args.get("birth_nakshatra") or "").strip() or None
        if janma_nakshatra and janma_nakshatra not in NAKSHATRA_NAMES:
            return jsonify({"success": False, "error": "Invalid Janma Nakshatra"}), 400
        muhurt_type = (request.args.get("muhurt_type") or request.args.get("type") or "general").strip().lower()
        if muhurt_type in ("वाहन", "vehicle", "vahan", "vahan-muhurt"):
            muhurt_type = "vehicle"
        elif muhurt_type in ("व्यवसायिक", "व्यवसाय", "business", "vyavasayik", "vyavsayik", "vyavsay"):
            muhurt_type = "business"
        elif muhurt_type in ("यात्रा", "यात्रा-मुहूर्त", "yatra", "travel", "travel-muhurt"):
            muhurt_type = "yatra"
        elif muhurt_type not in ("general", "samanya", "सामान्य", "सामान्य-मुहूर्त"):
            return jsonify({"success": False, "error": "Invalid Muhurt type. Use general, vehicle, business, or yatra."}), 400
        if muhurt_type == "yatra":
            if not direction or direction not in YATRA_DIRECTIONS:
                return jsonify({"success": False, "error": "Yatra direction is required. Use a valid direction."}), 400
        return jsonify(muhurt_search(start_date, city, lat, lon, target_idx, limit, muhurt_type, direction, janma_nakshatra))
    except ValueError as e:
        return jsonify({"success": False, "error": str(e)}), 400
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.get("/api/location")
def location_api():
    try:
        q = request.args.get("q", "").strip()
        if len(q) < 2:
            return jsonify({
                "success": False,
                "error": "Enter city or pincode"
            }), 400

        return jsonify({
            "success": True,
            "results": location_search(q)
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

# ============================================================
# SERVER
# ============================================================
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
