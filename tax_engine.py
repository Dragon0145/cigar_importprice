from dataclasses import dataclass


def yen_round(x: float) -> int:
    """円単位の四捨五入"""
    return int(round(x))


def fx_to_yen(amount_foreign: float, fx_rate: float) -> int:
    """外貨→円"""
    return yen_round(amount_foreign * fx_rate)


@dataclass
class Breakdown:
    # 入力・表示用（円）
    item_price_yen: int
    shipping_yen: int
    purchase_total_yen: int  # 商品+送料

    # 課税前提
    assessed_value_yen: int
    duty_vat_exempted: bool

    # 税金・手数料（円）
    duty_yen: int
    tobacco_tax_yen: int
    vat_national_yen: int
    vat_local_yen: int
    customs_fee_yen: int

    # 重量表示用
    total_weight_g: float

    # 合計（円）
    taxes_and_fees_total_yen: int   # 税金+通関料の合計
    grand_total_yen: int            # 購入金額(商品+送料)+税金+通関料
    per_stick_yen: int              # 1本あたり（四捨五入）


def calculate(
    *,
    sticks: int,
    weight_g_per_stick: float,
    item_price_yen: int,
    shipping_yen: int,
    duty_rate: float,
    vat_national_rate: float = 0.078,
    vat_local_rate: float = 0.022,
    tobacco_tax_per_kg: int = 15244,   # 1kgあたり
    assessed_ratio: float = 0.6,
    duty_vat_exempt_threshold_yen: int = 10_000,
    customs_fee_yen: int = 200,
) -> Breakdown:
    """
    ・関税・輸入消費税：商品価格×0.6、1万円以下は免税
    ・たばこ税：重量課税（1kgあたり15,244円）
    ・消費税：課税価格 + 関税 をベース（たばこ税は含めない）
    ・合計は「商品+送料+税金+通関料」
    ・1本あたり = 合計 / 本数
    """
    # 購入金額（商品+送料）
    purchase_total_yen = int(item_price_yen + shipping_yen)

    # 課税価格（関税・消費税の判定用）
assessed_value_yen = yen_round((item_price_yen + shipping_yen) * assessed_ratio)
    duty_vat_exempted = assessed_value_yen <= duty_vat_exempt_threshold_yen

    # 関税
    if duty_vat_exempted:
        duty_yen = 0
    else:
        duty_yen = yen_round(assessed_value_yen * duty_rate)

    # たばこ税（重量課税）
    total_weight_g = sticks * weight_g_per_stick
    total_weight_kg = total_weight_g / 1000.0
    tobacco_tax_yen = yen_round(total_weight_kg * tobacco_tax_per_kg)

    # 輸入消費税（国・地方）※たばこ税を含めない
    if duty_vat_exempted:
        vat_national_yen = 0
        vat_local_yen = 0
    else:
        vat_base = assessed_value_yen
vat_national_yen = yen_round(vat_base * vat_national_rate)
vat_local_yen = yen_round(vat_base * vat_local_rate)

    # 税金+手数料 合計
    taxes_and_fees_total_yen = (
        duty_yen + tobacco_tax_yen + vat_national_yen + vat_local_yen + int(customs_fee_yen)
    )

    # 本当の合計（購入金額+税金+通関料）
    grand_total_yen = purchase_total_yen + taxes_and_fees_total_yen

    # 1本あたり（四捨五入）
    per_stick_yen = yen_round(grand_total_yen / sticks) if sticks > 0 else 0

    return Breakdown(
        item_price_yen=int(item_price_yen),
        shipping_yen=int(shipping_yen),
        purchase_total_yen=purchase_total_yen,
        assessed_value_yen=assessed_value_yen,
        duty_vat_exempted=duty_vat_exempted,
        duty_yen=duty_yen,
        tobacco_tax_yen=tobacco_tax_yen,
        vat_national_yen=vat_national_yen,
        vat_local_yen=vat_local_yen,
        customs_fee_yen=int(customs_fee_yen),
        total_weight_g=float(total_weight_g),
        taxes_and_fees_total_yen=taxes_and_fees_total_yen,
        grand_total_yen=grand_total_yen,
        per_stick_yen=per_stick_yen,
    )
