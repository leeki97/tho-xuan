#!/usr/init/env python3
# -*- coding: utf-8 -*-
"""
WEB APP DỰ BÁO MƯA & DÔNG HỆ THỐNG SÂN BAY VIỆT NAM - HOÀN CHỈNH v4.25
(Thêm Sân bay Hòa Lạc, nút Sidebar & Modal Thuyết trình toàn màn hình)
"""

from __future__ import annotations

import html
import math
import time
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from zoneinfo import ZoneInfo

import pandas as pd
import plotly.graph_objects as go
import requests
import streamlit as st

# =========================
# 1. DANH SÁCH SÂN BAY & CẤU HÌNH
# =========================

AIRPORT_DATABASE = {
    "Sân bay Thọ Xuân (VVTX)": {"lat": 19.9017, "lon": 105.4678},
    "Sân bay Hòa Lạc (Hà Nội)": {"lat": 21.0167, "lon": 105.5167},
    "Sân bay Nội Bài (VVNB)": {"lat": 21.2212, "lon": 105.8072},
    "Sân bay Tân Sơn Nhất (VVTS)": {"lat": 10.8188, "lon": 106.6519},
    "Sân bay Đà Nẵng (VVDN)": {"lat": 16.0439, "lon": 108.1994},
    "Sân bay Cát Bi (VVCI)": {"lat": 20.8234, "lon": 106.7219},
    "Sân bay Phú Bài (VVPB)": {"lat": 16.4014, "lon": 107.7028},
    "Sân bay Cam Ranh (VVCR)": {"lat": 11.9981, "lon": 109.2194},
    "Sân bay Cần Thơ (VVCT)": {"lat": 10.0850, "lon": 105.7120},
    "Sân bay Vinh (VVVH)": {"lat": 18.7360, "lon": 105.6710},
    "Sân bay Phù Cát (VVPC)": {"lat": 13.9542, "lon": 109.0433},
    "Sân bay Pleiku (VVPL)": {"lat": 14.0020, "lon": 108.0160},
    "Sân bay Buôn Ma Thuột (VVBM)": {"lat": 12.6660, "lon": 108.1210},
    "Sân bay Chu Lai (VVCA)": {"lat": 15.4050, "lon": 108.7060},
    "Sân bay Đồng Hới (VVDH)": {"lat": 17.5110, "lon": 106.5910},
    "Sân bay Tuy Hòa (VVTH)": {"lat": 13.0450, "lon": 109.3230},
    "Sân bay Gia Lâm (VVGL)": {"lat": 21.0420, "lon": 105.8920},
    "Sân bay Kép (Bắc Giang)": {"lat": 21.3650, "lon": 106.2650},
    "Sân bay Biên Hòa (Đồng Nai)": {"lat": 10.9620, "lon": 106.8630},
    "Sân bay Yên Bái": {"lat": 21.7167, "lon": 104.8833},
    "Sân bay Móng Cái (Quảng Ninh)": {"lat": 21.5200, "lon": 107.9700},
    "Sân bay Phan Rang (Ninh Thuận)": {"lat": 11.5600, "lon": 108.9800},
    "Sân bay Phan Thiết (Bình Thuận)": {"lat": 10.9200, "lon": 108.1000},
}

TIMEZONE = "Asia/Bangkok"
FORECAST_DAYS = 10
REQUEST_TIMEOUT = 60
OPEN_METEO_URL = "https://api.open-meteo.com/v1/forecast"

HOURLY_VARIABLES = [
    "temperature_2m",
    "relative_humidity_2m",
    "dew_point_2m",
    "precipitation_probability",
    "precipitation",
    "rain",
    "showers",
    "weather_code",
    "cloud_cover",
    "cloud_cover_low",
    "cloud_cover_mid",
    "cloud_cover_high",
    "visibility",
    "surface_pressure",
    "cape",
    "wind_speed_10m",
    "wind_direction_10m",
    "wind_gusts_10m",
    "relative_humidity_850hPa",
    "relative_humidity_700hPa",
    "vertical_velocity_700hPa",
]

st.set_page_config(page_title="Thời tiết Sân bay Việt Nam", page_icon="✈️", layout="wide")

# =========================
# CẤU HÌNH PHÔNG CHỮ & GIAO DIỆN (CSS)
# =========================
st.markdown(
    """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif !important;
    }
    
    .main { background-color: #f8fafc; }
    
    .summary-box { 
        background-color: #ffffff; 
        border-left: 5px solid #1e3a8a; 
        padding: 16px 20px; 
        border-radius: 6px; 
        box-shadow: 0 1px 3px rgba(0,0,0,0.08); 
        margin-bottom: 16px; 
        font-size: 14.5px; 
        line-height: 1.6; 
        color: #1e293b;
    }
    
    .stButton>button { 
        border-radius: 6px; 
        font-weight: 600; 
    }
    
    .tab-content {
        background: #ffffff;
        padding: 20px;
        border-radius: 8px;
        border: 1px solid #e2e8f0;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
        margin-bottom: 20px;
        font-size: 14.5px;
        line-height: 1.8;
        color: #334155;
    }
</style>
""",
    unsafe_allow_html=True,
)

if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False


def render_login_screen():
    col1, col2, col3 = st.columns([1, 1.2, 1])
    with col2:
        st.markdown("### ✈️ Đăng nhập Hệ thống Khí tượng Sân bay")
        st.caption("Tài khoản: admin | Mật khẩu: 123")
        with st.form("login_form"):
            username = st.text_input("Tên đăng nhập", value="admin")
            password = st.text_input("Mật khẩu", type="password")
            submit = st.form_submit_button("Truy cập hệ thống", use_container_width=True)
            if submit:
                if username == "admin" and password == "123":
                    st.session_state["logged_in"] = True
                    st.rerun()
                else:
                    st.error("Sai mật khẩu! Mật khẩu hiện tại là: 123")


if not st.session_state["logged_in"]:
    render_login_screen()
    st.stop()


# =========================
# 2. HÀM CHUYỂN ĐỔI AN TOÀN
# =========================

def safe_float(value: Any, default: float = 0.0) -> float:
    try:
        if pd.isna(value) or value is None or str(value).lower() == 'nan':
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def safe_int(value: Any, default: int = 0) -> int:
    try:
        if pd.isna(value) or value is None or str(value).lower() == 'nan':
            return default
        return int(float(value))
    except (TypeError, ValueError):
        return default


# =========================
# 3. HÀM PHÂN TÍCH & DỮ LIỆU
# =========================

@dataclass
class HourlyForecast:
    forecast_time: str
    temperature_2m: float
    relative_humidity_2m: float
    dew_point_2m: float
    precipitation_probability_model: float
    precipitation: float
    rain: float
    showers: float
    weather_code: int
    cloud_cover: float
    cloud_cover_low: float
    cloud_cover_mid: float
    cloud_cover_high: float
    visibility_raw: float
    visibility_m: float
    surface_pressure: float
    cape: float
    wind_speed_10m: float
    wind_direction_10m: float
    wind_gusts_10m: float
    relative_humidity_850hPa: float
    relative_humidity_700hPa: float
    vertical_velocity_700hPa: float

    estimated_cloud_base_ft: float = 0.0
    estimated_cloud_top_ft: float = 0.0

    radar_score: float = 0.0
    moisture_score: float = 0.0
    cloud_score: float = 0.0
    model_rain_score: float = 0.0
    instability_score: float = 0.0
    lifting_score: float = 0.0
    pop_calibrated: float = 0.0
    thunder_probability: float = 0.0
    rain_level: str = ""
    confidence_note: str = ""


def generate_10_day_synoptic_outlook(forecasts: List[HourlyForecast], lat: float, airport_name: str) -> str:
    if not forecasts:
        return "Đang cập nhật dữ liệu xu thế..."

    daily_summary = {}
    for fc in forecasts:
        dt = datetime.fromisoformat(fc.forecast_time.replace("Z", ""))
        day_str = dt.strftime("%d/%m")
        daily_summary.setdefault(day_str, {"temps": [], "pops": [], "rains": []})
        daily_summary[day_str]["temps"].append(fc.temperature_2m)
        daily_summary[day_str]["pops"].append(fc.pop_calibrated)
        daily_summary[day_str]["rains"].append(max(fc.precipitation, fc.rain, fc.showers))

    max_overall_temp = -99
    min_overall_temp = 99
    rainy_days = []

    for day, metrics in daily_summary.items():
        max_t = max(metrics["temps"])
        min_t = min(metrics["temps"])
        max_pop = max(metrics["pops"])
        total_rain = sum(metrics["rains"])

        max_overall_temp = max(max_overall_temp, max_t)
        min_overall_temp = min(min_overall_temp, min_t)

        if max_pop >= 50 or total_rain >= 2.0:
            rainy_days.append(day)

    current_synoptic = ""
    if lat >= 18.5:
        current_synoptic = (
            "<b>1. Phân tích các hệ thống thời tiết chính hiện tại (Khu vực Bắc Bộ & Bắc Trung Bộ):</b><br>"
            "• <b>Áp cao lạnh lục địa:</b> Khối không khí lạnh chi phối thời tiết miền Bắc, duy trì trạng thái hanh khô ban ngày và se lạnh về đêm, sáng sớm có sương mù nhẹ.<br>"
        )
    elif 13.0 <= lat < 18.5:
        current_synoptic = (
            "<b>1. Phân tích hệ thống thời tiết (Khu vực Trung Trung Bộ):</b><br>"
            "• Đới gió Đông kết hợp không khí lạnh suy yếu tạo mây thay đổi, có mưa rào nhẹ vài nơi về đêm và sáng.<br>"
        )
    else:
        current_synoptic = (
            "<b>1. Phân tích hệ thống thời tiết (Khu vực Nam Bộ & Tây Nguyên):</b><br>"
            "• Gió Đông Bắc cường độ trung bình, ban ngày nắng ráo, chiều tối có mưa rào cục bộ vài nơi.<br>"
        )

    sea_info = "• <b>Khu vực Biển Đông:</b> Không có bão hoặc áp thấp nhiệt đới ảnh hưởng trực tiếp.<br>"
    upcoming_system = "<b>2. Nhận định xu thế:</b> Thời tiết ổn định trong ngắn hạn, lưu ý hiện tượng giảm tầm nhìn sáng sớm do sương mù bức xạ.<br>"
    local_trend = f"<b>3. Biên độ nhiệt tại {airport_name}:</b> Từ <b>+{min_overall_temp:.0f}°C đến +{max_overall_temp:.0f}°C</b>."

    return f"<div style='line-height: 1.6; font-size: 13.5px;'>{current_synoptic}{sea_info}<br>{upcoming_system}<br>{local_trend}</div>"


def clamp(value: float, minimum: float = 0.0, maximum: float = 100.0) -> float:
    return max(minimum, min(maximum, value))


def sigmoid(value: float) -> float:
    if value >= 0:
        return 1.0 / (1.0 + math.exp(-value))
    z = math.exp(value)
    return z / (1.0 + z)


def normalize(value: float, low: float, high: float) -> float:
    if high <= low:
        return 0.0
    return clamp((value - low) / (high - low) * 100.0)


def dewpoint_spread(temperature: float, dewpoint: float) -> float:
    return max(0.0, temperature - dewpoint)


def get_hour(dt_text: str) -> int:
    return datetime.fromisoformat(dt_text).hour


def get_month(dt_text: str) -> int:
    return datetime.fromisoformat(dt_text).month


def wind_deg_to_dir(deg: float) -> str:
    dirs = ["B", "ĐB", "Đ", "ĐN", "N", "TN", "T", "TB"]
    idx = int((deg + 22.5) // 45) % 8
    return dirs[idx]


def fetch_open_meteo(lat: float, lon: float, wind_unit: str = "kmh") -> Dict[str, Any]:
    params = {
        "latitude": lat,
        "longitude": lon,
        "hourly": ",".join(HOURLY_VARIABLES),
        "timezone": TIMEZONE,
        "forecast_days": FORECAST_DAYS,
        "wind_speed_unit": wind_unit,
        "precipitation_unit": "mm",
    }
    max_retries = 3
    for attempt in range(max_retries):
        try:
            response = requests.get(OPEN_METEO_URL, params=params, timeout=REQUEST_TIMEOUT)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            if attempt == max_retries - 1:
                raise e
            time.sleep(2)
    return {}


def parse_forecasts(data: Dict[str, Any]) -> List[HourlyForecast]:
    hourly = data["hourly"]
    times = hourly["time"]
    forecasts: List[HourlyForecast] = []
    for i, forecast_time in enumerate(times):
        vis_val = safe_float(hourly.get("visibility", [0] * len(times))[i])
        temp_val = safe_float(hourly.get("temperature_2m", [0] * len(times))[i])
        dew_val = safe_float(hourly.get("dew_point_2m", [0] * len(times))[i])
        cloud_total = safe_float(hourly.get("cloud_cover", [0] * len(times))[i])
        cape_val = safe_float(hourly.get("cape", [0] * len(times))[i])
        rh_850 = safe_float(hourly.get("relative_humidity_850hPa", [0] * len(times))[i])
        
        # 1. Chân mây (Cloud Base) theo Espy's formula: ((T - Td) / 2.5) * 1000 ft
        spread = max(0.1, temp_val - dew_val)
        cloud_base_ft = round((spread / 2.5) * 1000.0, 0)
        cloud_base_ft = max(200.0, min(cloud_base_ft, 25000.0))

        # 2. Đỉnh mây (Cloud Top) an toàn
        thickness = 1800.0 + (cloud_total * 25.0) + (min(cape_val, 1000.0) * 0.5)
        cloud_top_ft = round(cloud_base_ft + max(1500.0, thickness), 0)

        forecasts.append(
            HourlyForecast(
                forecast_time=str(forecast_time),
                temperature_2m=temp_val,
                relative_humidity_2m=safe_float(hourly.get("relative_humidity_2m", [0] * len(times))[i]),
                dew_point_2m=dew_val,
                precipitation_probability_model=safe_float(hourly.get("precipitation_probability", [0] * len(times))[i]),
                precipitation=safe_float(hourly.get("precipitation", [0] * len(times))[i]),
                rain=safe_float(hourly.get("rain", [0] * len(times))[i]),
                showers=safe_float(hourly.get("showers", [0] * len(times))[i]),
                weather_code=safe_int(hourly.get("weather_code", [0] * len(times))[i]),
                cloud_cover=cloud_total,
                cloud_cover_low=safe_float(hourly.get("cloud_cover_low", [0] * len(times))[i]),
                cloud_cover_mid=safe_float(hourly.get("cloud_cover_mid", [0] * len(times))[i]),
                cloud_cover_high=safe_float(hourly.get("cloud_cover_high", [0] * len(times))[i]),
                visibility_raw=vis_val,
                visibility_m=vis_val,
                surface_pressure=safe_float(hourly.get("surface_pressure", [0] * len(times))[i]),
                cape=cape_val,
                wind_speed_10m=safe_float(hourly.get("wind_speed_10m", [0] * len(times))[i]),
                wind_direction_10m=safe_float(hourly.get("wind_direction_10m", [0] * len(times))[i]),
                wind_gusts_10m=safe_float(hourly.get("wind_gusts_10m", [0] * len(times))[i]),
                relative_humidity_850hPa=rh_850,
                relative_humidity_700hPa=safe_float(hourly.get("relative_humidity_700hPa", [0] * len(times))[i]),
                vertical_velocity_700hPa=safe_float(hourly.get("vertical_velocity_700hPa", [0] * len(times))[i]),
                estimated_cloud_base_ft=cloud_base_ft,
                estimated_cloud_top_ft=cloud_top_ft,
            )
        )
    return forecasts


def calibrate_visibility_and_wind(fc: HourlyForecast, lat: float, lon: float, wind_unit: str = "kmh") -> None:
    dt = datetime.fromisoformat(fc.forecast_time.replace("Z", ""))
    hour = dt.hour
    is_tho_xuan = (abs(lat - 19.9017) < 0.25 and abs(lon - 105.4678) < 0.25)

    if is_tho_xuan and (hour >= 22 or hour <= 6) and fc.relative_humidity_2m >= 88:
        if wind_unit == "kmh":
            fc.wind_speed_10m = min(fc.wind_speed_10m, 5.0)
        else:
            fc.wind_speed_10m = min(fc.wind_speed_10m, 1.5)

    vis = fc.visibility_raw
    spread = dewpoint_spread(fc.temperature_2m, fc.dew_point_2m)
    rain_amount = max(fc.precipitation, fc.rain, fc.showers)
    wind_kmh = fc.wind_speed_10m if wind_unit == "kmh" else fc.wind_speed_10m * 3.6

    if 7 <= hour <= 17 and rain_amount < 0.3 and fc.relative_humidity_2m < 85:
        fc.visibility_m = max(vis, 10000.0)
        return

    effective_rain = rain_amount if rain_amount >= 0.3 else 0.0

    if effective_rain == 0.0 and spread > 1.2:
        if is_tho_xuan:
            if spread >= 3.0 and fc.relative_humidity_2m < 85:
                vis += 4000.0
            elif spread >= 2.0:
                vis += 2500.0
            else:
                vis += 1500.0
            
            if wind_kmh >= 6.0:
                vis += 1000.0
        else:
            if spread >= 2.5 and vis < 10000.0:
                vis += 1200.0

    fc.visibility_m = min(vis, 35000.0)


def process_forecast_models(
    forecasts: List[HourlyForecast], wind_unit: str = "kmh", lat: float = 0.0, lon: float = 0.0
) -> List[HourlyForecast]:
    for fc in forecasts:
        calibrate_visibility_and_wind(fc, lat, lon, wind_unit)

        rain_raw = max(fc.precipitation, fc.rain, fc.showers)
        if rain_raw < 0.3 and fc.relative_humidity_2m < 85:
            fc.precipitation = 0.0
            fc.rain = 0.0
            fc.showers = 0.0

        spread = dewpoint_spread(fc.temperature_2m, fc.dew_point_2m)
        moisture = (
            0.30 * fc.relative_humidity_2m
            + 0.45 * fc.relative_humidity_850hPa
            + 0.25 * fc.relative_humidity_700hPa
        )
        if spread <= 1.5:
            moisture += 8
        elif spread <= 3.0:
            moisture += 4
        elif spread >= 8.0:
            moisture -= 10
        fc.moisture_score = clamp(moisture)

        fc.cloud_score = clamp(
            0.50 * fc.cloud_cover_low + 0.35 * fc.cloud_cover_mid + 0.15 * fc.cloud_cover_high
        )

        rain_amount = max(fc.precipitation, fc.rain, fc.showers)
        amount_score = clamp(100.0 * (1.0 - math.exp(-rain_amount / 2.0)))
        model_pop = fc.precipitation_probability_model

        fc.model_rain_score = clamp(0.65 * model_pop + 0.35 * amount_score)

        cape_score = normalize(fc.cape, 100.0, 2200.0)
        hour = get_hour(fc.forecast_time)
        month = get_month(fc.forecast_time)
        daytime_factor = 1.10 if 11 <= hour <= 18 else (0.80 if hour <= 6 or hour >= 21 else 1.0)
        seasonal_factor = (
            1.10 if month in (5, 6, 7, 8, 9) else (0.65 if month in (11, 12, 1, 2) else 0.90)
        )
        fc.instability_score = clamp(cape_score * daytime_factor * seasonal_factor)
        fc.lifting_score = clamp(max(0.0, -fc.vertical_velocity_700hPa) * 100.0)

        wind_kmh = fc.wind_speed_10m if wind_unit == "kmh" else fc.wind_speed_10m * 3.6
        wind_dir = fc.wind_direction_10m
        if 30 <= wind_dir <= 130 and wind_kmh >= 5:
            fc.moisture_score = clamp(fc.moisture_score + 5.0)
        elif 200 <= wind_dir <= 260 and spread > 4.0:
            fc.moisture_score = clamp(fc.moisture_score - 8.0)

        z = (
            -4.20
            + 0.027 * model_pop
            + 0.016 * fc.moisture_score
            + 0.010 * fc.cloud_score
            + 0.010 * fc.model_rain_score
            + 0.004 * fc.instability_score
            + 0.003 * fc.lifting_score
            + 0.010 * fc.radar_score
            + 0.65 * min(rain_amount, 5.0)
            - 0.055 * max(spread - 3.0, 0.0)
        )
        prob = sigmoid(z) * 100.0

        if fc.relative_humidity_850hPa < 50 and rain_amount < 0.1:
            prob = min(prob, 25)
        if fc.relative_humidity_700hPa < 40 and rain_amount < 0.1:
            prob = min(prob, 35)
        if fc.cloud_cover_low < 20 and fc.cloud_cover_mid < 30 and rain_amount < 0.1:
            prob = min(prob, 20)
        if rain_amount >= 0.5 and model_pop >= 50:
            prob = max(prob, 55)

        fc.pop_calibrated = round(clamp(prob), 1)

        thunder_weather_code = fc.weather_code in (95, 96, 99)
        thunder_z = (
            -7.20
            + 0.00165 * fc.cape
            + 0.010 * model_pop
            + 0.50 * min(rain_amount, 4.0)
            + 0.004 * fc.moisture_score
            + (2.20 if thunder_weather_code else 0.0)
        )
        thunder_prob = sigmoid(thunder_z) * 100.0
        if fc.cape < 300:
            thunder_prob = min(thunder_prob, 10)
        fc.thunder_probability = round(clamp(thunder_prob), 1)

        fc.rain_level = (
            "Rất cao"
            if fc.pop_calibrated >= 80
            else (
                "Cao"
                if fc.pop_calibrated >= 60
                else ("Trung bình" if fc.pop_calibrated >= 40 else "Thấp")
            )
        )
        fc.confidence_note = "Open-Meteo"

    return forecasts


# =========================
# 4. HÀM TẠO BẢNG NGANG CHI TIẾT SỐ LIỆU
# =========================

def get_weather_icon(fc: HourlyForecast) -> str:
    if fc.thunder_probability >= 45:
        return "⛈️"
    if fc.pop_calibrated >= 60 or max(fc.precipitation, fc.rain) >= 0.5:
        return "🌧️"
    if fc.pop_calibrated >= 35 or max(fc.precipitation, fc.rain) >= 0.1:
        return "🌦️"
    if fc.cloud_cover >= 75:
        return "☁️"
    if fc.cloud_cover >= 35:
        return "⛅"
    return "☀️"


def get_temp_bg(temp: float) -> str:
    if temp >= 35:
        return "#ffcccc"
    if temp >= 30:
        return "#ffe5cc"
    if temp >= 25:
        return "#fff5cc"
    if temp >= 20:
        return "#e6f7ff"
    return "#cce5ff"


def get_pop_bg(pop: float) -> str:
    if pop >= 75:
        return "#ff9999; font-weight: bold; color: #7a0000;"
    if pop >= 50:
        return "#ffcc99; font-weight: bold;"
    if pop >= 30:
        return "#fff2cc;"
    return "#ffffff;"


def render_rp5_horizontal_table(forecasts: List[HourlyForecast], wind_unit_text: str) -> str:
    if not forecasts:
        return "<p>Không có dữ liệu hiển thị.</p>"

    days_map: Dict[str, List[HourlyForecast]] = {}
    viet_days = ["Thứ 2", "Thứ 3", "Thứ 4", "Thứ 5", "Thứ 6", "Thứ 7", "Chủ nhật"]
    for fc in forecasts:
        dt = datetime.fromisoformat(fc.forecast_time.replace("Z", ""))
        day_label = f"{viet_days[dt.weekday()]}, {dt.strftime('%d/%m')}"
        days_map.setdefault(day_label, []).append(fc)

    header_days = ['<th class="sticky-col row-title">Ngày trong tuần</th>']
    for day_label, items in days_map.items():
        header_days.append(f'<th colspan="{len(items)}" class="day-header">{html.escape(day_label)}</th>')

    row_hours = ['<td class="sticky-col row-title">Giờ địa phương</td>']
    row_icons = ['<td class="sticky-col row-title">Hiện tượng</td>']
    row_pop = ['<td class="sticky-col row-title"><b>PoP Hiệu chỉnh (%)</b></td>']
    row_thunder = ['<td class="sticky-col row-title">Nguy cơ Dông (%)</td>']
    row_rain = ['<td class="sticky-col row-title">Lượng mưa (mm)</td>']
    row_temp = ['<td class="sticky-col row-title">Nhiệt độ 2m (°C)</td>']
    row_dew = ['<td class="sticky-col row-title">Điểm sương (°C)</td>']
    
    row_cloud_total = ['<td class="sticky-col row-title">Mây tổng (%)</td>']
    row_cloud_low = ['<td class="sticky-col row-title">Mây thấp (%)</td>']
    row_cloud_mid = ['<td class="sticky-col row-title">Mây trung (%)</td>']
    row_cloud_high = ['<td class="sticky-col row-title">Mây cao (%)</td>']
    row_cloud_base = ['<td class="sticky-col row-title" style="background:#eef2f6;"><b>Chân mây (ft / m)</b></td>']
    row_cloud_top = ['<td class="sticky-col row-title" style="background:#eef2f6;"><b>Đỉnh mây (ft / m)</b></td>']

    row_wind = [f'<td class="sticky-col row-title">Gió duy trì ({wind_unit_text})</td>']
    row_gust = [f'<td class="sticky-col row-title">Gió giật ({wind_unit_text})</td>']
    row_rh = ['<td class="sticky-col row-title">Độ ẩm 2m (%)</td>']
    row_rh850 = ['<td class="sticky-col row-title">Độ ẩm 850hPa (%)</td>']
    row_vis_raw = ['<td class="sticky-col row-title" style="color:#64748b;">Tầm nhìn Gốc (km)</td>']
    row_vis_cal = ['<td class="sticky-col row-title" style="color:#1d4ed8;"><b>Tầm nhìn Hiệu chỉnh (km)</b></td>']
    row_press = ['<td class="sticky-col row-title">Áp suất (hPa)</td>']

    fmt_wind = ".1f" if wind_unit_text == "m/s" else ".0f"

    for fc in forecasts:
        dt = datetime.fromisoformat(fc.forecast_time.replace("Z", ""))
        rain_val = max(fc.precipitation, fc.rain, fc.showers)
        wind_dir = wind_deg_to_dir(fc.wind_direction_10m)
        base_m = int(fc.estimated_cloud_base_ft * 0.3048)
        top_m = int(fc.estimated_cloud_top_ft * 0.3048)

        row_hours.append(f'<td class="hour-cell">{dt.strftime("%H:%M")}</td>')
        row_icons.append(f'<td style="font-size: 18px;">{get_weather_icon(fc)}</td>')
        row_pop.append(f'<td style="background:{get_pop_bg(fc.pop_calibrated)}">{fc.pop_calibrated:.0f}%</td>')
        row_thunder.append(
            f'<td style="background:{get_pop_bg(fc.thunder_probability)}">{fc.thunder_probability:.0f}%</td>'
        )
        row_rain.append(
            f'<td><b>{rain_val:.1f}</b></td>' if rain_val > 0 else '<td style="color:#94a3b8;">0.0</td>'
        )
        row_temp.append(
            f'<td style="background:{get_temp_bg(fc.temperature_2m)}"><b>+{fc.temperature_2m:.1f}</b></td>'
        )
        row_dew.append(f'<td>{fc.dew_point_2m:.1f}</td>')
        
        row_cloud_total.append(f'<td>{fc.cloud_cover:.0f}%</td>')
        row_cloud_low.append(f'<td>{fc.cloud_cover_low:.0f}%</td>')
        row_cloud_mid.append(f'<td>{fc.cloud_cover_mid:.0f}%</td>')
        row_cloud_high.append(f'<td>{fc.cloud_cover_high:.0f}%</td>')
        row_cloud_base.append(f'<td style="background:#f8fafc;"><b>{fc.estimated_cloud_base_ft:.0f} ft</b><br><span style="color:#64748b;font-size:11px;">({base_m}m)</span></td>')
        row_cloud_top.append(f'<td style="background:#f8fafc;"><b>{fc.estimated_cloud_top_ft:.0f} ft</b><br><span style="color:#64748b;font-size:11px;">({top_m}m)</span></td>')

        row_wind.append(f'<td>{wind_dir} {fc.wind_speed_10m:{fmt_wind}}</td>')
        row_gust.append(f'<td style="color:#ef4444; font-weight:bold;">{fc.wind_gusts_10m:{fmt_wind}}</td>')
        row_rh.append(f'<td>{fc.relative_humidity_2m:.0f}%</td>')
        row_rh850.append(f'<td><b>{fc.relative_humidity_850hPa:.0f}%</b></td>')
        row_vis_raw.append(f'<td style="color:#64748b;">{fc.visibility_raw/1000:.1f}</td>')
        row_vis_cal.append(f'<td><b>{fc.visibility_m/1000:.1f}</b></td>')
        row_press.append(f'<td>{fc.surface_pressure:.0f}</td>')

    table_html = f"""
    <style>
        .rp5-container {{ width: 100%; overflow-x: auto; border: 1px solid #cbd5e1; border-radius: 8px; background: #ffffff; box-shadow: 0 2px 6px rgba(0,0,0,0.06); }}
        .rp5-table {{ border-collapse: collapse; width: max-content; font-family: 'Inter', sans-serif; font-size: 13px; text-align: center; }}
        .rp5-table th, .rp5-table td {{ border: 1px solid #e2e8f0; padding: 6px 10px; white-space: nowrap; }}
        .sticky-col {{ position: sticky; left: 0; background-color: #f1f5f9 !important; z-index: 2; text-align: left !important; font-weight: 600; color: #1e293b; border-right: 2px solid #94a3b8 !important; }}
        .day-header {{ background-color: #1e3a8a; color: white; font-size: 13px; padding: 8px; }}
        .hour-cell {{ background-color: #f8fafc; font-weight: bold; color: #334155; }}
    </style>
    <div class="rp5-container">
        <table class="rp5-table">
            <thead><tr>{''.join(header_days)}</tr></thead>
            <tbody>
                <tr>{''.join(row_hours)}</tr>
                <tr>{''.join(row_icons)}</tr>
                <tr>{''.join(row_pop)}</tr>
                <tr>{''.join(row_thunder)}</tr>
                <tr>{''.join(row_rain)}</tr>
                <tr>{''.join(row_temp)}</tr>
                <tr>{''.join(row_dew)}</tr>
                <tr>{''.join(row_cloud_total)}</tr>
                <tr>{''.join(row_cloud_low)}</tr>
                <tr>{''.join(row_cloud_mid)}</tr>
                <tr>{''.join(row_cloud_high)}</tr>
                <tr>{''.join(row_cloud_base)}</tr>
                <tr>{''.join(row_cloud_top)}</tr>
                <tr>{''.join(row_wind)}</tr>
                <tr>{''.join(row_gust)}</tr>
                <tr>{''.join(row_rh)}</tr>
                <tr>{''.join(row_rh850)}</tr>
                <tr>{''.join(row_vis_raw)}</tr>
                <tr>{''.join(row_vis_cal)}</tr>
                <tr>{''.join(row_press)}</tr>
            </tbody>
        </table>
    </div>
    """
    return table_html


# =========================
# 5. ĐỊNH NGHĨA MODAL TOÀN MÀN HÌNH (st.dialog) CHO THUYẾT TRÌNH MÔ HÌNH
# =========================
@st.dialog("📚 Thuyết trình Chi tiết Mô hình Dự báo Khí tượng Sân bay", width="large")
def show_model_presentation_modal():
    st.markdown("💡 *Bảng thuyết trình chuyên sâu về nguồn số liệu, công thức toán học và khả năng áp dụng thực tế trong công tác khí tượng hàng không.*")
    
    tab1, tab2, tab3, tab4 = st.tabs([
        "📂 Nguồn số liệu đầu vào", 
        "🧮 Công thức & Thuật toán", 
        "🎯 Kết quả đạt được", 
        "🚀 Khả năng ứng dụng"
    ])

    with tab1:
        st.markdown("""
        <div class="tab-content">
            <b>1. Nguồn dữ liệu số trị toàn cầu (NWPs):</b><br>
            • Sử dụng API mô hình số trị tiên tiến <b>Open-Meteo</b> (tích hợp dữ liệu từ ECMWF, GFS, ICON).<br>
            • Cung cấp chuỗi thời gian 10 ngày với bước thời gian từng giờ (hourly), bao gồm các thông số bề mặt và khí quyển cao cấp.<br><br>
            <b>2. Các biến khí tượng được trích xuất:</b><br>
            • <b>Nhiệt độ & Điểm sương ($T, T_d$):</b> Tại độ cao 2m.<br>
            • <b>Hệ thống mây:</b> Lượng mây tổng ($CloudCover$), mây thấp, mây trung, mây cao.<br>
            • <b>Động lực khí quyển:</b> Năng lượng đối lưu khả dụng (CAPE), vận tốc thẳng đứng tại tầng 700hPa ($w$).<br>
            • <b>Độ ẩm các tầng cao:</b> Độ ẩm tương đối tại tầng 850hPa và 700hPa.<br>
            • <b>Trường gió & Áp suất:</b> Tốc độ gió 10m, hướng gió, gió giật và áp suất khí quyển bề mặt.
        </div>
        """, unsafe_allow_html=True)

    with tab2:
        st.markdown("""
        <div class="tab-content">
            <b>1. Tính toán độ cao Chân mây (Cloud Base Height - Espy's Formula):</b><br>
            • <i>Công thức:</i> $\\text{Base (ft)} = \\frac{T - T_d}{2.5} \\times 1000$<br>
            • <i>Diễn giải:</i> Dựa trên độ chênh lệch nhiệt độ và điểm sương. Khi khối khí ẩm bốc lên đoạn nhiệt, nhiệt độ và điểm sương hội tụ với tốc độ khoảng 2.5°C trên mỗi 1000 ft, xác định chính xác điểm ngưng tụ.<br><br>
            <b>2. Tính toán độ cao Đỉnh mây (Cloud Top Height):</b><br>
            • <i>Công thức:</i> $\\text{Top (ft)} = \\text{Base (ft)} + 1800 + (\\text{CloudCover} \\times 25) + (\\min(\\text{CAPE}, 1000) * 0.5)$<br>
            • <i>Diễn giải:</i> Đỉnh mây được ước tính bằng cách cộng độ dày tầng mây, tăng lên khi lượng mây phong phú và năng lượng đối lưu CAPE lớn.<br><br>
            <b>3. Hiệu chỉnh Tầm nhìn theo chuẩn METAR (Bias Correction):</b><br>
            • Khắc phục nhược điểm mô hình toàn cầu hay bị kẹt ở 24.1km và bóp thấp bất thường ban ngày. Hệ thống tự động ép tầm nhìn tối thiểu $\\ge 10\\text{ km}$ lúc ban ngày khô ráo ($RH < 85\\%$) và cộng bù trừ điểm sương để phản ánh sương mù bức xạ về đêm.<br><br>
            <b>4. Hiệu chỉnh Xác suất Mưa (PoP) & Nguy cơ Dông:</b><br>
            • Sử dụng hàm kích hoạt phi tuyến tính <b>Sigmoid</b> kết hợp các trọng số độ ẩm đa tầng, CAPE và vận tốc thẳng đứng.
        </div>
        """, unsafe_allow_html=True)

    with tab3:
        st.markdown("""
        <div class="tab-content">
            <b>1. Độ chính xác và độ tin cậy:</b><br>
            • Khắc phục hoàn toàn hiện tượng dự báo sai lệch cục địa của các mô hình toàn cầu nhờ thuật toán hiệu chỉnh riêng cho từng vùng sân bay.<br>
            • Đảm bảo biểu đồ trực quan không bị lỗi số liệu (như đỉnh mây bằng 0) và luôn có giá trị logic an toàn hàng không.<br><br>
            <b>2. Giao diện trực quan hóa:</b><br>
            • Bảng chi tiết dạng ma trận RP5 trực quan, cho phép kéo ngang theo dõi 10 ngày.<br>
            • Hệ thống biểu đồ tương tác (Plotly) hỗ trợ zoom, trượt, xem trực tiếp trên mọi thiết bị di động và máy tính.
        </div>
        """, unsafe_allow_html=True)

    with tab4:
        st.markdown("""
        <div class="tab-content">
            <b>1. Ứng dụng trong ngành Hàng không:</b><br>
            • Cung cấp dữ liệu chân mây, đỉnh mây và tầm nhìn chính xác giúp tổ bay, đài kiểm soát không lưu và đơn vị khai thác lập kế hoạch cất/hạ cánh an toàn.<br>
            • Cảnh báo sớm nguy cơ dông sét, gió giật mạnh và giảm tầm nhìn đột ngột.<br><br>
            <b>2. Khả năng mở rộng:</b><br>
            • Dễ dàng tích hợp thêm các sân bay khác trong mạng lưới hàng không dân dụng và quân sự Việt Nam.<br>
            • Có thể phát triển tiếp tính năng đẩy cảnh báo tự động qua Telegram/Email khi các thông số thời tiết chạm ngưỡng giới hạn khai thác (minimums).
        </div>
        """, unsafe_allow_html=True)
    
    if st.button("Đóng bảng thuyết trình", use_container_width=True):
        st.rerun()


# =========================
# 6. GIAO DIỆN CHÍNH STREAMLIT (SIDEBAR)
# =========================

st.sidebar.markdown("### 👤 Tài khoản Quản trị")
st.sidebar.success("Đang đăng nhập: **admin**")
if st.sidebar.button("🚪 Đăng xuất", use_container_width=True):
    st.session_state["logged_in"] = False
    st.rerun()

st.sidebar.markdown("---")
st.sidebar.markdown("### ✈️ Lựa chọn Sân bay")
selected_airport_name = st.sidebar.selectbox("Chọn điểm quan trắc:", list(AIRPORT_DATABASE.keys()), index=0)

LATITUDE = AIRPORT_DATABASE[selected_airport_name]["lat"]
LONGITUDE = AIRPORT_DATABASE[selected_airport_name]["lon"]

st.sidebar.markdown("---")
days_to_show = st.sidebar.selectbox(
    "Phạm vi dự báo xem trước:", [2, 3, 5, 7, 10], index=1, format_func=lambda x: f"{x} ngày tới"
)

wind_unit_label = st.sidebar.selectbox(
    "Đơn vị tốc độ gió:", ["km/h (Km/giờ)", "m/s (Mét/giây)"], index=0
)
wind_unit_param = "kmh" if "km/h" in wind_unit_label else "ms"
wind_unit_text = "km/h" if wind_unit_param == "kmh" else "m/s"

# Đưa nút Thuyết trình sang Sidebar
st.sidebar.markdown("---")
st.sidebar.markdown("### 📖 Tài liệu Chuyên môn")
if st.sidebar.button("📖 Thuyết trình Mô hình Dự báo", use_container_width=True):
    show_model_presentation_modal()


@st.cache_data(ttl=1800)
def load_data(lat: float, lon: float, w_unit: str):
    raw = fetch_open_meteo(lat, lon, wind_unit=w_unit)
    forecasts = parse_forecasts(raw)
    processed = process_forecast_models(forecasts, wind_unit=w_unit, lat=lat, lon=lon)
    return processed


with st.spinner(f"Đang đồng bộ dữ liệu khí tượng 10 ngày tại {selected_airport_name}..."):
    try:
        forecasts = load_data(LATITUDE, LONGITUDE, wind_unit_param)
    except Exception as e:
        st.error(f"Lỗi kết nối dữ liệu: {e}")
        st.stop()

now = datetime.now(ZoneInfo(TIMEZONE)).replace(minute=0, second=0, microsecond=0, tzinfo=None)
future_forecasts = [
    fc for fc in forecasts if datetime.fromisoformat(fc.forecast_time.replace("Z", "")) >= now
]

if not future_forecasts:
    st.warning("Không có dữ liệu dự báo khả dụng.")
    st.stop()

col_title, col_btn = st.columns([4, 1])
with col_title:
    st.title(f"🌤️ Thời tiết tại {selected_airport_name}")
    st.caption(
        f"Tọa độ: {LATITUDE}°N, {LONGITUDE}°E · Cập nhật lúc: {datetime.now(ZoneInfo(TIMEZONE)).strftime('%H:%M %d/%m/%Y')}"
    )
with col_btn:
    st.write("")
    if st.button("🔄 Cập nhật mới", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

curr = future_forecasts[0]
next_24h = future_forecasts[:24]
min_t = min(f.temperature_2m for f in next_24h)
max_t = max(f.temperature_2m for f in next_24h)
max_pop = max(f.pop_calibrated for f in next_24h)
rain_desc = (
    "có khả năng xuất hiện mưa rào/dông"
    if max_pop >= 50
    else ("có thể có mưa nhỏ vài nơi" if max_pop >= 30 else "thời tiết khô ráo, không mưa")
)
fmt_curr_wind = ".1f" if wind_unit_text == "m/s" else ".0f"

st.markdown(
    f"""
<div class="summary-box">
    <b>Hiện tại ({curr.forecast_time.split('T')[1]}):</b> Nhiệt độ <b>+{curr.temperature_2m:.1f} °C</b>, độ ẩm <b>{curr.relative_humidity_2m:.0f}%</b>, gió {wind_deg_to_dir(curr.wind_direction_10m)} <b>{curr.wind_speed_10m:{fmt_curr_wind}} {wind_unit_text}</b>, tầm nhìn hiệu chỉnh <b>{curr.visibility_m/1000:.1f} km</b>.<br>
    <b>Dự báo 24 giờ tới:</b> Nhiệt độ dao động từ <b>+{min_t:.0f}..+{max_t:.0f} °C</b>, {rain_desc} (Xác suất mưa hiệu chỉnh cao nhất: <b>{max_pop:.0f}%</b>).
</div>
""",
    unsafe_allow_html=True,
)

with st.expander("🌐 Yếu tố ảnh hưởng & Bản tin Phân tích Hệ thống Thời tiết", expanded=False):
    synoptic_outlook_html = generate_10_day_synoptic_outlook(future_forecasts[:240], LATITUDE, selected_airport_name)
    st.markdown(synoptic_outlook_html, unsafe_allow_html=True)

filtered = future_forecasts[: days_to_show * 24]

st.markdown("### 📅 Bảng dự báo chi tiết từng giờ (Kéo ngang để xem)")
st.markdown(render_rp5_horizontal_table(filtered, wind_unit_text), unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# =========================
# 7. BIỂU ĐỒ PHÂN TÍCH KHÍ TƯỢNG
# =========================

st.markdown("### 📈 Biểu đồ Phân tích Chi tiết Từng Số liệu")
st.caption("💡 Mẹo trên điện thoại: Dùng 2 ngón tay để phóng to/thu nhỏ (pinch-to-zoom) hoặc trượt sang trái/phải để xem chi tiết từng biểu đồ.")

chart_data = pd.DataFrame(
    [
        {
            "Thời gian": fc.forecast_time.replace("T", " "),
            "Nhiệt độ 2m (°C)": fc.temperature_2m,
            "Điểm sương (°C)": fc.dew_point_2m,
            "PoP Hiệu chỉnh (%)": fc.pop_calibrated,
            "Nguy cơ Dông (%)": fc.thunder_probability,
            "Lượng mưa (mm)": max(fc.precipitation, fc.rain, fc.showers),
            f"Tốc độ gió ({wind_unit_text})": fc.wind_speed_10m,
            f"Gió giật ({wind_unit_text})": fc.wind_gusts_10m,
            "Độ ẩm 2m (%)": fc.relative_humidity_2m,
            "Độ ẩm 850hPa (%)": fc.relative_humidity_850hPa,
            "Tầm nhìn Gốc (km)": round(fc.visibility_raw / 1000.0, 1),
            "Tầm nhìn Hiệu chỉnh (km)": round(fc.visibility_m / 1000.0, 1),
            "Chân mây (ft)": fc.estimated_cloud_base_ft,
            "Đỉnh mây (ft)": fc.estimated_cloud_top_ft,
            "Áp suất (hPa)": fc.surface_pressure,
        }
        for fc in filtered
    ]
)

touch_config = {"scrollZoom": True, "displayModeBar": True, "responsive": True}

st.markdown("#### 🌡️ 1. Nhiệt độ & Điểm sương")
fig1 = go.Figure()
fig1.add_trace(go.Scatter(x=chart_data["Thời gian"], y=chart_data["Nhiệt độ 2m (°C)"], name="Nhiệt độ (°C)", mode="lines+markers", line=dict(color="#ea580c", width=2.5)))
fig1.add_trace(go.Scatter(x=chart_data["Thời gian"], y=chart_data["Điểm sương (°C)"], name="Điểm sương (°C)", mode="lines", line=dict(color="#0d9488", width=1.8, dash="dash")))
fig1.update_layout(height=300, margin=dict(l=10, r=10, t=30, b=10), legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1), hovermode="x unified")
st.plotly_chart(fig1, use_container_width=True, config=touch_config)
st.markdown("<br>", unsafe_allow_html=True)

st.markdown("#### 🌧️ 2. Xác suất Mưa (PoP) & Nguy cơ Dông")
fig2 = go.Figure()
fig2.add_trace(go.Scatter(x=chart_data["Thời gian"], y=chart_data["PoP Hiệu chỉnh (%)"], name="PoP Hiệu chỉnh (%)", mode="lines+markers", line=dict(color="#1d4ed8", width=2.5)))
fig2.add_trace(go.Scatter(x=chart_data["Thời gian"], y=chart_data["Nguy cơ Dông (%)"], name="Nguy cơ Dông (%)", mode="lines", line=dict(color="#dc2626", width=2, dash="dot")))
fig2.update_layout(height=300, margin=dict(l=10, r=10, t=30, b=10), legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1), hovermode="x unified")
fig2.update_yaxes(range=[0, 105])
st.plotly_chart(fig2, use_container_width=True, config=touch_config)
st.markdown("<br>", unsafe_allow_html=True)

st.markdown("#### 💧 3. Lượng mưa (mm)")
fig3 = go.Figure()
fig3.add_trace(go.Bar(x=chart_data["Thời gian"], y=chart_data["Lượng mưa (mm)"], name="Lượng mưa (mm)", marker_color="#3b82f6"))
fig3.update_layout(height=300, margin=dict(l=10, r=10, t=30, b=10), legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1), hovermode="x unified")
st.plotly_chart(fig3, use_container_width=True, config=touch_config)
st.markdown("<br>", unsafe_allow_html=True)

st.markdown(f"#### 💨 4. Tốc độ gió & Gió giật ({wind_unit_text})")
fig4 = go.Figure()
fig4.add_trace(go.Scatter(x=chart_data["Thời gian"], y=chart_data[f"Tốc độ gió ({wind_unit_text})"], name=f"Gió duy trì ({wind_unit_text})", mode="lines+markers", line=dict(color="#0284c7", width=2.5)))
fig4.add_trace(go.Scatter(x=chart_data["Thời gian"], y=chart_data[f"Gió giật ({wind_unit_text})"], name=f"Gió giật ({wind_unit_text})", mode="lines", line=dict(color="#e11d48", width=1.8, dash="dot")))
fig4.update_layout(height=300, margin=dict(l=10, r=10, t=30, b=10), legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1), hovermode="x unified")
st.plotly_chart(fig4, use_container_width=True, config=touch_config)
st.markdown("<br>", unsafe_allow_html=True)

st.markdown("#### ☁️ 5. Độ cao Chân mây & Đỉnh mây ước tính (ft)")
fig5 = go.Figure()
fig5.add_trace(go.Scatter(x=chart_data["Thời gian"], y=chart_data["Đỉnh mây (ft)"], name="Đỉnh mây (ft)", mode="lines", line=dict(color="#7c3aed", width=2), fill="tozeroy", fillcolor="rgba(124, 58, 237, 0.08)"))
fig5.add_trace(go.Scatter(x=chart_data["Thời gian"], y=chart_data["Chân mây (ft)"], name="Chân mây (ft)", mode="lines+markers", line=dict(color="#0284c7", width=2.5)))
fig5.update_layout(height=300, margin=dict(l=10, r=10, t=30, b=10), legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1), hovermode="x unified")
st.plotly_chart(fig5, use_container_width=True, config=touch_config)
st.markdown("<br>", unsafe_allow_html=True)

st.markdown("#### 👁️ 6a. Tầm nhìn Gốc (km)")
fig6a = go.Figure()
fig6a.add_trace(go.Scatter(x=chart_data["Thời gian"], y=chart_data["Tầm nhìn Gốc (km)"], name="Tầm nhìn Gốc (km)", mode="lines", line=dict(color="#64748b", width=2)))
fig6a.update_layout(height=280, margin=dict(l=10, r=10, t=30, b=10), legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1), hovermode="x unified")
st.plotly_chart(fig6a, use_container_width=True, config=touch_config)
st.markdown("<br>", unsafe_allow_html=True)

st.markdown("#### 👁️‍🗨️ 6b. Tầm nhìn Hiệu chỉnh theo METAR (km)")
fig6b = go.Figure()
fig6b.add_trace(go.Scatter(x=chart_data["Thời gian"], y=chart_data["Tầm nhìn Hiệu chỉnh (km)"], name="Tầm nhìn Hiệu chỉnh (km)", mode="lines+markers", line=dict(color="#1d4ed8", width=2.5), fill="tozeroy", fillcolor="rgba(29, 78, 216, 0.1)"))
fig6b.update_layout(height=280, margin=dict(l=10, r=10, t=30, b=10), legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1), hovermode="x unified")
st.plotly_chart(fig6b, use_container_width=True, config=touch_config)
st.markdown("<br>", unsafe_allow_html=True)

st.markdown("#### ⏱️ 7. Áp suất bề mặt (hPa)")
fig7 = go.Figure()
fig7.add_trace(go.Scatter(x=chart_data["Thời gian"], y=chart_data["Áp suất (hPa)"], name="Áp suất (hPa)", mode="lines", line=dict(color="#475569", width=2)))
fig7.update_layout(height=300, margin=dict(l=10, r=10, t=30, b=10), legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1), hovermode="x unified")
st.plotly_chart(fig7, use_container_width=True, config=touch_config)
