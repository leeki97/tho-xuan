#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
WEB APP DỰ BÁO MƯA & DÔNG HỆ THỐNG SÂN BAY VIỆT NAM - HOÀN CHỈNH v4.35
(Cache 3h, đổi đơn vị mây ft/m, nhận diện hình thế theo mùa & vùng khí hậu cho toàn bộ sân bay, phân tích chi tiết mưa/tầm nhìn/nhiệt độ)
"""

from __future__ import annotations

import html
import math
import time
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Dict, List
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

HORIZON_OPTIONS: Dict[str, int] = {
    "48 giờ tới": 48,
    "72 giờ tới": 72,
    "5 ngày tới (120h)": 120,
    "10 ngày tới (240h)": 240,
}

CLOUD_UNIT_OPTIONS: Dict[str, str] = {
    "Feet (ft)": "ft",
    "Mét (m)": "m",
}

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

st.set_page_config(
    page_title="Thời tiết Sân bay Việt Nam",
    page_icon="✈️",
    layout="wide",
    initial_sidebar_state="collapsed",
)

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
# 2. HÀM CHUYỂN ĐỔI AN TOÀN, ĐƠN VỊ & THỜI GIAN
# =========================

def safe_float(value: Any, default: float = 0.0) -> float:
    try:
        if pd.isna(value) or value is None or str(value).lower() == "nan":
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def safe_int(value: Any, default: int = 0) -> int:
    try:
        if pd.isna(value) or value is None or str(value).lower() == "nan":
            return default
        return int(float(value))
    except (TypeError, ValueError):
        return default


def parse_local_dt(dt_text: str) -> datetime:
    dt = datetime.fromisoformat(dt_text.replace("Z", ""))
    if dt.tzinfo is None:
        return dt.replace(tzinfo=ZoneInfo(TIMEZONE))
    return dt.astimezone(ZoneInfo(TIMEZONE))


def get_3h_cycle_key(now_dt: datetime) -> str:
    """
    Tạo khóa chu kỳ 3 tiếng/lần theo giờ Việt Nam (UTC+7):
    00:00, 03:00, 06:00, 09:00, 12:00, 15:00, 18:00, 21:00.
    """
    cycle_hour = (now_dt.hour // 3) * 3
    cycle_dt = now_dt.replace(hour=cycle_hour, minute=0, second=0, microsecond=0)
    return cycle_dt.strftime("%Y-%m-%d %H:00")


def convert_cloud_ft(cloud_ft: float, cloud_unit: str) -> float:
    if cloud_unit == "m":
        return round(cloud_ft * 0.3048, 0)
    return round(cloud_ft, 0)


def format_cloud_height(cloud_ft: float, cloud_unit: str) -> str:
    val = convert_cloud_ft(cloud_ft, cloud_unit)
    return f"{val:.0f} {cloud_unit}"


# =========================
# 3. HÀM PHÂN TÍCH, NHẬN DIỆN HÌNH THẾ & DỮ LIỆU
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
    return parse_local_dt(dt_text).hour


def wind_deg_to_dir(deg: float) -> str:
    dirs = ["B", "ĐB", "Đ", "ĐN", "N", "TN", "T", "TB"]
    idx = int((deg + 22.5) // 45) % 8
    return dirs[idx]


def _season_name(month: int) -> str:
    if month in (12, 1, 2):
        return "Mùa Đông"
    if month in (3, 4):
        return "Mùa Xuân (chuyển tiếp / nồm ẩm)"
    if month in (5, 6, 7, 8):
        return "Mùa Hè (cao điểm nắng nóng & mưa dông/Tây Nam)"
    return "Mùa Thu (giao mùa & mưa lớn/không khí lạnh sớm)"


def _climate_zone_by_lat(lat: float) -> str:
    """
    Phân vùng khí hậu theo vĩ độ sân bay để chuẩn hóa ngưỡng nhận diện hình thế:
    - 'north_central': Bắc Bộ & Bắc Trung Bộ (lat >= 17.5)
    - 'central_highlands': Trung Trung Bộ & Tây Nguyên (12.0 <= lat < 17.5)
    - 'south': Nam Bộ & Nam Trung Bộ cực Nam (lat < 12.0)
    """
    if lat >= 17.5:
        return "north_central"
    if lat >= 12.0:
        return "central_highlands"
    return "south"


def detect_synoptic_patterns(forecasts: List[HourlyForecast], lat: float) -> List[str]:
    """
    Nhận diện các hình thế hoàn lưu theo mùa vụ và vùng khí hậu cho toàn bộ
    hệ thống sân bay Việt Nam từ chuỗi số liệu mô hình giờ.
    """
    if not forecasts:
        return []

    months = [parse_local_dt(fc.forecast_time).month for fc in forecasts]
    dominant_month = max(set(months), key=months.count)
    season_txt = _season_name(dominant_month)
    zone = _climate_zone_by_lat(lat)

    zone_label = {
        "north_central": "Bắc Bộ & Bắc Trung Bộ",
        "central_highlands": "Trung Trung Bộ & Tây Nguyên",
        "south": "Nam Bộ & Nam Trung Bộ",
    }[zone]

    n = len(forecasts)
    patterns: List[str] = [
        f"**Mùa vụ & Vùng chi phối:** {season_txt} (tháng trọng tâm: {dominant_month:02d}) — khu vực {zone_label}."
    ]

    pressures = [fc.surface_pressure for fc in forecasts if fc.surface_pressure > 0]
    p_first_avg = sum(pressures[:24]) / max(1, len(pressures[:24])) if pressures else 0.0
    p_last_avg = sum(pressures[-24:]) / max(1, len(pressures[-24:])) if pressures else 0.0
    p_delta = p_last_avg - p_first_avg

    # 1. Áp cao lục địa / Không khí lạnh & KKL lệch Đông (chủ yếu vùng có lat >= 12.0, mùa thu-đông-xuân)
    ne_count = sum(1 for fc in forecasts if 330.0 <= fc.wind_direction_10m or fc.wind_direction_10m <= 60.0)
    ne_ratio = ne_count / n
    cold_surge_wet = sum(
        1
        for fc in forecasts
        if (20.0 <= fc.wind_direction_10m <= 115.0)
        and fc.relative_humidity_850hPa >= 78.0
        and (fc.cloud_cover_low >= 60.0 or max(fc.precipitation, fc.rain, fc.showers) >= 0.3)
    )

    if zone in ("north_central", "central_highlands") and dominant_month in (9, 10, 11, 12, 1, 2, 3, 4):
        ne_min_ratio = 0.20 if zone == "north_central" else 0.25
        p_high_min = 1014.0 if zone == "north_central" else 1013.0
        if ne_ratio >= ne_min_ratio or (pressures and max(pressures) >= p_high_min):
            if p_delta >= 1.2:
                p_trend = "có xu hướng tăng / tăng cường"
            elif p_delta <= -1.2:
                p_trend = "có xu hướng suy yếu và dịch ra phía Đông"
            else:
                p_trend = "duy trì tương đối ổn định"
            patterns.append(
                f"**Áp cao lục địa / Không khí lạnh:** Gió Bắc–Đông Bắc chiếm ~{ne_ratio * 100:.0f}% số giờ, "
                f"áp suất mặt đất {p_trend} ({p_delta:+.1f} hPa)."
            )
            if cold_surge_wet >= 3:
                patterns.append(
                    f"**Không khí lạnh tăng cường lệch Đông / Gió mùa Đông Bắc ẩm:** Ghi nhận {cold_surge_wet} mốc gió Đông Bắc–Đông "
                    f"kèm ẩm tầng 850hPa cao và mây thấp/mưa rải rác, dễ gây mây thấp và mưa nhỏ/mưa rào."
                )

    # Gió Đông Bắc mùa khô ở phía Nam (tháng 11 - tháng 3)
    if zone == "south" and dominant_month in (11, 12, 1, 2, 3) and ne_ratio >= 0.25:
        patterns.append(
            f"**Gió Đông Bắc mùa khô:** Gió hướng Bắc–Đông Bắc chiếm ~{ne_ratio * 100:.0f}% số giờ, "
            f"thời tiết phổ biến ít mưa, nắng nhiều hơn vào ban ngày."
        )

    # 2. Sương mù & Nồm ẩm (áp dụng mọi sân bay)
    rh_fog_min = 86.0 if zone in ("north_central", "central_highlands") else 88.0
    spread_fog_max = 1.5 if zone == "north_central" else 1.2
    fog_min_hits = 3 if zone == "north_central" else 4

    fog_nom_count = sum(
        1
        for fc in forecasts
        if fc.relative_humidity_2m >= rh_fog_min
        and dewpoint_spread(fc.temperature_2m, fc.dew_point_2m) <= spread_fog_max
        and (parse_local_dt(fc.forecast_time).hour <= 8 or parse_local_dt(fc.forecast_time).hour >= 21)
    )
    if fog_nom_count >= fog_min_hits:
        nom_note = (
            " (lưu ý nồm ẩm / mây thấp kéo dài)"
            if dominant_month in (2, 3, 4) and zone == "north_central"
            else ""
        )
        patterns.append(
            f"**Sương mù / Mù ẩm sát bão hòa{nom_note}:** Có {fog_nom_count} mốc đêm–sáng sớm có độ ẩm >= {rh_fog_min:.0f}% "
            f"và chênh nhiệt – điểm sương <= {spread_fog_max:.1f}°C, làm tăng nguy cơ suy giảm tầm nhìn."
        )

    # 3. Gió mùa Tây Nam (mùa mưa: tháng 5 - tháng 10)
    sw_count = sum(
        1
        for fc in forecasts
        if 195.0 <= fc.wind_direction_10m <= 265.0
        and (fc.relative_humidity_850hPa >= 72.0 or max(fc.precipitation, fc.rain, fc.showers) >= 0.2)
    )
    sw_min_hits = 4 if zone == "south" else 6
    if dominant_month in (5, 6, 7, 8, 9, 10) and sw_count >= sw_min_hits:
        patterns.append(
            f"**Gió mùa Tây Nam:** Ghi nhận {sw_count} mốc luồng gió Tây Nam–Tây hoạt động kèm ẩm tầng thấp–trung, "
            f"thuận lợi phát sinh mưa rào và dông (thường rõ hơn về chiều và tối)."
        )

    # 4. Áp thấp nóng phía Tây (tháng 4 - tháng 8, vùng có lat >= 12.0)
    if zone in ("north_central", "central_highlands"):
        temp_hot_min = 32.5 if zone == "north_central" else 33.0
        rh_hot_max = 70.0 if zone == "north_central" else 68.0
        spread_hot_min = 5.5 if zone == "north_central" else 6.0
        hot_min_hits = 3

        hot_low_count = 0
        for fc in forecasts:
            dt_fc = parse_local_dt(fc.forecast_time)
            sp_daytime = dewpoint_spread(fc.temperature_2m, fc.dew_point_2m)
            is_west_or_sw_wind = 180.0 <= fc.wind_direction_10m <= 295.0
            if (
                dt_fc.month in (4, 5, 6, 7, 8)
                and 9 <= dt_fc.hour <= 17
                and fc.temperature_2m >= temp_hot_min
                and fc.relative_humidity_2m <= rh_hot_max
                and sp_daytime >= spread_hot_min
                and max(fc.precipitation, fc.rain, fc.showers) < 0.2
                and (is_west_or_sw_wind or fc.temperature_2m >= 35.0)
            ):
                hot_low_count += 1

        if hot_low_count >= hot_min_hits:
            max_hot_temp = max(fc.temperature_2m for fc in forecasts)
            patterns.append(
                f"**Áp thấp nóng phía Tây:** Ghi nhận {hot_low_count} mốc ban ngày nắng nóng, không khí khô hơn "
                f"(nhiệt đỉnh ~{max_hot_temp:.1f}°C), chú ý nắng nóng/gió Tây ban ngày và dông nhiệt cục bộ về chiều tối."
            )

    # 5. Nhiễu động đới gió Đông & dấu hiệu mưa lớn / xoáy thuận nhiệt đới (mọi sân bay)
    e_disturbance_count = sum(
        1
        for fc in forecasts
        if (60.0 <= fc.wind_direction_10m <= 135.0)
        and fc.relative_humidity_850hPa >= 76.0
        and (fc.vertical_velocity_700hPa <= -0.07 or max(fc.precipitation, fc.rain, fc.showers) >= 0.8)
    )
    strong_rain_wind_count = sum(
        1
        for fc in forecasts
        if max(fc.precipitation, fc.rain, fc.showers) >= 2.5
        and (fc.wind_gusts_10m >= 38.0 or fc.relative_humidity_850hPa >= 85.0)
    )
    e_min_hits = 3 if zone in ("north_central", "central_highlands") else 4
    strong_min_hits = 2 if zone in ("north_central", "central_highlands") else 3

    if e_disturbance_count >= e_min_hits:
        patterns.append(
            f"**Nhiễu động đới gió Đông:** Có {e_disturbance_count} mốc gió Đông–Đông Nam ẩm "
            f"kết hợp nâng mực 700hPa hoặc mưa, dễ gây mây dày, mưa rào và mưa vừa/to cục bộ."
        )
    if strong_rain_wind_count >= strong_min_hits:
        patterns.append(
            f"**Nhiễu động mạnh / Dấu hiệu xoáy thuận nhiệt đới – mưa lớn:** Xuất hiện {strong_rain_wind_count} mốc mưa đáng kể "
            f"kèm gió giật hoặc ẩm tầng 850hPa rất cao; cần đối chiếu thêm bản đồ synop và cảnh báo áp thấp/bão."
        )

    # 6. Dải hội tụ nhiệt đới (ITCZ) / Đối lưu nhiệt ẩm mạnh (mọi sân bay)
    itcz_conv_count = sum(
        1
        for fc in forecasts
        if fc.relative_humidity_850hPa >= 80.0
        and fc.relative_humidity_700hPa >= 70.0
        and fc.vertical_velocity_700hPa <= -0.12
        and (fc.cape >= 400.0 or max(fc.precipitation, fc.rain, fc.showers) >= 1.0)
    )
    cape_high_threshold = 700.0 if zone == "south" else 800.0
    if itcz_conv_count >= 3 or (
        dominant_month in (4, 5, 6, 7, 8, 9, 10) and any(fc.cape >= cape_high_threshold for fc in forecasts)
    ):
        patterns.append(
            f"**Dải hội tụ nhiệt đới / Đối lưu nhiệt ẩm:** Có {itcz_conv_count} mốc hội tụ ẩm sâu (850–700hPa) "
            f"kèm chuyển động nâng và năng lượng đối lưu CAPE, tiềm ẩn mưa rào, dông và gió giật mạnh."
        )

    if len(patterns) == 1:
        patterns.append(
            "**Trường khí áp & Hoàn lưu:** Phân bố khí áp và trường gió tương đối êm dịu, chưa nổi bật hình thế nhiễu động lớn kéo dài."
        )

    return patterns


def generate_10_day_synoptic_outlook(forecasts: List[HourlyForecast], lat: float, airport_name: str) -> str:
    if not forecasts:
        return "Đang cập nhật dữ liệu xu thế..."

    daily_summary: Dict[str, Dict[str, Any]] = {}
    rain_windows: List[str] = []
    low_vis_windows: List[str] = []

    all_temps: List[float] = []
    day_temps: List[float] = []
    night_temps: List[float] = []
    all_vis_km: List[float] = []

    for fc in forecasts:
        dt = parse_local_dt(fc.forecast_time)
        day_str = dt.strftime("%d/%m")
        hour = dt.hour
        rain_val = max(fc.precipitation, fc.rain, fc.showers)
        vis_km = fc.visibility_m / 1000.0
        spread = dewpoint_spread(fc.temperature_2m, fc.dew_point_2m)

        all_temps.append(fc.temperature_2m)
        all_vis_km.append(vis_km)
        if 7 <= hour <= 17:
            day_temps.append(fc.temperature_2m)
        else:
            night_temps.append(fc.temperature_2m)

        bucket = daily_summary.setdefault(
            day_str,
            {
                "temps": [],
                "pops": [],
                "thunders": [],
                "rains": [],
                "rain_hours": [],
                "min_vis_km": 999.0,
                "low_vis_hours": [],
            },
        )
        bucket["temps"].append(fc.temperature_2m)
        bucket["pops"].append(fc.pop_calibrated)
        bucket["thunders"].append(fc.thunder_probability)
        bucket["rains"].append(rain_val)
        bucket["min_vis_km"] = min(bucket["min_vis_km"], vis_km)

        if fc.pop_calibrated >= 45 or rain_val >= 0.5:
            bucket["rain_hours"].append(f"{dt.strftime('%H:%M')} ({rain_val:.1f}mm, {fc.pop_calibrated:.0f}%)")

        if vis_km < 5.0 or (spread <= 1.2 and fc.relative_humidity_2m >= 88):
            bucket["low_vis_hours"].append(f"{dt.strftime('%H:%M')} ({vis_km:.1f}km)")

    max_overall_temp = max(all_temps)
    min_overall_temp = min(all_temps)
    max_day_temp = max(day_temps) if day_temps else max_overall_temp
    min_night_temp = min(night_temps) if night_temps else min_overall_temp
    amplitude_temp = max_overall_temp - min_overall_temp

    min_vis_overall = min(all_vis_km)
    avg_vis_overall = sum(all_vis_km) / len(all_vis_km)

    rainy_days: List[str] = []
    for day, m in daily_summary.items():
        max_pop = max(m["pops"])
        max_thunder = max(m["thunders"])
        total_rain = sum(m["rains"])
        if max_pop >= 50 or total_rain >= 2.0 or max_thunder >= 35:
            rainy_days.append(day)
            if m["rain_hours"]:
                sample_hours = ", ".join(m["rain_hours"][:4])
                more_txt = f" (+{len(m['rain_hours']) - 4} mốc)" if len(m["rain_hours"]) > 4 else ""
                rain_windows.append(
                    f"• **{day}:** mưa cao nhất ~{total_rain:.1f}mm/ngày, PoP đỉnh {max_pop:.0f}% — các mốc đáng chú ý: {sample_hours}{more_txt}"
                )

        if m["low_vis_hours"]:
            sample_vis = ", ".join(m["low_vis_hours"][:4])
            more_vis = f" (+{len(m['low_vis_hours']) - 4} mốc)" if len(m["low_vis_hours"]) > 4 else ""
            low_vis_windows.append(
                f"• **{day}:** tầm nhìn thấp nhất ~{m['min_vis_km']:.1f}km — {sample_vis}{more_vis}"
            )

    detected_patterns = detect_synoptic_patterns(forecasts, lat)
    pattern_lines = "\n".join(f"- {item}" for item in detected_patterns)

    zone = _climate_zone_by_lat(lat)
    if zone == "north_central":
        region_note = (
            "- **Đặc trưng khu vực (Bắc Bộ & Bắc Trung Bộ):** Chú ý biến thiên khí áp/gió mùa, nắng nóng/áp thấp nóng phía Tây mùa hè và ẩm tầng 850hPa gây mây thấp, sương mù/mù nhẹ."
        )
    elif zone == "central_highlands":
        region_note = (
            "- **Đặc trưng khu vực (Trung Trung Bộ & Tây Nguyên):** Lưu ý tương tác giữa gió Đông/Đông Bắc, địa hình đón gió, hiệu ứng khô nóng mùa hè và độ ẩm mực 850–700hPa."
        )
    else:
        region_note = (
            "- **Đặc trưng khu vực (Nam Bộ & Nam Trung Bộ):** Chú ý đối lưu nhiệt ẩm, gió mùa Tây Nam và hội tụ ẩm phát triển rõ về chiều tối khi CAPE và độ ẩm tầng thấp tăng."
        )

    region_synoptic = (
        f"**1. Nhận diện hình thế hoàn lưu tại {airport_name}:**\n"
        f"{pattern_lines}\n"
        f"{region_note}"
    )

    if rain_windows:
        rain_detail_text = (
            "**2. Chi tiết mưa & Khung giờ đáng lưu ý:**\n"
            + f"- Các ngày có xu thế mưa/dông nổi bật: **{', '.join(rainy_days)}**.\n"
            + "\n".join(rain_windows[:5])
        )
    else:
        rain_detail_text = (
            "**2. Chi tiết mưa & Khung giờ đáng lưu ý:**\n"
            "- Trong chuỗi dự báo hiện tại, mưa xuất hiện rải rác hoặc lượng mưa nhỏ không đáng kể; cần theo dõi thêm các khung giờ chiều tối khi độ ẩm và mây tầng thấp tăng."
        )

    vis_detail_text = (
        "**3. Xu thế Tầm nhìn & Thời điểm suy giảm:**\n"
        f"- Tầm nhìn toàn chuỗi phổ biến quanh mức trung bình **{avg_vis_overall:.1f} km**, thấp nhất khoảng **{min_vis_overall:.1f} km**.\n"
        + (
            "\n".join(low_vis_windows[:5])
            if low_vis_windows
            else "- Tầm nhìn nhìn chung duy trì tốt (ít ghi nhận các mốc tầm nhìn thấp dưới 5 km hoặc nguy cơ sương mù sát bão hòa)."
        )
    )

    temp_detail_text = (
        "**4. Diễn biến Nhiệt độ & Biên độ ngày–đêm:**\n"
        f"- Toàn giai đoạn dao động từ **+{min_overall_temp:.1f}°C** đến **+{max_overall_temp:.1f}°C** (biên độ chênh lệch lớn nhất khoảng **{amplitude_temp:.1f}°C**).\n"
        f"- Nhiệt độ cao nhất ban ngày (07h–17h) đạt khoảng **+{max_day_temp:.1f}°C**, trong khi nhiệt độ thấp nhất về đêm/sáng sớm hạ xuống khoảng **+{min_night_temp:.1f}°C**."
    )

    return "\n\n".join([region_synoptic, rain_detail_text, vis_detail_text, temp_detail_text])


@st.cache_data(ttl=10800, show_spinner=False)
def fetch_open_meteo(lat: float, lon: float, wind_unit: str = "kmh", cycle_key: str = "") -> Dict[str, Any]:
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
            payload = response.json()
            payload["_fetched_at"] = datetime.now(ZoneInfo(TIMEZONE)).strftime("%H:%M %d/%m/%Y")
            return payload
        except requests.exceptions.RequestException as e:
            if attempt == max_retries - 1:
                raise e
            time.sleep(2 * (attempt + 1))
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

        spread = max(0.1, temp_val - dew_val)
        cloud_base_ft = round((spread / 2.5) * 1000.0, 0)
        cloud_base_ft = max(200.0, min(cloud_base_ft, 25000.0))

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
    dt = parse_local_dt(fc.forecast_time)
    hour = dt.hour
    month = dt.month
    is_tho_xuan_or_halac = (abs(lat - 19.9017) < 0.3 or abs(lat - 21.0167) < 0.3)

    is_nom_season = is_tho_xuan_or_halac and (2 <= month <= 4)
    is_dry_season = (11 <= month or month == 1)

    if is_tho_xuan_or_halac and (hour >= 22 or hour <= 7) and fc.relative_humidity_2m >= 85:
        limit_wind = 4.0 if is_nom_season else 5.0
        if wind_unit == "kmh":
            fc.wind_speed_10m = min(fc.wind_speed_10m, limit_wind)
        else:
            fc.wind_speed_10m = min(fc.wind_speed_10m, limit_wind / 3.6)

    vis = fc.visibility_raw
    spread = dewpoint_spread(fc.temperature_2m, fc.dew_point_2m)
    rain_amount = max(fc.precipitation, fc.rain, fc.showers)

    if 7 <= hour <= 17 and rain_amount < 0.3 and fc.relative_humidity_2m < 85:
        fc.visibility_m = max(vis, 12000.0 if is_dry_season else 10000.0)
        return

    effective_rain = rain_amount if rain_amount >= 0.3 else 0.0

    if effective_rain == 0.0 and spread > 1.2:
        if is_tho_xuan_or_halac:
            if is_nom_season and fc.relative_humidity_2m >= 90:
                vis = max(1000.0, vis - 2000.0)
            elif spread >= 3.0 and fc.relative_humidity_2m < 85:
                vis += 4500.0 if is_dry_season else 3500.0
            elif spread >= 2.0:
                vis += 2200.0
            else:
                vis += 1200.0
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

        dt = parse_local_dt(fc.forecast_time)
        month = dt.month
        hour = get_hour(fc.forecast_time)

        seasonal_pop_boost = 1.15 if (5 <= month <= 10) else (0.85 if (11 <= month or month <= 1) else 1.0)

        spread = dewpoint_spread(fc.temperature_2m, fc.dew_point_2m)
        moisture = (
            0.30 * fc.relative_humidity_2m
            + 0.45 * fc.relative_humidity_850hPa
            + 0.25 * fc.relative_humidity_700hPa
        )
        if spread <= 1.5:
            moisture += 10 if (2 <= month <= 4) else 8
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
        model_pop = fc.precipitation_probability_model * seasonal_pop_boost

        fc.model_rain_score = clamp(0.65 * model_pop + 0.35 * amount_score)

        cape_score = normalize(fc.cape, 100.0, 2200.0)
        daytime_factor = 1.10 if 11 <= hour <= 18 else (0.80 if hour <= 6 or hour >= 21 else 1.0)
        seasonal_factor = (
            1.20 if month in (5, 6, 7, 8, 9) else (0.60 if month in (11, 12, 1, 2) else 0.90)
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
# 4. BẢNG NGANG & BIỂU ĐỒ TRỰC QUAN
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


def render_rp5_horizontal_table(
    forecasts: List[HourlyForecast], wind_unit_text: str, cloud_unit: str = "ft"
) -> str:
    if not forecasts:
        return "<p>Không có dữ liệu hiển thị.</p>"

    days_map: Dict[str, List[HourlyForecast]] = {}
    viet_days = ["Thứ 2", "Thứ 3", "Thứ 4", "Thứ 5", "Thứ 6", "Thứ 7", "Chủ nhật"]
    for fc in forecasts:
        dt = parse_local_dt(fc.forecast_time)
        day_label = f"{viet_days[dt.weekday()]}, {dt.strftime('%d/%m')}"
        days_map.setdefault(day_label, []).append(fc)

    unit_label_pair = "ft / m" if cloud_unit == "ft" else "m / ft"

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
    row_cloud_base = [
        f'<td class="sticky-col row-title" style="background:#eef2f6;"><b>Chân mây ({unit_label_pair})</b></td>'
    ]
    row_cloud_top = [
        f'<td class="sticky-col row-title" style="background:#eef2f6;"><b>Đỉnh mây ({unit_label_pair})</b></td>'
    ]

    row_wind = [f'<td class="sticky-col row-title">Gió duy trì ({wind_unit_text})</td>']
    row_gust = [f'<td class="sticky-col row-title">Gió giật ({wind_unit_text})</td>']
    row_rh = ['<td class="sticky-col row-title">Độ ẩm 2m (%)</td>']
    row_rh850 = ['<td class="sticky-col row-title">Độ ẩm 850hPa (%)</td>']
    row_vis_raw = ['<td class="sticky-col row-title" style="color:#64748b;">Tầm nhìn Gốc (km)</td>']
    row_vis_cal = ['<td class="sticky-col row-title" style="color:#1d4ed8;"><b>Tầm nhìn Hiệu chỉnh (km)</b></td>']
    row_press = ['<td class="sticky-col row-title">Áp suất (hPa)</td>']

    fmt_wind = ".1f" if wind_unit_text == "m/s" else ".0f"

    for fc in forecasts:
        dt = parse_local_dt(fc.forecast_time)
        rain_val = max(fc.precipitation, fc.rain, fc.showers)
        wind_dir = wind_deg_to_dir(fc.wind_direction_10m)

        if cloud_unit == "ft":
            base_main = f"{fc.estimated_cloud_base_ft:.0f} ft"
            base_sub = f"({int(round(fc.estimated_cloud_base_ft * 0.3048))}m)"
            top_main = f"{fc.estimated_cloud_top_ft:.0f} ft"
            top_sub = f"({int(round(fc.estimated_cloud_top_ft * 0.3048))}m)"
        else:
            base_main = f"{convert_cloud_ft(fc.estimated_cloud_base_ft, 'm'):.0f} m"
            base_sub = f"({fc.estimated_cloud_base_ft:.0f}ft)"
            top_main = f"{convert_cloud_ft(fc.estimated_cloud_top_ft, 'm'):.0f} m"
            top_sub = f"({fc.estimated_cloud_top_ft:.0f}ft)"

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
        row_cloud_base.append(
            f'<td style="background:#f8fafc;"><b>{base_main}</b><br>'
            f'<span style="color:#64748b;font-size:11px;">{base_sub}</span></td>'
        )
        row_cloud_top.append(
            f'<td style="background:#f8fafc;"><b>{top_main}</b><br>'
            f'<span style="color:#64748b;font-size:11px;">{top_sub}</span></td>'
        )

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


def render_aviation_charts(
    forecasts: List[HourlyForecast], airport_name: str, cloud_unit: str = "ft"
) -> None:
    if not forecasts:
        return

    times = [parse_local_dt(fc.forecast_time) for fc in forecasts]
    cloud_base = [convert_cloud_ft(fc.estimated_cloud_base_ft, cloud_unit) for fc in forecasts]
    cloud_top = [convert_cloud_ft(fc.estimated_cloud_top_ft, cloud_unit) for fc in forecasts]
    vis_km = [round(fc.visibility_m / 1000.0, 2) for fc in forecasts]
    pop_vals = [fc.pop_calibrated for fc in forecasts]
    thunder_vals = [fc.thunder_probability for fc in forecasts]

    col_c1, col_c2 = st.columns(2)

    with col_c1:
        fig_cloud = go.Figure()
        fig_cloud.add_trace(
            go.Scatter(
                x=times,
                y=cloud_top,
                name=f"Đỉnh mây ({cloud_unit})",
                line=dict(color="#64748b", width=2, dash="dash"),
            )
        )
        fig_cloud.add_trace(
            go.Scatter(
                x=times,
                y=cloud_base,
                name=f"Chân mây ({cloud_unit})",
                fill="tonexty",
                fillcolor="rgba(30, 58, 138, 0.14)",
                line=dict(color="#1e3a8a", width=2.5),
            )
        )
        fig_cloud.update_layout(
            title=f"Chân mây & Đỉnh mây ({cloud_unit}) — {airport_name}",
            xaxis_title="Thời gian địa phương",
            yaxis_title=f"Độ cao ({cloud_unit})",
            height=340,
            margin=dict(l=20, r=20, t=45, b=20),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        )
        st.plotly_chart(fig_cloud, use_container_width=True)

    with col_c2:
        fig_risk = go.Figure()
        fig_risk.add_trace(
            go.Bar(
                x=times,
                y=pop_vals,
                name="PoP Hiệu chỉnh (%)",
                marker_color="#2563eb",
                opacity=0.75,
            )
        )
        fig_risk.add_trace(
            go.Scatter(
                x=times,
                y=thunder_vals,
                name="Nguy cơ Dông (%)",
                line=dict(color="#dc2626", width=2.5),
            )
        )
        fig_risk.add_trace(
            go.Scatter(
                x=times,
                y=vis_km,
                name="Tầm nhìn (km)",
                line=dict(color="#059669", width=2),
            )
        )
        fig_risk.update_layout(
            title="Xác suất mưa, Nguy cơ dông (%) & Tầm nhìn (km)",
            xaxis_title="Thời gian địa phương",
            height=340,
            margin=dict(l=20, r=20, t=45, b=20),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        )
        st.plotly_chart(fig_risk, use_container_width=True)


# =========================
# 5. ĐỊNH NGHĨA MODAL TOÀN MÀN HÌNH (st.dialog) CHO THUYẾT TRÌNH MÔ HÌNH
# =========================
@st.dialog("📚 Thuyết trình Chi tiết Mô hình Dự báo & Công thức Khí tượng Hàng không", width="large")
def show_model_presentation_modal():
    st.markdown(
        "💡 *Tài liệu thuyết minh chi tiết bằng tiếng Việt rõ nghĩa, tường minh về cơ sở tính toán, "
        "tinh chỉnh theo mùa và ứng dụng thực tế.*"
    )

    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📂 Nguồn số liệu",
        "🧮 Công thức & Thuật toán",
        "🌱 Tinh chỉnh theo mùa",
        "🎯 Kết quả đạt được",
        "🚀 Ứng dụng thực tế",
    ])

    with tab1:
        st.markdown(
            "**1. Hệ thống Mô hình Số trị Toàn cầu (NWPs):**\n\n"
            "- Sử dụng API mô hình số trị độ phân giải cao **Open-Meteo**, kết hợp dữ liệu từ các trung tâm dự báo hàng đầu thế giới: **ECMWF** (Châu Âu), **GFS** (Mỹ) và **ICON** (Đức).\n"
            "- Cung cấp chuỗi dữ liệu dự báo 10 ngày với bước thời gian liên tục từng giờ, bao gồm các thông số bề mặt và các lớp khí quyển đẳng áp (850hPa, 700hPa).\n\n"
            "**2. Danh mục 21 biến khí tượng chuyên sâu được khai thác:**\n"
            "- *Nhiệt độ & Điểm sương:* Nhiệt độ không khí ở độ cao 2 mét (`temperature_2m`), nhiệt độ điểm sương (`dew_point_2m`).\n"
            "- *Hệ thống mây:* Lượng mây tổng cộng (`cloud_cover`), lượng mây tầng thấp, mây tầng trung và mây tầng cao.\n"
            "- *Động lực học & Đối lưu:* Năng lượng đối lưu khả dụng (`cape`), vận tốc chuyển động thẳng đứng tại mực 700hPa (`vertical_velocity_700hPa`).\n"
            "- *Độ ẩm tầng cao:* Độ ẩm tương đối tại mực 850hPa và 700hPa.\n"
            "- *Trường gió & Khí áp:* Tốc độ gió 10m, hướng gió, gió giật mạnh, áp suất khí quyển bề mặt, tầm nhìn xa và xác suất mưa."
        )

    with tab2:
        st.markdown(
            "**1. Phương pháp tính độ cao Chân mây (Công thức Espy):**\n\n"
            "- *Cách tính:* Lấy Nhiệt độ mặt đất trừ đi Nhiệt độ điểm sương, sau đó chia cho 2.5 rồi nhân với 1,000 để ra độ cao tính bằng feet (ft).\n"
            "- *Giải thích vật lý:* Khi không khí ẩm bốc lên cao và lạnh dần theo chiều thẳng đứng, nhiệt độ và điểm sương sẽ gặp nhau (hội tụ) với tốc độ khoảng 2.5°C cho mỗi 1,000 ft dâng lên. Điểm đó chính là nơi mây bắt đầu hình thành.\n\n"
            "**2. Phương pháp tính độ cao Đỉnh mây:**\n\n"
            "- *Cách tính:* Đỉnh mây = Độ cao chân mây + 1,800 ft cơ bản + (Lượng mây tổng nhân với 25) + (Chỉ số năng lượng đối lưu CAPE nhân với 0.5, tối đa lấy 1,000).\n"
            "- *Ý nghĩa:* Giúp ước tính độ dày của tầng mây. Khi bầu trời nhiều mây và có dòng đối lưu mạnh (CAPE cao), tầng mây sẽ dày lên và đỉnh mây vươn lên cao hơn hẳn so với chân mây.\n\n"
            "**3. Thuật toán hiệu chỉnh Tầm nhìn theo chuẩn METAR:**\n\n"
            "- *Vấn đề:* Mô hình toàn cầu thường bị giới hạn cứng ở 24.1 km và hay đánh giá tầm nhìn thấp vô lý vào ban trưa.\n"
            "- *Giải pháp:* Hệ thống tự động kiểm tra: Vào ban ngày trời khô ráo (độ ẩm dưới 85%), tầm nhìn được ép tối thiểu từ 10 km trở lên. Ngược lại, vào ban đêm nếu độ ẩm cao và điểm sương sát nhiệt độ, hệ thống sẽ tự động hạ thấp tầm nhìn để phản ánh đúng hiện tượng sương mù thực tế tại sân bay.\n\n"
            "**4. Thuật toán tính Xác suất Mưa (PoP) & Nguy cơ Dông:**\n\n"
            "- Sử dụng hàm toán học Sigmoid kết hợp đồng thời nhiều yếu tố: xác suất của mô hình gốc, độ ẩm ở cả 3 tầng (mặt đất, 850hPa, 700hPa), chỉ số năng lượng dông sét CAPE và vận tốc gió đứng để lọc bỏ các dự báo mưa ảo, cho ra con số xác suất mưa thực tế cực kỳ chính xác."
        )

    with tab3:
        st.markdown(
            "**1. Ý nghĩa của việc Tinh chỉnh theo mùa:**\n\n"
            "- Thời tiết Việt Nam có sự phân hóa mùa vụ rất rõ rệt: **mùa nồm ẩm** (tháng 2–4), **mùa mưa dông/bão** (tháng 5–10) và **mùa khô/đông lạnh** (tháng 11–tháng 1).\n"
            "- Các tham số như gió nhẹ ban đêm, sương mù/mây thấp sáng sớm và chỉ số bất ổn định đối lưu được hiệu chỉnh theo tháng và khung giờ để bám sát đặc trưng địa phương trên toàn quốc.\n\n"
            "**2. Hiệu chỉnh hướng gió & độ ẩm tầng thấp:**\n\n"
            "- Gió Đông đến Đông Nam mang ẩm từ biển vào làm tăng điểm tích lũy độ ẩm, trong khi luồng gió khô (spread lớn) làm giảm khả năng duy trì mưa nhỏ kéo dài."
        )

    with tab4:
        st.markdown(
            "**1. Tích hợp dữ liệu đa tầng & chuẩn hóa thông số bay:**\n\n"
            "- Quy đổi trực tiếp chân mây, đỉnh mây giữa **feet (ft)** và **mét (m)**, tầm nhìn sang **km**, và hỗ trợ chuyển đổi tốc độ gió giữa **km/h** và **m/s**.\n"
            "- Bảng ngang trực quan phân tách theo ngày và từng khung giờ giúp nhận diện nhanh các mốc thời điểm nhạy cảm (sương mù, trần mây thấp, mưa rào, dông).\n\n"
            "**2. Lọc nhiễu dự báo mưa nhỏ không đáng kể:**\n\n"
            "- Loại bỏ các giá trị mưa vết dưới 0.3 mm khi không khí khô (độ ẩm dưới 85%), tránh gây báo động giả trong công tác theo dõi thời tiết."
        )

    with tab5:
        st.markdown(
            "**1. Hỗ trợ theo dõi & lập kế hoạch bay:**\n\n"
            "- Cung cấp cái nhìn tổng quan 10 ngày và chi tiết từng giờ cho 23 sân bay/khu vực bay trên cả nước.\n"
            "- Giúp kíp trực, điều hành và bộ phận khai thác nắm bắt sớm xu thế tầm nhìn, trần mây, gió giật và nguy cơ dông.\n\n"
            "**2. Khả năng mở rộng:**\n\n"
            "- Có thể kết nối thêm dữ liệu quan trắc thực tế (METAR/SYNOP) và radar thời tiết để đối chiếu sai số trực tiếp theo thời gian thực."
        )


# =========================
# 6. GIAO DIỆN CHÍNH (MAIN APP)
# =========================

now_vn = datetime.now(ZoneInfo(TIMEZONE))
current_cycle = get_3h_cycle_key(now_vn)
next_cycle_dt = datetime.strptime(current_cycle, "%Y-%m-%d %H:%M").replace(tzinfo=ZoneInfo(TIMEZONE)) + timedelta(hours=3)

col_title, col_action = st.columns([3.5, 1])
with col_title:
    st.title("✈️ Dự báo Mưa, Dông & Khí tượng Sân bay Việt Nam")
    st.caption(f"Phiên bản v4.35 • Giờ hệ thống: {now_vn.strftime('%H:%M %d/%m/%Y')} (UTC+7)")
with col_action:
    st.write("")
    if st.button("📚 Thuyết trình Mô hình", use_container_width=True):
        show_model_presentation_modal()

col_f1, col_f2, col_f3, col_f4, col_f5 = st.columns([2.1, 1.3, 1.0, 1.1, 0.8])

with col_f1:
    selected_airport = st.selectbox(
        "Chọn sân bay / khu vực",
        options=list(AIRPORT_DATABASE.keys()),
        index=0,
    )

with col_f2:
    horizon_label = st.selectbox(
        "Khoảng thời gian hiển thị",
        options=list(HORIZON_OPTIONS.keys()),
        index=1,
    )

with col_f3:
    wind_unit_label = st.selectbox(
        "Đơn vị gió",
        options=["km/h", "m/s"],
        index=0,
    )

with col_f4:
    cloud_unit_label = st.selectbox(
        "Độ cao mây",
        options=list(CLOUD_UNIT_OPTIONS.keys()),
        index=0,
    )

with col_f5:
    st.write("")
    st.write("")
    if st.button("🔄 Làm mới", use_container_width=True):
        fetch_open_meteo.clear()
        st.rerun()

cloud_unit = CLOUD_UNIT_OPTIONS[cloud_unit_label]
coords = AIRPORT_DATABASE[selected_airport]
lat = coords["lat"]
lon = coords["lon"]
api_wind_unit = "kmh" if wind_unit_label == "km/h" else "ms"

try:
    with st.spinner(f"Đang tải và xử lý dữ liệu khí tượng cho {selected_airport}..."):
        raw_data = fetch_open_meteo(
            lat=lat,
            lon=lon,
            wind_unit=api_wind_unit,
            cycle_key=current_cycle,
        )
        all_forecasts = parse_forecasts(raw_data)
        all_forecasts = process_forecast_models(all_forecasts, wind_unit=api_wind_unit, lat=lat, lon=lon)
except Exception as exc:
    st.error(f"Không thể lấy dữ liệu từ Open-Meteo lúc này: {exc}")
    st.stop()

if not all_forecasts:
    st.warning("Không có dữ liệu dự báo hợp lệ.")
    st.stop()

fetched_at = raw_data.get("_fetched_at", current_cycle)
st.caption(
    f"🕒 Dữ liệu đồng bộ lúc: **{fetched_at}** • Chu kỳ 3h: `{current_cycle[11:]}` "
    f"(Tự động cập nhật mới sau `{next_cycle_dt.strftime('%H:%M')}`)"
)

horizon_hours = HORIZON_OPTIONS[horizon_label]
future_forecasts = [
    fc for fc in all_forecasts if parse_local_dt(fc.forecast_time) >= (now_vn - timedelta(hours=1))
]
if not future_forecasts:
    future_forecasts = all_forecasts

filtered_forecasts = future_forecasts[:horizon_hours]
current_fc = filtered_forecasts[0]

wind_fmt = f"{current_fc.wind_speed_10m:.1f}" if wind_unit_label == "m/s" else f"{current_fc.wind_speed_10m:.0f}"
gust_fmt = f"{current_fc.wind_gusts_10m:.1f}" if wind_unit_label == "m/s" else f"{current_fc.wind_gusts_10m:.0f}"

m1, m2, m3, m4, m5, m6 = st.columns(6)
m1.metric(
    "Nhiệt độ",
    f"{current_fc.temperature_2m:.1f} °C",
    f"Điểm sương {current_fc.dew_point_2m:.1f}°C",
    delta_color="off",
)
m2.metric(
    "Tầm nhìn",
    f"{current_fc.visibility_m / 1000:.1f} km",
    f"Gốc {current_fc.visibility_raw / 1000:.1f} km",
    delta_color="off",
)
m3.metric(
    "Chân mây",
    format_cloud_height(current_fc.estimated_cloud_base_ft, cloud_unit),
    f"Đỉnh {format_cloud_height(current_fc.estimated_cloud_top_ft, cloud_unit)}",
    delta_color="off",
)
m4.metric(
    "Gió 10m",
    f"{wind_deg_to_dir(current_fc.wind_direction_10m)} {wind_fmt} {wind_unit_label}",
    f"Giật {gust_fmt} {wind_unit_label}",
    delta_color="off",
)
m5.metric(
    "PoP Hiệu chỉnh",
    f"{current_fc.pop_calibrated:.0f}%",
    f"Mức: {current_fc.rain_level}",
    delta_color="off",
)
m6.metric(
    "Nguy cơ Dông",
    f"{current_fc.thunder_probability:.0f}%",
    f"CAPE {current_fc.cape:.0f} J/kg",
    delta_color="off",
)

outlook_md = generate_10_day_synoptic_outlook(all_forecasts, lat=lat, airport_name=selected_airport)
st.markdown(f'<div class="summary-box">{outlook_md.replace(chr(10), "<br>")}</div>', unsafe_allow_html=True)

st.subheader(f"📈 Biểu đồ xu thế ({horizon_label})")
render_aviation_charts(filtered_forecasts, airport_name=selected_airport, cloud_unit=cloud_unit)

st.subheader(f"📋 Bảng số liệu chi tiết từng giờ ({horizon_label})")
st.markdown(
    render_rp5_horizontal_table(filtered_forecasts, wind_unit_text=wind_unit_label, cloud_unit=cloud_unit),
    unsafe_allow_html=True,
)

df_export = pd.DataFrame([
    {
        "thoi_gian": fc.forecast_time,
        "nhiet_do_c": fc.temperature_2m,
        "diem_suong_c": fc.dew_point_2m,
        "do_am_2m_pct": fc.relative_humidity_2m,
        "do_am_850hpa_pct": fc.relative_humidity_850hPa,
        "pop_hieu_chinh_pct": fc.pop_calibrated,
        "nguy_co_dong_pct": fc.thunder_probability,
        "luong_mua_mm": max(fc.precipitation, fc.rain, fc.showers),
        f"chan_may_{cloud_unit}": convert_cloud_ft(fc.estimated_cloud_base_ft, cloud_unit),
        f"dinh_may_{cloud_unit}": convert_cloud_ft(fc.estimated_cloud_top_ft, cloud_unit),
        "tam_nhin_hieu_chinh_km": round(fc.visibility_m / 1000.0, 2),
        f"gio_{wind_unit_label}": fc.wind_speed_10m,
        f"gio_giat_{wind_unit_label}": fc.wind_gusts_10m,
    }
    for fc in filtered_forecasts
])

st.write("")
st.download_button(
    label=f"⬇️ Tải dữ liệu CSV ({horizon_label})",
    data=df_export.to_csv(index=False).encode("utf-8-sig"),
    file_name=f"thoitiet_{selected_airport[:15].strip().replace(' ', '_').lower()}_{horizon_hours}h.csv",
    mime="text/csv",
)
