import json
from pathlib import Path

from flask import Flask, render_template, request

from tax_engine import calculate, fx_to_yen
try:
    from fx_service import get_fx_rate
except Exception:
    get_fx_rate = None

APP_DIR = Path(__file__).parent
RATES_PATH = APP_DIR / "rates.json"

app = Flask(__name__)


def load_rates() -> dict:
    return json.loads(RATES_PATH.read_text(encoding="utf-8"))


def _parse_float(name: str, default=None):
    v = request.form.get(name, "").strip()
    if v == "":
        return default
    return float(v)


def _parse_int(name: str):
    v = request.form.get(name, "").strip()
    return int(v)


@app.get("/")
def index():
    rates = load_rates()
    return render_template("index.html", rates=rates, errors=[])


@app.post("/calc")
def calc():
    rates = load_rates()
    errors = []

    # 入力値
    try:
        sticks = _parse_int("sticks")
        weight_g = float(request.form.get("weight_g", "0"))
        currency = (request.form.get("currency", "USD") or "USD").upper().strip()

        item_price_foreign = float(request.form.get("item_price_foreign", "0"))
        shipping_foreign = float(request.form.get("shipping_foreign", "0"))

        duty_rate = float(request.form.get("duty_rate", rates.get("default_duty_rate", 0.16)))
    except Exception:
        errors.append("入力値の形式が正しくありません。数字を確認してください。")
        return render_template("index.html", rates=rates, errors=errors), 400

    # 入力チェック
    if sticks <= 0:
        errors.append("本数は1以上で入力してください。")
    if weight_g <= 0:
        errors.append("重量(g)は0より大きい値で入力してください。")
    if item_price_foreign < 0 or shipping_foreign < 0:
        errors.append("商品価格・送料は0以上で入力してください。")
    if not (0 <= duty_rate <= 1):
        errors.append("関税率は 0〜1 の範囲で入力してください（例: 0.16）。")

    if errors:
        return render_template("index.html", rates=rates, errors=errors), 400

    # 為替：基本は自動取得。失敗したら手入力があればそれを使う。
    fx_source = "auto"
    fx_rate = None

    # JPYの場合はレート1固定
    if currency == "JPY":
        fx_rate = 1.0
        fx_source = "fixed"
    else:
        if get_fx_rate is not None:
            fx_rate, source = get_fx_rate(currency, "JPY")
            fx_source = source

        if fx_rate is None:
            fx_rate_manual = _parse_float("fx_rate_manual", default=None)
            if fx_rate_manual is None:
                errors.append(
                    "為替レートの自動取得に失敗しました。少し時間をおいて再実行するか、詳細設定で為替レートを手入力してください。"
                )
                return render_template("index.html", rates=rates, errors=errors), 503
            fx_rate = fx_rate_manual
            fx_source = "manual"

    # 円換算
    item_price_yen = fx_to_yen(item_price_foreign, fx_rate)
    shipping_yen = fx_to_yen(shipping_foreign, fx_rate)

    # 税計算
    vat_rate = float(rates.get("vat_rate", 0.10))
    tobacco_tax_per_1000_equiv = int(rates.get("tobacco_tax_per_1000_equiv", 15244))

    b = calculate(
        sticks=sticks,
        weight_g_per_stick=weight_g,
        item_price_yen=item_price_yen,
        shipping_yen=shipping_yen,
        duty_rate=duty_rate,
        vat_rate=vat_rate,
        tobacco_tax_per_1000_equiv=tobacco_tax_per_1000_equiv,
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
        item_price=item_price_yen,
        shipping=shipping_yen,
        duty_rate=duty_rate,
        b=b,
    )


if __name__ == "__main__":
    # ローカル開発用
    app.run(debug=True)
