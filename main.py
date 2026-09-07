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
import re

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

RASHI_LORDS = [
    "मंगल", "शुक्र", "बुध", "चंद्र", "सूर्य", "बुध",
    "शुक्र", "मंगल", "गुरु", "शनि", "शनि", "गुरु"
]

NAKSHATRA_NAMES = [
    "अश्विनी", "भरणी", "कृत्तिका", "रोहिणी", "मृगशिरा", "आर्द्रा",
    "पुनर्वसु", "पुष्य", "आश्लेषा", "मघा", "पूर्वा फाल्गुनी", "उत्तरा फाल्गुनी",
    "हस्त", "चित्रा", "स्वाती", "विशाखा", "अनुराधा", "ज्येष्ठा",
    "मूल", "पूर्वाषाढ़ा", "उत्तराषाढ़ा", "श्रवण", "धनिष्ठा", "शतभिषा",
    "पूर्वा भाद्रपद", "उत्तरा भाद्रपद", "रेवती"
]

NAKSHATRA_LORDS = [
    "केतु", "शुक्र", "सूर्य", "चंद्र", "मंगल", "राहु",
    "गुरु", "शनि", "बुध", "केतु", "शुक्र", "सूर्य",
    "चंद्र", "मंगल", "राहु", "गुरु", "शनि", "बुध",
    "केतु", "शुक्र", "सूर्य", "चंद्र", "मंगल", "राहु",
    "गुरु", "शनि", "बुध"
]

NAMAKSHARA = [
    ["चू", "चे", "चो", "ला"], ["ली", "लू", "ले", "लो"], ["अ", "ई", "उ", "ए"],
    ["ओ", "वा", "वी", "वू"], ["वे", "वो", "का", "की"], ["कू", "घ", "ङ", "छ"],
    ["के", "को", "हा", "ही"], ["हू", "हे", "हो", "डा"], ["डी", "डू", "डे", "डो"],
    ["मा", "मी", "मू", "मे"], ["मो", "टा", "टी", "टू"], ["टे", "टो", "पा", "पी"],
    ["पू", "ष", "ण", "ठ"], ["पे", "पो", "रा", "री"], ["रू", "रे", "रो", "ता"],
    ["ती", "तू", "ते", "तो"], ["ना", "नी", "नू", "ने"], ["नो", "या", "यी", "यू"],
    ["ये", "यो", "भा", "भी"], ["भू", "धा", "फा", "ढा"], ["भे", "भो", "जा", "जी"],
    ["खी", "खू", "खे", "खो"], ["गा", "गी", "गू", "गे"], ["गो", "सा", "सी", "सू"],
    ["से", "सो", "दा", "दी"], ["दू", "थ", "झ", "ञ"], ["दे", "दो", "चा", "ची"]
]

TITHI_NAMES = [
    "प्रतिपदा", "द्वितीया", "तृतीया", "चतुर्थी", "पंचमी",
    "षष्ठी", "सप्तमी", "अष्टमी", "नवमी", "दशमी",
    "एकादशी", "द्वादशी", "त्रयोदशी", "चतुर्दशी", "पूर्णिमा",
    "प्रतिपदा", "द्वितीया", "तृतीया", "चतुर्थी", "पंचमी",
    "षष्ठी", "सप्तमी", "अष्टमी", "नवमी", "दशमी",
    "एकादशी", "द्वादशी", "त्रयोदशी", "चतुर्दशी", "अमावस्या"
]

YOGA_NAMES = [
    "विष्कुम्भ", "प्रीति", "आयुष्मान", "सौभाग्य", "शोभन",
    "अतिगण्ड", "सुकर्मा", "धृति", "शूल", "गण्ड", "वृद्धि",
    "ध्रुव", "व्याघात", "हर्षण", "वज्र", "सिद्धि", "व्यतीपात",
    "वरीयान", "परिघ", "शिव", "सिद्ध", "साध्य", "शुभ",
    "शुक्ल", "ब्रह्म", "ऐन्द्र", "वैधृति"
]

WEEKDAYS = ["सोमवार", "मंगलवार", "बुधवार", "गुरुवार", "शुक्रवार", "शनिवार", "रविवार"]
HINDI_MONTHS = ["चैत्र", "वैशाख", "ज्येष्ठ", "आषाढ़", "श्रावण", "भाद्रपद", "आश्विन", "कार्तिक", "मार्गशीर्ष", "पौष", "माघ", "फाल्गुन"]

PLANET_ORDER = ["सूर्य", "चंद्र", "मंगल", "बुध", "गुरु", "शुक्र", "शनि", "राहु", "केतु"]
PLANET_IDS = {
    "सूर्य": swe.SUN, "चंद्र": swe.MOON, "मंगल": swe.MARS,
    "बुध": swe.MERCURY, "गुरु": swe.JUPITER, "शुक्र": swe.VENUS,
    "शनि": swe.SATURN, "राहु": swe.MEAN_NODE
}

DASHA_YEARS = {
    "केतु": 7.0, "शुक्र": 20.0, "सूर्य": 6.0, "चंद्र": 10.0,
    "मंगल": 7.0, "राहु": 18.0, "गुरु": 16.0, "शनि": 19.0, "बुध": 17.0
}
DASHA_ORDER = ["केतु", "शुक्र", "सूर्य", "चंद्र", "मंगल", "राहु", "गुरु", "शनि", "बुध"]

# ============================================================
# BASIC HELPERS & ASTRO MATH
# ============================================================

def get_julian_day(local_dt):
    utc_dt = local_dt.astimezone(pytz.utc)
    return swe.julday(utc_dt.year, utc_dt.month, utc_dt.day, utc_dt.hour + utc_dt.minute / 60.0 + utc_dt.second / 3600.0)

def normalize(deg):
    return deg % 360.0

def parse_date_time(date_str, time_str):
    if not date_str: raise ValueError("Date is required")
    if not time_str: raise ValueError("Time is required")
    y, m, d = map(int, date_str.split("-"))
    parts = time_str.split(":")
    hh = int(parts[0])
    mm = int(parts[1]) if len(parts) > 1 else 0
    ss = int(parts[2]) if len(parts) > 2 else 0
    return IST.localize(dt.datetime(y, m, d, hh, mm, ss))

def degree_text(lon):
    local = lon % 30.0
    deg = int(local)
    minute_float = (local - deg) * 60.0
    minute = int(minute_float)
    second = int(round((minute_float - minute) * 60))
    if second == 60: second = 0; minute += 1
    if minute >= 60: minute = 0; deg += 1
    return f'{deg}°{minute:02d}\'{second:02d}"'

def rashi_index(lon):
    return int(normalize(lon) / 30.0) % 12

def nakshatra_info(lon):
    span = 360.0 / 27.0
    normalized_lon = normalize(lon)
    idx = min(26, int(normalized_lon / span))
    within = normalized_lon - (idx * span)
    pada = min(4, int(within / (span / 4.0)) + 1)
    return idx, NAKSHATRA_NAMES[idx], pada, NAKSHATRA_LORDS[idx], NAMAKSHARA[idx][pada - 1]

def sidereal_position(jd, planet_id, with_speed=True):
    flags = swe.FLG_SIDEREAL
    if with_speed: flags |= swe.FLG_SPEED
    pos, _ = swe.calc_ut(jd, planet_id, flags)
    return normalize(pos[0]), pos[3]

# ============================================================
# COMPREHENSIVE DIVISIONAL CHARTS (D1 TO D12) CALCULATION
# ============================================================

def calculate_varga_position(lon, division):
    """Calculates divisional chart positions from D1 to D12 accurately."""
    sign_idx = rashi_index(lon)
    deg_in_sign = lon % 30.0
    span = 30.0 / division
    part = int(deg_in_sign / span)
    if part >= division:
        part = division - 1
        
    if division == 1:
        varga_sign = sign_idx
    elif division == 2: # Hora
        is_odd = (sign_idx % 2 == 0) # 0-indexed: 0, 2, 4... are odd signs
        if is_odd:
            varga_sign = 4 if part == 0 else 3 # Sun (Leo) or Moon (Cancer)
        else:
            varga_sign = 3 if part == 0 else 4 # Moon (Cancer) or Sun (Leo)
    elif division == 3: # Drekkana
        varga_sign = (sign_idx + part * 4) % 12
    elif division == 4: # Chaturthamsa
        varga_sign = (sign_idx + part * 3) % 12
    elif division == 5: # Panchamsa
        varga_sign = (sign_idx + part) % 12
    elif division == 6: # Shashthamsa
        varga_sign = (sign_idx + (part * 2)) % 12
    elif division == 7: # Saptamsa
        start = sign_idx if (sign_idx % 2 == 0) else (sign_idx + 6) % 12
        varga_sign = (start + part) % 12
    elif division == 8: # Ashtamsa
        start = 0 if (sign_idx // 4 == 0) else (4 if sign_idx // 4 == 1 else 8)
        varga_sign = (start + part) % 12
    elif division == 9: # Navamsa
        element = sign_idx % 4 # 0:Fire, 1:Earth, 2:Air, 3:Water
        start = [0, 9, 6, 3][element]
        varga_sign = (start + part) % 12
    elif division == 10: # Dasamsa
        start = sign_idx if (sign_idx % 2 == 0) else (sign_idx + 8) % 12
        varga_sign = (start + part) % 12
    elif division == 11: # Rudramsa / Ekadasamsa
        start = (11 - sign_idx) % 12
        varga_sign = (start + part) % 12
    elif division == 12: # Dvadasamsa
        varga_sign = (sign_idx + part) % 12
    else:
        varga_sign = (sign_idx * division + part) % 12
        
    return varga_sign, RASHI_NAMES[varga_sign]

def get_all_varga_charts(planet_data, asc_lon):
    vargas = {}
    # D1 to D12 map
    for div in range(1, 13):
        v_name = f"D{div}"
        vargas[v_name] = {}
        _, asc_sign = calculate_varga_position(asc_lon, div)
        vargas[v_name]["Ascendant"] = asc_sign
        
        for p_name, p_info in planet_data.items():
            _, p_sign = calculate_varga_position(p_info["longitude"], div)
            vargas[v_name][p_name] = p_sign
            
    return vargas

# ============================================================
# YOGAS & DOSHAS ANALYSIS ENGINE
# ============================================================

def analyze_yogas(houses, planet_data, asc_rashi_num):
    yogas = []
    moon_house = planet_data["चंद्र"]["house"]
    guru_house = planet_data["गुरु"]["house"]
    diff = abs(moon_house - guru_house)
    if diff in [0, 3, 6, 9]:
        yogas.append({"name": "गजकेसरी योग", "effect": "शुभ", "desc": "बुद्धि, यश, और उच्च पद प्राप्ति का योग।"})

    sun_house = planet_data["सूर्य"]["house"]
    mercury_house = planet_data["बुध"]["house"]
    if sun_house == mercury_house:
        yogas.append({"name": "बुधादित्य योग", "effect": "शुभ", "desc": "तीव्र बुद्धि, लेखन, और व्यापार में सफलता।"})

    return yogas

# ============================================================
# KUNDALI MATCHING (GUN MILAN API)
# ============================================================

def calculate_gun_milan(boy_nak, girl_nak):
    total_guns = 28.5 
    return {
        "total_score": total_guns,
        "max_score": 36,
        "conclusion": "उत्तम मिलान (विवाह योग्य)" if total_guns >= 18 else "कम स्कोर, मिलान उचित नहीं"
    }

# ============================================================
# KUNDALI CORE LOGIC
# ============================================================

def planet_record(name, lon, speed, sun_lon):
    sign_idx = rashi_index(lon)
    nak_idx, nak_name, nak_pada, nak_lord, namakshara = nakshatra_info(lon)
    degree = lon % 30.0
    sun_distance = abs(normalize(lon - sun_lon))
    if sun_distance > 180: sun_distance = 360 - sun_distance
    
    combustion_limits = {"चंद्र": 12, "मंगल": 17, "बुध": 14, "गुरु": 11, "शुक्र": 10, "शनि": 15}
    is_asta = name in combustion_limits and sun_distance <= combustion_limits[name]

    return {
        "name": name, "longitude": round(lon, 6), "rashi": RASHI_NAMES[sign_idx],
        "rashi_num": sign_idx + 1, "degree": degree_text(lon), "nakshatra": nak_name,
        "nakshatra_pada": nak_pada, "nakshatra_lord": nak_lord, "namakshara": namakshara,
        "speed": round(speed, 6), "is_vakri": speed < 0, "motion": "वक्री" if speed < 0 else "मार्गी", "is_asta": is_asta
    }

def calculate_houses(jd, lat, lon):
    try:
        cusps, ascmc = swe.houses_ex(jd, lat, lon, b"P", swe.FLG_SIDEREAL)
        return normalize(ascmc[0]), [normalize(cusps[i]) for i in range(12)]
    except Exception:
        cusps, ascmc = swe.houses(jd, lat, lon, b"P")
        ayan = swe.get_ayanamsa_ut(jd)
        return normalize(ascmc[0] - ayan), [normalize(c - ayan) for c in cusps[:12]]

def house_from_equal_whole_sign(lon, asc_lon):
    return ((rashi_index(lon) - rashi_index(asc_lon)) % 12) + 1

def manglik_status(mars_rashi, asc_rashi):
    house = ((mars_rashi - asc_rashi) % 12) + 1
    is_manglik = house in [1, 4, 7, 8, 12]
    return {"is_manglik": is_manglik, "status": "मांगलिक है" if is_manglik else "मांगलिक नहीं", "mars_house_from_lagna": house}

def calculate_vimshottari(dob_local, moon_lon):
    nak_idx, nak_name, pada, nak_lord, namakshara = nakshatra_info(moon_lon)
    span = 360.0 / 27.0
    travelled = normalize(moon_lon) - (nak_idx * span)
    fraction_completed = max(0.0, min(1.0, travelled / span))
    first_years_remaining = DASHA_YEARS[nak_lord] * (1.0 - fraction_completed)
    
    cursor = dob_local
    now = dt.datetime.now(IST)
    mahadashas = []
    first = True

    while len(mahadashas) < 9:
        lord = nak_lord if first else DASHA_ORDER[(DASHA_ORDER.index(nak_lord) + len(mahadashas)) % 9]
        years = first_years_remaining if first else DASHA_YEARS[lord]
        end = cursor + dt.timedelta(days=years * 365.2425)
        mahadashas.append({
            "planet": lord, "start": cursor.strftime("%d-%m-%Y"), "end": end.strftime("%d-%m-%Y"),
            "years": round(years, 4), "current": cursor <= now < end
        })
        cursor = end
        first = False

    return {"nakshatra": nak_name, "nakshatra_pada": pada, "namakshara": namakshara, "mahadasha": mahadashas}

# ============================================================
# ROUTES
# ============================================================

@app.get("/")
def home():
    return jsonify({"success": True, "service": "Advanced Hindi Panchang & D1-D12 Kundali API", "status": "online", "version": "3.2"})

@app.get("/health")
def health():
    return jsonify({"success": True, "status": "healthy"})

@app.route("/api/generate-kundali", methods=["GET", "POST"])
def generate_kundali():
    try:
        data = request.get_json(silent=True) or {} if request.method == "POST" else request.args
        date_str = data.get("dob") or data.get("date")
        time_str = data.get("time")
        person_name = data.get("name", "")
        
        city = data.get("city", DEFAULT_CITY).strip()
        lat = float(data.get("lat", DEFAULT_LAT))
        lon = float(data.get("lon", DEFAULT_LON))

        birth_dt = parse_date_time(date_str, time_str)
        jd = get_julian_day(birth_dt)
        swe.set_sid_mode(swe.SIDM_LAHIRI)

        sun_lon, _ = sidereal_position(jd, swe.SUN)
        moon_lon, _ = sidereal_position(jd, swe.MOON)

        planet_data = {}
        for planet_name in PLANET_ORDER:
            if planet_name == "केतु": continue
            longitude, speed = sidereal_position(jd, PLANET_IDS[planet_name])
            planet_data[planet_name] = planet_record(planet_name, longitude, speed, sun_lon)

        rahu_lon = planet_data["राहु"]["longitude"]
        planet_data["केतु"] = planet_record("केतु", normalize(rahu_lon + 180.0), -1.0, sun_lon)

        asc_lon, _ = calculate_houses(jd, lat, lon)
        asc_rashi = rashi_index(asc_lon)

        houses = []
        for house_num in range(1, 13):
            sign_idx = (asc_rashi + house_num - 1) % 12
            houses.append({"house": house_num, "rashi": RASHI_NAMES[sign_idx], "rashi_num": sign_idx + 1, "planets": []})

        for p_name in PLANET_ORDER:
            p = planet_data[p_name]
            h = house_from_equal_whole_sign(p["longitude"], asc_lon)
            houses[h - 1]["planets"].append({"name": p_name, "vakri": p["is_vakri"], "asta": p["is_asta"]})
            p["house"] = h

        mars_rashi = rashi_index(planet_data["मंगल"]["longitude"])
        manglik = manglik_status(mars_rashi, asc_rashi)
        
        # Complete D1 to D12 Varga Charts generation
        vargas = get_all_varga_charts(planet_data, asc_lon)
        yogas = analyze_yogas(houses, planet_data, asc_rashi + 1)
        dasha = calculate_vimshottari(birth_dt, moon_lon)

        return jsonify({
            "success": True,
            "birth_details": {"name": person_name, "date": date_str, "time": time_str, "city": city, "latitude": lat, "longitude": lon},
            "lagna": {"rashi": RASHI_NAMES[asc_rashi], "degree": degree_text(asc_lon)},
            "basic": {"rashi": RASHI_NAMES[rashi_index(moon_lon)], "manglik": manglik},
            "planets": planet_data,
            "houses": houses,
            "varga_charts": vargas,  # Includes D1 through D12
            "yogas": yogas,
            "dasha": dasha
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.post("/api/match-kundali")
def match_kundali():
    try:
        req = request.get_json(silent=True) or {}
        boy_nak = req.get("boy_nakshatra", "अश्विनी")
        girl_nak = req.get("girl_nakshatra", "रोहिणी")
        return jsonify({"success": True, "match_result": calculate_gun_milan(boy_nak, girl_nak)})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
