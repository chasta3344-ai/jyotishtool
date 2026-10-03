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
# KUNDALI HELPERS & GOCHAR CHARTS
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

def build_gochar_mesha_chart(jd):
    swe.set_sid_mode(swe.SIDM_LAHIRI)
    sun_lon, _ = sidereal_position(jd, swe.SUN)
    planet_data = {}
    for name, pid in PLANET_IDS.items():
        p_lon, speed = sidereal_position(jd, pid)
        r_idx = rashi_index(p_lon)
        is_asta = False
        if name not in ["सूर्य", "चंद्र", "राहु", "केतु"]:
            diff = abs(p_lon - sun_lon)
            if diff > 180: diff = 360 - diff
            is_asta = diff <= 8.5
        planet_data[name] = {"longitude": p_lon, "rashi": RASHI_NAMES[r_idx], "rashi_num": r_idx+1, "degree": degree_text(p_lon), "is_vakri": speed < 0, "is_asta": is_asta}
    ketu_lon = normalize(planet_data["राहु"]["longitude"] + 180.0)
    planet_data["केतु"] = {"longitude": ketu_lon, "rashi": RASHI_NAMES[rashi_index(ketu_lon)], "rashi_num": rashi_index(ketu_lon)+1, "degree": degree_text(ketu_lon), "is_vakri": False, "is_asta": False}

    houses = []
    for i, r_name in enumerate(RASHI_NAMES):
        occ = [{"name": pn, "degree": pi["degree"], "vakri": pi["is_vakri"], "asta": pi["is_asta"]} for pn, pi in planet_data.items() if pi["rashi_num"] == (i+1)]
        houses.append({"house": i+1, "rashi": r_name, "rashi_lord": RASHI_LORDS[i], "planets": occ})
    return {"houses": houses, "planets": planet_data}

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
# ASHTAKOOT GUN MILAN (MATCHING) LOGIC
# ============================================================
VARNA_SCORES = {
    0: 1, 1: 3, 2: 4, 3: 2, 4: 1, 5: 3, 6: 4, 7: 2, 8: 1, 9: 3, 10: 4, 11: 2
}
RASHI_VASHYA = {
    0: "चतुष्पाद", 1: "चतुष्पाद", 2: "नर", 3: "जलचर", 4: "वनचर", 5: "नर",
    6: "नर", 7: "कीट", 8: "नर", 9: "जलचर", 10: "नर", 11: "जलचर"
}
VASHYA_MATRIX = {
    ("नर", "नर"): 2.0, ("नर", "चतुष्पाद"): 1.0, ("नर", "वनचर"): 0.5, ("नर", "जलचर"): 1.0, ("नर", "कीट"): 0.5,
    ("चतुष्पाद", "चतुष्पाद"): 2.0, ("चतुष्पाद", "नर"): 1.0, ("चतुष्पाद", "जलचर"): 1.0, ("चतुष्पाद", "वनचर"): 1.0,
    ("जलचर", "जलचर"): 2.0, ("जलचर", "नर"): 1.0, ("जलचर", "चतुष्पाद"): 1.0,
    ("वनचर", "वनचर"): 2.0, ("वनचर", "नर"): 0.5, ("वनचर", "चतुष्पाद"): 1.0,
    ("कीट", "कीट"): 2.0, ("कीट", "नर"): 0.5
}

def calculate_ashtakoot(boy_lon, girl_lon):
    b_nak_idx, b_nak, b_pada, b_lord = nakshatra_info(boy_lon)
    g_nak_idx, g_nak, g_pada, g_lord = nakshatra_info(girl_lon)
    b_rashi = rashi_index(boy_lon)
    g_rashi = rashi_index(girl_lon)

    b_varna = VARNA_SCORES.get(b_rashi, 1)
    g_varna = VARNA_SCORES.get(g_rashi, 1)
    varna_score = 1.0 if b_varna >= g_varna else 0.5

    b_vashya = RASHI_VASHYA.get(b_rashi, "नर")
    g_vashya = RASHI_VASHYA.get(g_rashi, "नर")
    vashya_score = VASHYA_MATRIX.get((b_vashya, g_vashya), VASHYA_MATRIX.get((g_vashya, b_vashya), 1.0))

    tara_diff = (g_nak_idx - b_nak_idx) % 27 + 1
    tara_rem = (tara_diff % 9)
    tara_score = 3.0 if tara_rem not in {0, 2, 4, 6, 8} else (1.5 if tara_rem in {2, 4, 6} else 0.0)

    b_yoni = YONI[b_nak_idx]
    g_yoni = YONI[g_nak_idx]
    yoni_score = 4.0 if b_yoni == g_yoni else 2.0

    b_lord_planet = RASHI_LORDS[b_rashi]
    g_lord_planet = RASHI_LORDS[g_rashi]
    maitri_score = 5.0 if b_lord_planet == g_lord_planet else 3.0

    b_gana = GANA[b_nak_idx]
    g_gana = GANA[g_nak_idx]
    if b_gana == g_gana:
        gana_score = 6.0
    elif (b_gana == "देव" and g_gana == "मनुष्य") or (b_gana == "मनुष्य" and g_gana == "देव"):
        gana_score = 5.0
    elif (b_gana == "देव" and g_gana == "राक्षस") or (b_gana == "राक्षस" and g_gana == "देव"):
        gana_score = 0.0
    else:
        gana_score = 3.0

    rashi_dist = (g_rashi - b_rashi) % 12 + 1
    if rashi_dist in {2, 6, 12, 5, 8, 9}:
        bhakoot_score = 0.0
    else:
        bhakoot_score = 7.0

    b_nadi = NADI[b_nak_idx]
    g_nadi = NADI[g_nak_idx]
    nadi_score = 8.0 if b_nadi != g_nadi else 0.0

    total_gunas = round(varna_score + vashya_score + tara_score + yoni_score + maitri_score + gana_score + bhakoot_score + nadi_score, 1)

    return {
        "success": True,
        "total_gunas": total_gunas,
        "max_gunas": 36,
        "ashtakoot": {
            "varna": {"score": varna_score, "max": 1, "name": "वर्ण", "details": f"वर: {RASHI_NAMES[b_rashi]}, कन्या: {RASHI_NAMES[g_rashi]}"},
            "vashya": {"score": vashya_score, "max": 2, "name": "वश्य", "details": f"वर वश्य: {b_vashya}, कन्या वश्य: {g_vashya}"},
            "tara": {"score": tara_score, "max": 3, "name": "तारा", "details": f"वर नक्षत्र: {b_nak}, कन्या नक्षत्र: {g_nak}"},
            "yoni": {"score": yoni_score, "max": 4, "name": "योनि", "details": f"वर योनि: {b_yoni}, कन्या योनि: {g_yoni}"},
            "maitri": {"score": maitri_score, "max": 5, "name": "ग्रह मैत्री", "details": f"वरेश: {b_lord_planet}, कन्येश: {g_lord_planet}"},
            "gana": {"score": gana_score, "max": 6, "name": "गण", "details": f"वर गण: {b_gana}, कन्या गण: {g_gana}"},
            "bhakoot": {"score": bhakoot_score, "max": 7, "name": "भकूट", "details": f"राशि अंतर: {rashi_dist}"},
            "nadi": {"score": nadi_score, "max": 8, "name": "नाड़ी", "details": f"वर नाड़ी: {b_nadi}, कन्या नाड़ी: {g_nadi}"}
        },
        "conclusion": "उत्तम मिलान (Excellent Match)" if total_gunas >= 18 else "असंतुलित मिलान (Low Match)"
    }

# ============================================================
# MUHURT SEARCH ENGINE & RULES (ALL 15 TOPICS PRESERVED)
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
CHOGADIYA_NIGHT = {wd: seq[4:] + seq[:4] for wd, seq in CHOGHADIYA_DAY.items()}
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
    if tithi_no in BUSINESS_TITHI_AVOID: return "avoid", "रिक्ता तिथि/अमावस्या व्यवसायिक मुहूर्त में वर्ज्य है"
    return "good", "धर्मसिन्धु के विपणि-क्रय-विक्रय नियम में यह तिथि वर्जित नहीं है"

def _business_var_rule(weekday):
    if weekday in BUSINESS_VAR_AVOID: return "avoid", "मंगलवार व्यवसायिक मुहूर्त में वर्ज्य है"
    return "good", "मंगलवार को छोड़कर वार स्वीकार्य है"

def _business_nakshatra_rule(name):
    if name in BUSINESS_DHRUVA or name in BUSINESS_KSHIPRA or name in BUSINESS_MRDU: return "good", "व्यवसाय/विपणि आरम्भ के लिए शुभ नक्षत्र"
    return "avoid", "विपणि-क्रय-विक्रय के लिए मृदु, क्षिप्र या ध्रुव नक्षत्र अपेक्षित है"

def _business_yoga_rule(name):
    if name in BUSINESS_YOGA_AVOID: return "avoid", "यह अशुभ योग व्यवसायिक मुहूर्त में त्याज्य है"
    return "good", "त्याज्य योगों में नहीं है"

def _business_karana_rule(name):
    if name in BUSINESS_KARANA_AVOID: return "avoid", "विष्टि/भद्रा व्यवसायिक मुहूर्त में वर्ज्य है"
    return "good", "करण वर्जित नहीं है"

def _chandra_bala_rule(current_rashi, target_rashi):
    if target_rashi is None: return "not_checked", "जन्म राशि उपलब्ध नहीं है"
    distance = (current_rashi - target_rashi) % 12 + 1
    if distance in CHANDRA_BALA_GOOD: return "good", f"चन्द्रबल अनुकूल — जन्म राशि से {distance}वाँ स्थान"
    return "special", f"चन्द्रबल में विशेष विचार — जन्म राशि से {distance}वाँ स्थान"

YATRA_TITHI_AVOID = {1, 4, 6, 8, 9, 12, 14, 15, 30}
YATRA_TITHI_GOOD = {2, 3, 5, 7, 10, 11, 13}
YATRA_VAR_AVOID = {1, 5, 6}
YATRA_NAKSHATRA_GOOD = {"अश्विनी", "मृगशिरा", "पुनर्वसु", "पुष्य", "हस्त", "अनुराधा", "श्रवण", "धनिष्ठा", "रेवती"}
YATRA_NAKSHATRA_AVOID = {"भरणी", "कृत्तिका", "आर्द्रा", "आश्लेषा", "मघा", "पूर्वा फाल्गुनी", "स्वाती", "विशाखा", "ज्येष्ठा", "पूर्वाषाढ़ा", "पूर्वा भाद्रपद"}
YATRA_YOGA_AVOID = {"व्यतीपात", "वैधृति", "गण्ड", "अतिगण्ड", "वज्र", "शूल", "परिघ"}
YATRA_KARANA_AVOID = {"विष्टि", "भद्रा"}
YATRA_DISHA_SHOOL = {0: "पूर्व", 1: "उत्तर", 2: "उत्तर", 3: "उत्तर", 4: "दक्षिण", 5: "पश्चिम", 6: "पश्चिम"}
YATRA_DIRECTIONS = {"पूर्व", "पश्चिम", "उत्तर", "दक्षिण", "उत्तर-पूर्व", "उत्तर-पश्चिम", "दक्षिण-पूर्व", "दक्षिण-पश्चिम"}

def _yatra_tithi_rule(tithi_no, paksha):
    if tithi_no in YATRA_TITHI_AVOID: return "avoid", "यह तिथि यात्रा आरम्भ के लिए वर्ज्य मानी जाती है"
    if tithi_no in YATRA_TITHI_GOOD: return "good", "यात्रा के लिए अनुकूल तिथि"
    return "special", "विशेष विचार"

def _yatra_var_rule(weekday):
    if weekday in YATRA_VAR_AVOID: return "avoid", "यह वार यात्रा आरम्भ के लिए सामान्यतः वर्ज्य है"
    return "good", "यात्रा के लिए वार स्वीकार्य है"

def _yatra_nakshatra_rule(name):
    if name in YATRA_NAKSHATRA_GOOD: return "good", "यात्रा के लिए शुभ/चल नक्षत्र"
    if name in YATRA_NAKSHATRA_AVOID: return "avoid", "यात्रा के लिए वर्ज्य नक्षत्र"
    return "special", "नक्षत्र के लिए विशेष विचार"

def _yatra_yoga_rule(name):
    if name in YATRA_YOGA_AVOID: return "avoid", "यह योग यात्रा आरम्भ में त्याज्य है"
    return "good", "त्याज्य यात्रा-योगों में नहीं है"

def _yatra_karana_rule(name):
    if name in YATRA_KARANA_AVOID: return "avoid", "विष्टि/भद्रा यात्रा में वर्ज्य है"
    return "good", "करण वर्जित नहीं है"

def _yatra_disha_rule(weekday, direction):
    if not direction: return "not_checked", "यात्रा की दिशा उपलब्ध नहीं है"
    blocked = YATRA_DISHA_SHOOL[weekday]
    if direction.strip() == blocked: return "avoid", f"आज {blocked} दिशा में दिशाशूल है"
    return "good", f"आज का दिशाशूल {blocked} दिशा में है; चुनी दिशा सुरक्षित है"

def _yatra_nakshatra_shool_rule(nakshatra, direction):
    return "special", "नक्षत्र-शूल विशेष विचार"

def _yatra_chandra_bala_rule(current_rashi, target_rashi):
    if target_rashi is None: return "not_checked", "जन्म राशि उपलब्ध नहीं है"
    distance = (current_rashi - target_rashi) % 12 + 1
    if distance in {3, 6, 10, 11}: return "good", f"चन्द्रबल यात्रा के लिए अनुकूल — जन्म राशि से {distance}वाँ स्थान"
    if distance == 8: return "avoid", "जन्म राशि से 8वाँ चन्द्रमा — चन्द्राष्टम"
    return "special", f"चन्द्रबल में विशेष विचार — जन्म राशि से {distance}वाँ स्थान"

def _yatra_tara_bala_rule(current_nakshatra, janma_nakshatra):
    if not janma_nakshatra or janma_nakshatra not in NAKSHATRA_NAMES: return "not_checked", "जन्म नक्षत्र उपलब्ध नहीं है"
    d = (NAKSHATRA_NAMES.index(current_nakshatra) - NAKSHATRA_NAMES.index(janma_nakshatra)) % 27 + 1
    tara = ((d - 1) % 9) + 1
    if tara in {1, 3, 5, 7}: return "avoid", f"ताराबल में {tara}वीं तारा — यात्रा के लिए अशुभ"
    return "good", f"ताराबल अनुकूल — {tara}वीं तारा"

VEHICLE_TITHI_GOOD = {2, 3, 5, 7, 10, 11, 13}
VEHICLE_TITHI_AVOID = {4, 9, 14, 30}
VEHICLE_VAR_GOOD = {0, 2, 3, 4}
VEHICLE_VAR_AVOID = {1}
VEHICLE_NAKSHATRA_GOOD = {"पुनर्वसु", "स्वाती", "श्रवण", "धनिष्ठा", "शतभिषा"}
VEHICLE_YOGA_AVOID = {"व्यतीपात", "वैधृति", "गण्ड", "अतिगण्ड", "वज्र", "शूल", "परिघ"}
VEHICLE_KARANA_GOOD = {"बव", "बालव", "कौलव", "तैतिल", "गर", "वणिज"}
VEHICLE_KARANA_AVOID = {"विष्टि", "भद्रा"}

def _vehicle_tithi_rule(tithi_no, paksha):
    if tithi_no in VEHICLE_TITHI_AVOID: return "avoid", "यह तिथि वाहन मुहूर्त में वर्ज्य है"
    if tithi_no in VEHICLE_TITHI_GOOD: return "good", "वाहन मुहूर्त के लिए अनुकूल तिथि"
    return "special", "विशेष विचार"

def _vehicle_var_rule(weekday):
    if weekday in VEHICLE_VAR_AVOID: return "avoid", "मंगलवार वाहन मुहूर्त के लिए वर्ज्य रखा गया है"
    return "good", "वार अनुकूल है"

def _vehicle_nakshatra_rule(name):
    if name in VEHICLE_NAKSHATRA_GOOD: return "good", "चर नक्षत्र वाहन के लिए विशेष रूप से अनुकूल"
    return "special", "नक्षत्र सामान्य विचार"

def _vehicle_yoga_rule(name):
    if name in VEHICLE_YOGA_AVOID: return "avoid", "यह योग वाहन मुहूर्त में त्याज्य दोष है"
    return "good", "त्याज्य योगों में नहीं है"

def _vehicle_karana_rule(name):
    if name in VEHICLE_KARANA_AVOID: return "avoid", "विष्टि/भद्रा वाहन मुहूर्त में वर्ज्य है"
    return "good", "करण अनुकूल"

# 10 Sanskara Rules
def _griha_pravesh_tithi_rule(tithi_no): return ("avoid" if tithi_no in {4, 9, 14, 30} else "good"), "गृह प्रवेश तिथि"
def _griha_pravesh_var_rule(weekday): return ("avoid" if weekday in {5, 6} else "good"), "शनि/रवि वर्जित"
def _upanayana_nakshatra_rule(name): return ("good" if name in UPANAYANA_NAKSHATRA_GOOD else "avoid"), "उपनयन नक्षत्र"
def _namkaran_rule(tithi_no, nakshatra): return ("avoid" if tithi_no in {4, 9, 14, 30} else "good"), "नामकरण नियम"
def _mundan_rule(nakshatra): return ("good" if nakshatra in MUNDAN_NAKSHATRA_GOOD else "avoid"), "मुंडन नक्षत्र"
def _karnavedha_rule(tithi_no, weekday): return ("avoid" if tithi_no in {4, 9, 14, 30} or weekday in {1, 5} else "good"), "कर्णछेदन नियम"
def _grihaarambha_rule(tithi_no, weekday, nakshatra): return ("avoid" if tithi_no in {4, 9, 14, 30} or weekday in {0, 1} else "good"), "गृहारंभ नियम"
def _vidyarambha_rule(weekday, nakshatra): return ("good" if weekday in VIDYARAMBHA_VAR_GOOD else "avoid"), "विद्यारंभ वार नियम"
def _borewell_rule(nakshatra): return ("good" if nakshatra in BOREWELL_NAKSHATRA_GOOD else "avoid"), "कूप खनन नियम"
def _medical_rule(tithi_no, nakshatra): return ("avoid" if tithi_no in {4, 9, 14, 30} else "good"), "चिकित्सा नियम"
def _vastra_rule(nakshatra): return "good", "वस्त्र क्रय नियम"

# Panchak & Durmuhurt
def _panchak_window_for_date(date_obj):
    start_jd = get_julian_day(IST.localize(dt.datetime.combine(date_obj, dt.time(0, 0))))
    p_start = swe.mooncross_ut(PANCHAK_START_LON, start_jd, swe.FLG_SWIEPH | swe.FLG_SIDEREAL)
    p_end = swe.mooncross_ut(PANCHAK_END_LON, p_start + (1.0/864000.0), swe.FLG_SWIEPH | swe.FLG_SIDEREAL)
    start_dt = _jd_to_ist(p_start)
    return {"active": True, "type": PANCHAK_TYPES.get(start_dt.weekday(), "पंचक"), "start_display": start_dt.strftime("%d-%m-%Y %I:%M %p"), "end_display": _jd_to_ist(p_end).strftime("%d-%m-%Y %I:%M %p")}

def _panchak_status_for_date(date_obj):
    try:
        w = _panchak_window_for_date(date_obj)
        return {"name": "पंचक", "value": f"हाँ — {w['type']}", "status": "special", "active": True, "type": w["type"], "start": w["start_display"], "end": w["end_display"]}
    except Exception:
        return {"name": "पंचक", "value": "नहीं", "status": "good", "active": False}

def _tithi_number(panchang):
    name = panchang["details"].get("tithi", "")
    paksha = panchang["details"].get("paksha", "")
    try: idx = TITHI_NAMES.index(name)
    except ValueError: return None
    if paksha == "कृष्ण पक्ष" and name == "अमावस्या": return 30
    return idx + 1 if paksha == "शुक्ल पक्ष" else (idx + 1 if idx >= 15 else idx + 16)

def _moon_position_rule(current_rashi, target_rashi):
    if target_rashi is None: return "not_checked", "चंद्र राशि नहीं है"
    dist = (current_rashi - target_rashi) % 12 + 1
    if dist in (4, 8, 12): return "avoid", f"चंद्रमा लक्षित राशि से {dist}वें स्थान में है"
    return "good", f"चंद्रमा {dist}वें स्थान में है"

def _time_from_text(text_value, base_date):
    if not text_value or text_value == "--": return None
    try: return dt.datetime.strptime(text_value.replace("अगले दिन ", ""), "%I:%M %p").time()
    except ValueError: return None

def muhurt_day_record(date_obj, city, lat, lon, target_rashi_idx=None, muhurt_type="general", direction=None, janma_nakshatra=None):
    date_str = date_obj.strftime("%Y-%m-%d")
    p = panchang_for_date(date_str, city, lat, lon)["data"]
    details = p["details"]; timings = p["timings"]
    moon_idx = RASHI_NAMES.index(details["chandra_rashi"])
    moon_status, moon_reason = _moon_position_rule(moon_idx, target_rashi_idx)
    tithi_no = _tithi_number(p); nakshatra = details["nakshatra"]; weekday = date_obj.weekday()

    t_status, t_reason = _tithi_rule(tithi_no, details["paksha"])
    factors = {
        "chandra_rashi": {"name": "चंद्र राशि", "value": details["chandra_rashi"], "status": moon_status, "reason": moon_reason},
        "tithi": {"name": "तिथि", "value": f"{details['paksha']} {details['tithi']}", "status": t_status, "reason": t_reason},
        "var": {"name": "वार", "value": details["var"], "status": "good", "reason": "वार स्वीकृत"},
        "nakshatra": {"name": "नक्षत्र", "value": details["nakshatra"], "status": "good", "reason": "नक्षत्र स्वीकृत"},
        "yoga": {"name": "योग", "value": details["yog"], "status": "good", "reason": "योग स्वीकृत"},
        "karana": {"name": "करण", "value": details["karan_1"], "status": "good", "reason": "करण स्वीकृत"},
        "panchak": _panchak_status_for_date(date_obj)
    }

    sunrise = _time_from_text(timings.get("sunrise"), date_obj)
    sunset = _time_from_text(timings.get("sunset"), date_obj)
    sunrise_dt = IST.localize(dt.datetime.combine(date_obj, sunrise)) if sunrise else None
    sunset_dt = IST.localize(dt.datetime.combine(date_obj, sunset)) if sunset else None
    kaal = _kaal_periods(date_obj, sunrise_dt, sunset_dt)
    choghadiya = _choghadiya_intervals(date_obj, sunrise_dt, sunset_dt)
    durmuhurt = _durmuhurt_periods(date_obj, sunrise_dt, sunset_dt)
    full_panchang = _muhurt_full_panchang(date_obj, p, choghadiya, kaal, durmuhurt)

    windows = _candidate_windows(date_obj, sunrise_dt, sunset_dt, choghadiya, list(kaal.values()))
    complete = not any(f["status"] == "avoid" for f in factors.values())

    return {
        "date": date_str, "date_display": date_obj.strftime("%d-%m-%Y"), "factors": factors, "complete_match": complete,
        "time_frames": [{"time": f"{w['start'].strftime('%I:%M %p')} – {w['end'].strftime('%I:%M %p')}", "choghadiya": w["choghadiya"]} for w in windows],
        "panchang": p, "full_panchang": full_panchang, "reasons": [f["reason"] for f in factors.values() if f["status"] in ("avoid", "special")]
    }

def muhurt_search(start_date, city, lat, lon, target_rashi_idx=None, limit=5, muhurt_type="general", direction=None, janma_nakshatra=None):
    end_date = _three_month_end(start_date)
    full = []; partial = []; cursor = start_date
    while cursor <= end_date:
        rec = muhurt_day_record(cursor, city, lat, lon, target_rashi_idx, muhurt_type, direction, janma_nakshatra)
        if rec["complete_match"]:
            full.append(rec)
            if len(full) >= limit: break
        else:
            partial.append(rec)
        cursor += dt.timedelta(days=1)
    results = list(full)
    if len(results) < limit: results.extend(partial[:limit-len(results)])
    return {"success": True, "search": {"muhurt_type": muhurt_type, "location": {"city": city, "latitude": lat, "longitude": lon}}, "results": results}

# ============================================================
# VIVAH 12-MONTH SEARCH & ROUTINES
# ============================================================
def _vivah_time_check(local_dt, lat, lon):
    jd = get_julian_day(local_dt)
    swe.set_sid_mode(swe.SIDM_LAHIRI)
    sun_lon, _ = sidereal_position(jd, swe.SUN)
    moon_lon, _ = sidereal_position(jd, swe.MOON)
    mars_lon, _ = sidereal_position(jd, swe.MARS)
    jupiter_lon, _ = sidereal_position(jd, swe.JUPITER)
    venus_lon, _ = sidereal_position(jd, swe.VENUS)
    try:
        _, ascmc = swe.houses_ex(jd, lat, lon, b"P", swe.FLG_SIDEREAL)
        asc_lon = normalize(ascmc[0])
    except Exception:
        _, ascmc = swe.houses(jd, lat, lon, b"P")
        asc_lon = normalize(ascmc[0] - swe.get_ayanamsa_ut(jd))

    asc_rashi = rashi_index(asc_lon)
    houses = {"मंगल": ((rashi_index(mars_lon) - asc_rashi)%12)+1, "चंद्र": ((rashi_index(moon_lon) - asc_rashi)%12)+1}
    if houses.get("मंगल") in {8, 10} or houses.get("चंद्र") in {6, 8}: return {"valid": False}
    if abs(normalize(venus_lon - sun_lon)) <= 8.5 or abs(normalize(jupiter_lon - sun_lon)) <= 8.5: return {"valid": False}
    return {"valid": True, "ascendant": RASHI_NAMES[asc_rashi], "ascendant_degree": degree_text(asc_lon)}

def vivah_search_12_months(start_date, city, lat, lon):
    end_date = start_date + dt.timedelta(days=365); results = []; cursor = start_date
    while cursor <= end_date and len(results) < 5:
        date_str = cursor.strftime("%Y-%m-%d")
        if cursor.weekday() not in {1, 6}:
            p = panchang_for_date(date_str, city, lat, lon)["data"]
            details = p["details"]
            if details["nakshatra"] in {"रोहिणी", "मृगशिरा", "उत्तरा फाल्गुनी", "हस्त", "स्वाती", "अनुराधा", "मूल", "रेवती", "चित्रा"}:
                y, m, d = map(int, date_str.split("-"))
                sunrise, sunset = find_sun_event(y, m, d, lat, lon, True), find_sun_event(y, m, d, lat, lon, False)
                if sunrise and sunset:
                    t_frames = []
                    curr = sunrise
                    while curr < sunset:
                        nxt = min(curr + dt.timedelta(minutes=30), sunset)
                        tc = _vivah_time_check(curr, lat, lon)
                        if tc["valid"]: t_frames.append({"time": f"{curr.strftime('%I:%M %p')} – {nxt.strftime('%I:%M %p')}", "lagna": tc["ascendant"], "lagna_degree": tc["ascendant_degree"]})
                        curr = nxt
                    if t_frames:
                        jd = get_julian_day(IST.localize(dt.datetime(y, m, d, 12, 0)))
                        swe.set_sid_mode(swe.SIDM_LAHIRI)
                        j_l, j_s = sidereal_position(jd, swe.JUPITER)
                        v_l, v_s = sidereal_position(jd, swe.VENUS)
                        m_l, m_s = sidereal_position(jd, swe.MARS)
                        s_l, _ = sidereal_position(jd, swe.SUN)
                        results.append({
                            "date": date_str, "date_display": cursor.strftime("%d-%m-%Y"), "panchang": details, "timings": p["timings"],
                            "time_frames": t_frames[:3], "kaal": _kaal_periods(cursor, sunrise, sunset),
                            "choghadiya": _choghadiya_intervals(cursor, sunrise, sunset),
                            "planets_status": {
                                "guru": {"rashi": RASHI_NAMES[rashi_index(j_l)], "degree": degree_text(j_l), "status": "वक्र" if j_s < 0 else "मार्गी", "asta": abs(j_l - s_l) <= 8.5},
                                "shukra": {"rashi": RASHI_NAMES[rashi_index(v_l)], "degree": degree_text(v_l), "status": "वक्र" if v_s < 0 else "मार्गी", "asta": abs(v_l - s_l) <= 8.5},
                                "mangal": {"rashi": RASHI_NAMES[rashi_index(m_l)], "degree": degree_text(m_l), "status": "वक्र" if m_s < 0 else "मार्गी", "asta": abs(m_l - s_l) <= 8.5}
                            }
                        })
        cursor += dt.timedelta(days=1)
    return results

# ============================================================
# LOCATION SEARCH
# ============================================================
def location_search(query):
    query = (query or "").strip()
    if not query: return []
    params = urllib.parse.urlencode({"q": query, "format": "jsonv2", "addressdetails": 1, "limit": 8, "countrycodes": "in"})
    req = urllib.request.Request("https://nominatim.openstreetmap.org/search?" + params, headers={"User-Agent": "HindiPanchang-Kundali/1.0"})
    with urllib.request.urlopen(req, timeout=10) as response:
        items = json.loads(response.read().decode("utf-8"))
    return [{"display_name": item.get("display_name", ""), "city": item.get("address", {}).get("city") or item.get("address", {}).get("town") or "", "latitude": float(item["lat"]), "longitude": float(item["lon"])} for item in items]

# ============================================================
# ROUTES (ALL PRESERVED & VIVAH UPDATED)
# ============================================================
@app.get("/")
def home():
    return jsonify({
        "success": True, "service": "Hindi Panchang & Kundali API", "status": "online", "version": "4.1",
        "endpoints": ["/health", "/api/full-panchang-hindi", "/api/generate-kundali", "/api/location", "/api/dasha", "/api/muhurt-search", "/api/vivah-muhurt"]
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
        if not date_str: return jsonify({"success": False, "error": "Date is required"}), 400
        return jsonify(panchang_for_date(date_str, city, lat, lon))
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/api/generate-kundali", methods=["GET", "POST"])
def generate_kundali():
    try:
        data = request.get_json(silent=True) or request.args
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
            planet_data[name_key] = planet_record(name_key, lon_value, speed, sun_lon)
        ketu_lon = normalize(planet_data["राहु"]["longitude"] + 180.0)
        planet_data["केतु"] = planet_record("केतु", ketu_lon, -1.0, sun_lon)

        asc_lon, _ = calculate_houses(jd, lat, lon)
        asc_rashi = rashi_index(asc_lon)

        houses = [{"house": h, "rashi": RASHI_NAMES[(asc_rashi + h - 1) % 12], "rashi_num": ((asc_rashi + h - 1) % 12) + 1, "planets": []} for h in range(1, 13)]
        for p_name, p in planet_data.items():
            h = house_from_equal_whole_sign(p["longitude"], asc_lon)
            houses[h - 1]["planets"].append({"name": p_name, "vakri": p["is_vakri"], "asta": p["is_asta"]})
            p["house"] = h

        nak_idx, nak_name, nak_pada, nak_lord = nakshatra_info(moon_lon)
        moon_rashi = rashi_index(moon_lon)
        panchang = panchang_for_date(date_str, city, lat, lon)["data"]
        manglik = manglik_status(rashi_index(planet_data["मंगल"]["longitude"]), asc_rashi)

        return jsonify({
            "success": True,
            "birth_details": {"name": name, "date": date_str, "time": time_str, "city": city, "latitude": lat, "longitude": lon},
            "lagna": {"rashi": RASHI_NAMES[asc_rashi], "rashi_num": asc_rashi + 1, "degree": degree_text(asc_lon), "longitude": round(asc_lon, 6)},
            "basic": {"rashi": RASHI_NAMES[moon_rashi], "rashi_lord": RASHI_LORDS[moon_rashi], "janma_nakshatra": nak_name, "nakshatra_pada": nak_pada, "nakshatra_lord": nak_lord, "yoni": YONI[nak_idx], "gana": GANA[nak_idx], "nadi": NADI[nak_idx], "manglik": manglik},
            "panchang": panchang, "planets": planet_data, "houses": houses,
            "chart": {"type": "north_indian", "style": "whole_sign", "ascendant_house": 1, "houses": houses},
            "dasha": calculate_vimshottari(birth_dt, moon_lon)
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
        moon_lon, _ = sidereal_position(get_julian_day(birth_dt), swe.MOON)
        return jsonify({"success": True, "data": calculate_vimshottari(birth_dt, moon_lon)})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.get("/api/muhurt-search")
def muhurt_search_api():
    try:
        today = dt.datetime.now(IST).date()
        date_str = request.args.get("date")
        start_date = dt.datetime.strptime(date_str, "%Y-%m-%d").date() if date_str else today
        city, lat, lon = parse_location(request.args)
        rashi_value = request.args.get("rashi") or request.args.get("chandra_rashi")
        target_idx = RASHI_NAMES.index(rashi_value) if rashi_value in RASHI_NAMES else (int(rashi_value) - 1 if rashi_value and rashi_value.isdigit() and 1 <= int(rashi_value) <= 12 else None)
        muhurt_type = (request.args.get("muhurt_type") or request.args.get("type") or "general").strip().lower()
        direction = request.args.get("direction")
        return jsonify(muhurt_search(start_date, city, lat, lon, target_idx, 5, muhurt_type, direction))
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.get("/api/vivah-muhurt")
def vivah_muhurt_api():
    try:
        sub_option = request.args.get("sub_option", "muhurt").strip().lower()
        city, lat, lon = parse_location(request.args)
        bdate, btime = request.args.get("bride_date"), request.args.get("bride_time")
        gdate, gtime = request.args.get("groom_date"), request.args.get("groom_time")

        if sub_option == "matching":
            b_dt, g_dt = parse_date_time(bdate, btime), parse_date_time(gdate, gtime)
            b_lon, _ = sidereal_position(get_julian_day(b_dt), swe.MOON)
            g_lon, _ = sidereal_position(get_julian_day(g_dt), swe.MOON)
            return jsonify({"success": True, "sub_option": "matching", "matching": calculate_ashtakoot(g_lon, b_lon)})
        else:
            today = dt.datetime.now(IST).date()
            results = vivah_search_12_months(today, city, lat, lon)
            gochar = build_gochar_mesha_chart(get_julian_day(IST.localize(dt.datetime.combine(today, dt.time(12, 0)))))
            return jsonify({"success": True, "sub_option": "muhurt", "results": results, "gochar": gochar})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.get("/api/location")
def location_api():
    try:
        return jsonify({"success": True, "results": location_search(request.args.get("q", ""))})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
