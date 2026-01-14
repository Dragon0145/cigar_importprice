from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP


@dataclass(frozen=True)
class Breakdown:
    cif_yen: int
    duty_yen: int
    tobacco_tax_yen: int
    import_vat_yen: int
    total_yen: int
    equiv_cigarettes: float


def _yen_round(x: Decimal) -> int:
    # 概算用：四捨五入
    return int(x.quantize(Decimal("1"), rounding=ROUND_HALF_UP))


def cigarette_equiv(sticks: int, weight_g_per_stick: float) -> float:
    """
    葉巻の紙巻換算（概算）
    - 1g = 紙巻1本
    - 1本1g未満なら 1本 = 紙巻1本
    """
    per = max(1.0, float(weight_g_per_stick))
    return sticks * per


def fx_to_yen(amount_foreign: float, fx_rate: float) -> int:
    """
    外貨 → 円（四捨五入）
    """
    a = Decimal(str(amount_foreign))
    r = Decimal(str(fx_rate))
    return _yen_round(a * r)


def calculate(
    sticks: int,
    weight_g_per_stick: float,
    item_price_yen: int,
    shipping_yen: int,
    duty_rate: float,
    vat_rate: float,
    tobacco_tax_per_1000_equiv: int,
) -> Breakdown:
    cif = Decimal(item_price_yen + shipping_yen)

    duty = cif * Decimal(str(duty_rate))

    equiv = Decimal(str(cigarette_equiv(sticks, weight_g_per_stick)))
    tobacco_tax = (equiv / Decimal("1000")) * Decimal(tobacco_tax_per_1000_equiv)

    vat_base = cif + duty + tobacco_tax
    import_vat = vat_base * Decimal(str(vat_rate))

    total = cif + duty + tobacco_tax + import_vat

    return Breakdown(
        cif_yen=_yen_round(cif),
        duty_yen=_yen_round(duty),
        tobacco_tax_yen=_yen_round(tobacco_tax),
        import_vat_yen=_yen_round(import_vat),
        total_yen=_yen_round(total),
        equiv_cigarettes=float(equiv),
    )
