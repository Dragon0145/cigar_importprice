import json
from pathlib import Path
from flask import Flask, render_template, request

from tax_engine import calculate, fx_to_yen
from fx_service import get_fx_rate

app = Flask(__name__)

# 税率データ
RATES_PATH = Path(__file__).parent / "rates.json"


def load_rates() -> dict:
    with open(RATES_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def parse_int(s: str, default: int = 0) -> int:
    try:
        return int(s)
    except Exception:
        return default


def parse_float(s: str, default: float = 0.0) -> float:
    try:
        return float(s)
    except Exception:
        return default


@app.get("/")
def index():
    rates = load_rates()
    return render_template("index.html", rates=rates)


@app.post("/calc")
def calc():
    rates = load_rates()
    errors = []

    # どのボタンが押されたか
    action = request.form.get("action", "calc_normal")

    # 本数・重量
    sticks = parse_int(request.form.get("sticks", "0"), 0)
    weight_g = parse_float(request.form.get("weight_g", "1.0"), 1.0)

    if sticks <= 0:
        errors.append("本数は1以上で入力してください。")
    if weight_g <= 0:
        errors.append("重量(g)は0より大きい値を入力してください。")

    # 通貨・為替
    currency = request.form.get("currency", "USD").upper().strip()
    fx_mode = request.form.get("fx_mode", "auto")

    # USD→JPYボタンが押されたら強制上書き
    if action == "calc_usd_jpy":
        currency = "USD"
        fx_mode = "auto"

    fx_rate_manual = parse_float(request.form.get("fx_rate_manual", "0"), 0.0)

    fx_rate = None
    fx_source = "manual"

    if fx_mode == "auto":
        fx_rate, fx_source = get_fx_rate(currency, "JPY")
        if fx_rate is None and fx_rate_manual > 0:
            fx_rate = fx_rate_manual
            fx_source = "manual_fallback"
    else:
        if fx_rate_manual > 0:
            fx_rate = fx_rate_manual
            fx_source = "manual"

    if fx_rate is None or fx_rate <= 0:
        errors.append(
            "為替レートを取得できませんでした。手入力レートを入力するか、時間をおいて再試行してください。"
        )

    # 外貨金額
    item_price_foreign = parse_float(request.form.get("item_price_foreign", "0"), 0.0)
    shipping_foreign = parse_float(request.form.get("shipping_foreign", "0"), 0.0)

    if item_price_foreign < 0 or shipping_foreign < 0:
        errors.append("商品価格・送料は0以上で入力してください。")

    if errors:
        return render_template("index.html", rates=rates, errors=errors), 400

    # 円換算
    item_price = fx_to_yen(item_price_foreign, fx_rate)
    shipping = fx_to_yen(shipping_foreign, fx_rate)

    # 関税率
    duty_rate = parse_float(
        request.form.get("duty_rate", str(rates["default_duty_rate"])),
        float(rates["default_duty_rate"]),
    )

    if duty_rate < 0 or duty_rate > 1:
        return render_template(
            "index.html",
            rates=rates,
            errors=["関税率は 0〜1 の範囲で入力してください（例: 0.16）"],
        ), 400

    # 税計算
    b = calculate(
        sticks=sticks,
        weight_g_per_stick=weight_g,
        item_price_yen=item_price,
        shipping_yen=shipping,
        duty_rate=duty_rate,
        vat_rate=float(rates["vat_rate"]),
        tobacco_tax_per_1000_equiv=int(rates["tobacco_tax_per_1000_equiv"]),
    )

    return render_template(
        "result.html",
        rates=rates,
        sticks=sticks,
        weight_g=weight_g,
        currency=currency,
        fx_rate=fx_rate,
        fx_source=fx_source,
        item_price_foreign=item_price_foreign,
        shipping_foreign=shipping_foreign,
        item_price=item_price,
        shipping=shipping,
        duty_rate=duty_rate,
        b=b,
    )


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)
