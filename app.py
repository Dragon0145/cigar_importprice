from flask import Flask, render_template, request
from tax_engine import calculate, fx_to_yen
from fx_service import get_fx_info
import json
import os

app = Flask(__name__)

# 税率などの設定読み込み
RATES_FILE = "rates.json"

def load_rates():
    if not os.path.exists(RATES_FILE):
        return {
            "default_duty_rate": 0.16,
            "updated_at": "N/A"
        }
    with open(RATES_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

rates = load_rates()

@app.route("/", methods=["GET"])
def index():
    return render_template(
        "index.html",
        rates=rates
    )

@app.route("/calc", methods=["POST"])
def calc():
    errors = []

    try:
        sticks = int(request.form.get("sticks", 0))
        weight_g = float(request.form.get("weight_g", 0))
        currency = request.form.get("currency")

        item_price_foreign = float(request.form.get("item_price_foreign", 0))
        shipping_foreign = float(request.form.get("shipping_foreign", 0))

        duty_rate = float(request.form.get("duty_rate", rates["default_duty_rate"]))
        fx_rate_manual = request.form.get("fx_rate_manual", "").strip()

        if sticks <= 0:
            errors.append("本数は1以上を入力してください。")
        if weight_g <= 0:
            errors.append("重量は正の値を入力してください。")
        if not currency:
            errors.append("通貨を選択してください。")

        # 為替レート取得（手入力があれば優先、なければ自動）
        fx_date = None
        if fx_rate_manual:
            fx_rate = float(fx_rate_manual)
            fx_source = "手入力"
        else:
            info = get_fx_info(currency, "JPY")
            fx_rate = info["rate"]
            fx_date = info["date"]
            fx_source = f"自動（{info.get('source','frankfurter')}）"

        if fx_rate <= 0:
            errors.append("為替レートが不正です。")

    except Exception as e:
        errors.append(f"入力エラー: {type(e).__name__}: {e}")

    if errors:
        return render_template(
            "index.html",
            errors=errors,
            rates=rates
        )

    # 円換算
    item_price_yen = fx_to_yen(item_price_foreign, fx_rate)
    shipping_yen = fx_to_yen(shipping_foreign, fx_rate)

    # 税計算
    b = calculate(
        sticks=sticks,
        weight_g_per_stick=weight_g,
        item_price_yen=item_price_yen,
        shipping_yen=shipping_yen,
        duty_rate=duty_rate,
        tobacco_tax_per_kg=15244,
        vat_national_rate=0.078,
        vat_local_rate=0.022,
        customs_fee_yen=200,
    )

    return render_template(
        "result.html",
        sticks=sticks,
        weight_g=weight_g,
        currency=currency,
        fx_rate=fx_rate,
        fx_date=fx_date,
        fx_source=fx_source,
        item_price_foreign=item_price_foreign,
        shipping_foreign=shipping_foreign,
        duty_rate=duty_rate,
        b=b,
        rates=rates
    )

if __name__ == "__main__":
    app.run(debug=True)
