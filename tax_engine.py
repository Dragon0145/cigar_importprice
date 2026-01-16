from dataclasses import dataclass


def yen_round(x: float) -> int:
    return int(round(x))


def fx_to_yen(amount_foreign: float, fx_rate: float) -> int:
    return yen_round(amount_foreign * fx_rate)


@dataclass
class Breakdown:
    item_price_yen: int
    shipping_yen: int
    purchase_total_yen: int

    assessed_value_yen: int
    duty_vat_exempted: bool

    duty_yen: int
    tobacco_tax_yen: int
    vat_national_yen: int
    vat_local_yen: int
    customs_fee_yen: int

    total_weight_g: float

    taxes_and_fees_total_yen: int
    grand_total_yen: int
    per_stick_yen: int


def calculate(
    *,
    sticks: int,
    weight_g_per_stick: float,
    item_price_yen: int,
    shipping_yen: int,
    duty_rate: float,
    vat_national_rate: float = 0.078,
    vat_local_rate: float = 0.022,
    tobacco_tax_per_kg: int = 15244,
    assessed_ratio: float = 0.6,
    duty_vat_exempt_threshold_yen: int = 10_000,
    customs_fee_yen: int = 200,
) -> Breakdown:

    purchase_total_yen = int(item_price_yen + shipping_yen)

    assessed_value_yen = yen_round((item_price_yen + shipping_yen) * assessed_ratio)
    duty_vat_exempted = assessed_value_yen <= duty_vat_exempt_threshold_yen

    if duty_vat_exempted:
        duty_yen = 0
    else:
        duty_yen = yen_round(assessed_value_yen * duty_rate)

    total_weight_g = sticks * weight_g_per_stick
    total_weight_kg = total_weight_g / 1000.0
    tobacco_tax_yen = yen_round(total_weight_kg * tobacco_tax_per_kg)

    if duty_vat_exempted:
        vat_national_yen = 0
        vat_local_yen = 0
    else:
        vat_base = assessed_value_yen + duty_yen
        vat_national_yen = yen_round(vat_base * vat_national_rate)
        vat_local_yen = yen_round(vat_base * vat_local_rate)

    taxes_and_fees_total_yen = (
        duty_yen
        + tobacco_tax_yen
        + vat_national_yen
        + vat_local_yen
        + customs_fee_yen
    )

    grand_total_yen = purchase_total_yen + taxes_and_fees_total_yen
    per_stick_yen = yen_round(grand_total_yen / sticks) if sticks > 0 else 0

    return Breakdown(
        item_price_yen=item_price_yen,
        shipping_yen=shipping_yen,
        purchase_total_yen=purchase_total_yen,
        assessed_value_yen=assessed_value_yen,
        duty_vat_exempted=duty_vat_exempted,
        duty_yen=duty_yen,
        tobacco_tax_yen=tobacco_tax_yen,
        vat_national_yen=vat_national_yen,
        vat_local_yen=vat_local_yen,
        customs_fee_yen=customs_fee_yen,
        total_weight_g=total_weight_g,
        taxes_and_fees_total_yen=taxes_and_fees_total_yen,
        grand_total_yen=grand_total_yen,
        per_stick_yen=per_stick_yen,
    )
