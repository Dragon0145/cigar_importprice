import json
import os
from datetime import date
import requests

CACHE_FILE = "fx_cache.json"
API_URL = "https://api.frankfurter.dev/v1/latest"

def _today_str() -> str:
    return date.today().isoformat()

def _load_cache() -> dict:
    if not os.path.exists(CACHE_FILE):
        return {}
    try:
        with open(CACHE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}

def _save_cache(data: dict) -> None:
    with open(CACHE_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def get_fx_info(from_ccy: str, to_ccy: str = "JPY") -> dict:
    """
    戻り値: {"rate": float, "date": "YYYY-MM-DD", "source": "frankfurter"}
    当日キャッシュがあればそれを返し、なければ取得して保存する。
    """
    from_ccy = from_ccy.upper()
    to_ccy = to_ccy.upper()
    key = f"{from_ccy}_{to_ccy}"
    today = _today_str()

    cache = _load_cache()
    if key in cache and cache[key].get("date") == today:
        return {
            "rate": float(cache[key]["rate"]),
            "date": cache[key]["date"],
            "source": cache[key].get("source", "frankfurter"),
        }

    params = {"base": from_ccy, "symbols": to_ccy}
    r = requests.get(API_URL, params=params, timeout=10)
    r.raise_for_status()
    payload = r.json()

    rate = float(payload["rates"][to_ccy])
    fx_date = payload.get("date", today)

    cache[key] = {"date": fx_date, "rate": rate, "source": "frankfurter"}
    _save_cache(cache)

    return {"rate": rate, "date": fx_date, "source": "frankfurter"}

def get_fx_rate(from_ccy: str, to_ccy: str = "JPY") -> float:
    return float(get_fx_info(from_ccy, to_ccy)["rate"])
