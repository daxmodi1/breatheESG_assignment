"""
Unit normalisation utilities.
Converts domain-specific units to a standard base (kWh for energy, km for distance).
"""
from decimal import Decimal, ROUND_HALF_UP

# ---------------------------------------------------------------------------
# Energy conversions → kWh
# ---------------------------------------------------------------------------
ENERGY_TO_KWH = {
    'kwh':   Decimal('1'),
    'mwh':   Decimal('1000'),
    'gwh':   Decimal('1000000'),
    'mj':    Decimal('0.277778'),        # 1 MJ = 0.277778 kWh
    'gj':    Decimal('277.778'),
    'therm': Decimal('29.3001'),
    'therms': Decimal('29.3001'),
    'ccf':   Decimal('29.3001'),         # 1 CCF ≈ 1 therm
    'mmbtu': Decimal('293.071'),
    'kvah':  Decimal('1'),               # treat kVAh ≈ kWh (power-factor adjusted later)
}

# ---------------------------------------------------------------------------
# Volume conversions → litres
# ---------------------------------------------------------------------------
VOLUME_TO_LITRES = {
    'l':    Decimal('1'),
    'ltr':  Decimal('1'),
    'litre': Decimal('1'),
    'litres': Decimal('1'),
    'm3':   Decimal('1000'),
    'm³':   Decimal('1000'),
    'gal':  Decimal('3.78541'),          # US gallon
}

# ---------------------------------------------------------------------------
# Fuel density (litres → kWh via combustion energy content)
# ---------------------------------------------------------------------------
FUEL_KWH_PER_LITRE = {
    'diesel':  Decimal('10.0'),          # ~10 kWh/L
    'petrol':  Decimal('9.5'),
    'gasoline': Decimal('9.5'),
    'lpg':     Decimal('7.1'),
    'kerosene': Decimal('10.4'),
}

# Natural gas: 1 m³ ≈ 10.55 kWh
NATURAL_GAS_KWH_PER_M3 = Decimal('10.55')


def normalise_energy(value: Decimal, unit: str) -> tuple[Decimal, str]:
    """Convert any energy unit to kWh. Returns (value_kwh, 'kWh')."""
    key = unit.lower().strip()
    factor = ENERGY_TO_KWH.get(key)
    if factor is None:
        raise ValueError(f"Unknown energy unit: '{unit}'")
    return (value * factor).quantize(Decimal('0.000001'), rounding=ROUND_HALF_UP), 'kWh'


def normalise_volume_to_litres(value: Decimal, unit: str) -> Decimal:
    """Convert volume units to litres."""
    key = unit.lower().strip()
    factor = VOLUME_TO_LITRES.get(key)
    if factor is None:
        raise ValueError(f"Unknown volume unit: '{unit}'")
    return (value * factor).quantize(Decimal('0.000001'), rounding=ROUND_HALF_UP)


def fuel_litres_to_kwh(litres: Decimal, fuel_type: str) -> Decimal:
    """Convert fuel volume (litres) to energy (kWh)."""
    key = fuel_type.lower().strip()
    factor = FUEL_KWH_PER_LITRE.get(key)
    if factor is None:
        raise ValueError(f"Unknown fuel type: '{fuel_type}'")
    return (litres * factor).quantize(Decimal('0.000001'), rounding=ROUND_HALF_UP)


def natural_gas_m3_to_kwh(m3: Decimal) -> Decimal:
    """Convert natural gas volume (m³) to energy (kWh)."""
    return (m3 * NATURAL_GAS_KWH_PER_M3).quantize(Decimal('0.000001'), rounding=ROUND_HALF_UP)


def normalise_distance(value: Decimal, unit: str) -> tuple[Decimal, str]:
    """Convert distance to km."""
    key = unit.lower().strip()
    factors = {
        'km': Decimal('1'),
        'mi': Decimal('1.60934'),
        'mile': Decimal('1.60934'),
        'miles': Decimal('1.60934'),
        'nm': Decimal('1.852'),  # nautical miles
    }
    factor = factors.get(key)
    if factor is None:
        raise ValueError(f"Unknown distance unit: '{unit}'")
    return (value * factor).quantize(Decimal('0.000001'), rounding=ROUND_HALF_UP), 'km'
