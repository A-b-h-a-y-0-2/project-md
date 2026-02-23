# import math
# import requests
# from urllib.parse import quote
# from geopy.geocoders import Nominatim
# from geopy.extra.rate_limiter import RateLimiter
# from .utils import (pin_to_city_state, dealers_in, haversine)# ---------- utilities ------------------------------------------------------
# from typing import Optional, Dict

# # ---------- simple “map tool” ---------------------------------------------

# _geocoder = Nominatim(user_agent="hrj-map-tool")
# _geocode  = RateLimiter(_geocoder.geocode)

# def find_nearest_retailer(user_pin: str):
#     """
#     Return the JSON dict of the closest dealer to `user_pin`,
#     or None if nothing can be found.
#     Args: user_pin (str): The pincode of the user to find the nearest retailer.
#     Returns: dict | None: The dealer information with distance or None if not found.
#     """
#     city_state = pin_to_city_state(user_pin)
#     if not city_state:
#         print("Invalid or unknown pincode")
#         return None
#     city, state = city_state

#     dealers = dealers_in(city, state)
#     if not dealers:
#         print(f"No dealers listed for {city}, {state}")
#         return None

#     # geocode user's pin once
#     u_loc = _geocode(f"{user_pin}, India", exactly_one=True, timeout=5)
#     if not u_loc:
#         print("Could not geolocate user pin")
#         return None

#     best, best_d = None, 1e9
#     for d in dealers:
#         query = f"{d.get('pincode','')} India" if d.get("pincode") else d["address"]
#         loc   = _geocode(query, exactly_one=True, timeout=5)
#         if not loc:
#             continue
#         dist = haversine(u_loc.latitude, u_loc.longitude, loc.latitude, loc.longitude)
#         if dist < best_d:
#             best, best_d = d, dist

#     if best:
#         best["distance_km"] = round(best_d, 1)
#     return best




from pathlib import Path
from functools import lru_cache
from typing import List, Dict
from google.adk.tools import FunctionTool
import pandas as pd

# ── CONFIG ────────────────────────────────────────────────────────────────
# Robustly locate the Excel file
try:                                   # running as a .py script
    BASE_DIR = Path(__file__).parent
except NameError:                      # running in a notebook / REPL
    BASE_DIR = Path.cwd()

EXCEL_PATH = BASE_DIR / "Dealer address.xlsx"   # adjust filename if needed



# ── STATE CODE ↔ NAME MAP (extend as needed) ──────────────────────────────
_STATE_CODE_MAP = {
    # 2–3-letter codes → canonical full names
    "AN":  "Andaman & Nicobar Islands",
    "AP":  "Andhra Pradesh",
    "ARP": "Arunachal Pradesh",
    "AS":  "Assam",
    "BH":  "Bihar",
    "CG":  "Chhattisgarh",
    "CH":  "Chandigarh",
    "DD":  "Daman & Diu",
    "DL":  "Delhi",
    "GA":  "Goa",
    "GJ":  "Gujarat",
    "HP":  "Himachal Pradesh",
    "HR":  "Haryana",
    "JK":  "Jammu & Kashmir",
    "JH":  "Jharkhand",
    "KA":  "Karnataka",
    "KL":  "Kerala",
    "LD":  "Lakshadweep",
    "MH":  "Maharashtra",
    "MP":  "Madhya Pradesh",
    "MN":  "Manipur",
    "ML":  "Meghalaya",
    "MZ":  "Mizoram",
    "NL":  "Nagaland",
    "OD":  "Odisha",
    "PB":  "Punjab",
    "PY":  "Puducherry",
    "RJ":  "Rajasthan",
    "SK":  "Sikkim",
    "TN":  "Tamil Nadu",
    "TS":  "Telangana",
    "TR":  "Tripura",
    "UP":  "Uttar Pradesh",
    "UK":  "Uttarakhand",
    "WB":  "West Bengal",
}

# Reverse map: full name (casefolded) → code
_NAME_TO_CODE = {name.casefold(): code for code, name in _STATE_CODE_MAP.items()}

# ── INTERNAL HELPERS ──────────────────────────────────────────────────────
def _normalise_state(user_input: str) -> str:
    """
    Accept either a state *code* ("UP") or full name ("Uttar Pradesh")
    and return the canonical code used in the Excel sheet.
    """
    s = user_input.strip()
    code = s.upper()
    if code in _STATE_CODE_MAP:           # already a code
        return code
    key = s.casefold()
    if key in _NAME_TO_CODE:              # full name given
        return _NAME_TO_CODE[key]
    raise ValueError(
        f"Unknown state '{user_input}'. "
        f"Accepted codes: {', '.join(sorted(_STATE_CODE_MAP))}"
    )

@lru_cache(maxsize=1)
def _load_df() -> pd.DataFrame:
    """
    Read the Excel file once, standardise column names,
    trim whitespace, and cache the DataFrame in memory.
    """
    df = pd.read_excel(EXCEL_PATH)

    df = df.rename(
        columns={
            "Region":      "state",        # code in your sheet
            "City":        "city",
            "Name":        "dealer_name",
            "Address":     "address",
            "Postal Code": "postal_code",
            "Tel":         "phone",
        }
    )

    for col in ("state", "city", "dealer_name"):
        df[col] = df[col].astype(str).str.strip()

    return df

# ── PUBLIC API ────────────────────────────────────────────────────────────
def states() -> List[str]:
    """
    Return all distinct *codes* present in the sheet.
    """
    return sorted(_load_df()["state"].unique())

def cities_with_dealers(state: str) -> List[str]:
    """
    List every city that has ≥1 dealer in the given state.
    *state* may be code ("UP") or full name ("Uttar Pradesh").
    """
    code = _normalise_state(state)
    df   = _load_df()
    return sorted(df.loc[df["state"] == code, "city"].unique())

def dealers_in(city: str, state: str) -> List[Dict]:
    """
    Return dealers for (city, state) as list[dict].
    *state* may be code or full name; city match is case-insensitive.
    """
    code = _normalise_state(state)
    df   = _load_df()
    mask = (df["state"] == code) & (df["city"].str.casefold() == city.casefold())
    cols = ["dealer_name", "address", "postal_code", "phone"]
    return df.loc[mask, cols].to_dict(orient="records")

map_tool = FunctionTool(
    func=dealers_in)

