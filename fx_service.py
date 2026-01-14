import json
from pathlib import Path
from datetime import date
import requests

CACHE_PATH = Path(__file__).parent / "fx_cache.json"


def _load_cache() -> dict:
    if CACHE_PATH.exists():
        try:
            return json.loads(CACHE_PATH.read_text(encoding="utf-8"))
        except Exception:
            return {}
    return {}


def _save_cache(data: dict) -> None:
    CACHE_PATH.write_text(
        json.dumps(data, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )


def get_fx_rate(from_ccy: str, to_ccy: str):
    """
    Frankfurter API（無料・APIキー不要）
    戻り値: (rate or None, source_string)
    """
    from_ccy = from_ccy.upper().strip()
    to_ccy = to_ccy.upper().strip()
    today = date.today().isoformat()
    key = f"{from_ccy}->{to_ccy}"

    cache = _load_cache()
    if cache.get("date") == today and key in cache.get("rates", {}):
        return float(cache["rates"][key]), "cache"

    url = "https://api.frankfurter.app/latest"
    try:
        r = requests.get(
            url,
            params={"from": from_ccy, "to": to_ccy},
            timeout=6
        )
        r.raise_for_status()
        data = r.json()
        rate = data["rates"][to_ccy]
    except Exception:
        return None, "unavailable"

    cache.setdefault("rates", {})
    cache["date"] = today
    cache["rates"][key] = rate
    _save_cache(cache)

    return float(rate), "frankfurter"
