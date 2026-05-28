"""
SAP Flat-File Parser
Handles pipe-delimited (|) or tab-delimited IDoc exports.
Maps German column headers to English, normalises units and dates.
"""
import io
import csv
from decimal import Decimal, InvalidOperation
from datetime import date

from apps.ingestion.normalizers.dates import parse_date
from apps.ingestion.normalizers.units import (
    normalise_energy,
    normalise_volume_to_litres,
    fuel_litres_to_kwh,
    natural_gas_m3_to_kwh,
)

# ---------------------------------------------------------------------------
# German → English header mapping (SAP standard field names)
# ---------------------------------------------------------------------------
HEADER_MAP = {
    'MANDT': 'client',
    'BUKRS': 'company_code',
    'WERKS': 'plant_code',
    'MATNR': 'material_number',
    'MENGE': 'quantity',
    'MEINS': 'unit',
    'NETWR': 'net_value',
    'WAERS': 'currency',
    'BLDAT': 'document_date',
    'MATKL': 'material_group',
    'BELNR': 'document_number',
    'GJAHR': 'fiscal_year',
    'LIFNR': 'vendor',
    'EBELN': 'purchase_order',
}

# ---------------------------------------------------------------------------
# Material-group → scope / category mapping
# ---------------------------------------------------------------------------
MATERIAL_GROUP_MAP = {
    'ROE': {'scope': 1, 'category': 'stationary_combustion', 'fuel': 'diesel'},
    'ROG': {'scope': 1, 'category': 'stationary_combustion', 'fuel': 'natural_gas'},
    'ROB': {'scope': 1, 'category': 'stationary_combustion', 'fuel': 'petrol'},
    'ROK': {'scope': 1, 'category': 'stationary_combustion', 'fuel': 'kerosene'},
    'ROL': {'scope': 1, 'category': 'stationary_combustion', 'fuel': 'lpg'},
}

# Material groups starting with 'ELE' → Scope 2 electricity
ELECTRICITY_PREFIXES = ('ELE', 'ELEK', 'STR')

# DEFRA 2023 emission factors (kgCO2e per kWh)
EMISSION_FACTORS = {
    'diesel':       {'factor': Decimal('0.25301'), 'source': 'DEFRA 2023'},
    'natural_gas':  {'factor': Decimal('0.18254'), 'source': 'DEFRA 2023'},
    'petrol':       {'factor': Decimal('0.22166'), 'source': 'DEFRA 2023'},
    'kerosene':     {'factor': Decimal('0.24667'), 'source': 'DEFRA 2023'},
    'lpg':          {'factor': Decimal('0.21445'), 'source': 'DEFRA 2023'},
    'electricity':  {'factor': Decimal('0.20700'), 'source': 'DEFRA 2023 UK Grid'},
}


def _detect_delimiter(first_line: str) -> str:
    """Detect whether the file uses pipe, tab, or comma as delimiter."""
    if '|' in first_line:
        return '|'
    if '\t' in first_line:
        return '\t'
    return ','


def _map_headers(raw_headers: list[str]) -> list[str]:
    """Map German SAP headers to English names."""
    return [HEADER_MAP.get(h.strip(), h.strip().lower()) for h in raw_headers]


def _classify_material_group(group_code: str) -> dict:
    """Determine scope, category, and fuel type from SAP material group code."""
    code = group_code.strip().upper()

    # Direct match
    if code in MATERIAL_GROUP_MAP:
        return MATERIAL_GROUP_MAP[code]

    # Electricity prefix
    for prefix in ELECTRICITY_PREFIXES:
        if code.startswith(prefix):
            return {'scope': 2, 'category': 'electricity', 'fuel': 'electricity'}

    # Unknown — default to Scope 1 generic
    return {'scope': 1, 'category': 'other_combustion', 'fuel': 'unknown'}


def parse_sap_file(file_content: bytes | str, filename: str = '') -> dict:
    """
    Parse an SAP flat-file export.

    Returns:
        {
            'records': [list of normalised row dicts],
            'errors': [list of {row: int, error: str}],
            'row_count': int
        }
    """
    if isinstance(file_content, bytes):
        file_content = file_content.decode('utf-8-sig')  # handle BOM

    lines = file_content.strip().splitlines()
    if len(lines) < 2:
        return {'records': [], 'errors': [{'row': 0, 'error': 'File has fewer than 2 lines'}], 'row_count': 0}

    delimiter = _detect_delimiter(lines[0])
    reader = csv.reader(io.StringIO(file_content), delimiter=delimiter)

    raw_headers = next(reader)
    headers = _map_headers(raw_headers)

    records = []
    errors = []

    for row_idx, raw_row in enumerate(reader, start=1):
        try:
            if not any(cell.strip() for cell in raw_row):
                continue  # skip blank lines

            row = dict(zip(headers, [c.strip() for c in raw_row]))
            raw_dict = dict(zip(raw_headers, [c.strip() for c in raw_row]))

            # Required fields
            quantity_str = row.get('quantity', '')
            unit_raw = row.get('unit', '')
            date_str = row.get('document_date', '')
            material_group = row.get('material_group', '')

            if not quantity_str or not unit_raw:
                errors.append({'row': row_idx, 'error': f'Missing quantity or unit: qty="{quantity_str}", unit="{unit_raw}"'})
                continue

            # Parse quantity
            try:
                quantity_raw = Decimal(quantity_str.replace(',', '.'))
            except (InvalidOperation, ValueError):
                errors.append({'row': row_idx, 'error': f'Invalid quantity: "{quantity_str}"'})
                continue

            # Parse date
            try:
                activity_date = parse_date(date_str)
            except ValueError:
                errors.append({'row': row_idx, 'error': f'Invalid date: "{date_str}"'})
                continue

            # Classify
            classification = _classify_material_group(material_group)
            scope = classification['scope']
            category = classification['category']
            fuel = classification['fuel']

            # Normalise quantity → kWh
            unit_key = unit_raw.upper().strip()
            if unit_key in ('L', 'LTR'):
                # Liquid fuel in litres → kWh
                kwh_value = fuel_litres_to_kwh(quantity_raw, fuel) if fuel != 'unknown' else quantity_raw
                unit_normalised = 'kWh'
            elif unit_key in ('M3', 'M³'):
                # Gas in m³ → kWh
                kwh_value = natural_gas_m3_to_kwh(quantity_raw)
                unit_normalised = 'kWh'
            elif unit_key in ('KWH', 'MWH', 'GWH', 'MJ', 'GJ'):
                kwh_value, unit_normalised = normalise_energy(quantity_raw, unit_raw)
            elif unit_key in ('KG', 'T', 'ST'):
                # Mass-based or piece count — keep as-is, no energy conversion
                kwh_value = quantity_raw
                unit_normalised = unit_raw
            else:
                kwh_value, unit_normalised = normalise_energy(quantity_raw, unit_raw)

            # Apply emission factor
            ef_info = EMISSION_FACTORS.get(fuel, {})
            ef = ef_info.get('factor')
            ef_source = ef_info.get('source', '')
            co2e_kg = (kwh_value * ef).quantize(Decimal('0.0001')) if ef else None

            records.append({
                'source_row_index': row_idx,
                'source_row_raw': raw_dict,
                'activity_date': activity_date,
                'period_start': activity_date.replace(day=1),
                'period_end': activity_date,
                'scope': scope,
                'category': category,
                'subcategory': fuel,
                'quantity_raw': quantity_raw,
                'unit_raw': unit_raw,
                'quantity_normalised': kwh_value,
                'unit_normalised': unit_normalised,
                'emission_factor': ef,
                'emission_factor_source': ef_source,
                'co2e_kg': co2e_kg,
                'metadata': {
                    'plant_code': row.get('plant_code', ''),
                    'material_number': row.get('material_number', ''),
                    'company_code': row.get('company_code', ''),
                    'net_value': row.get('net_value', ''),
                    'currency': row.get('currency', ''),
                },
            })

        except Exception as e:
            errors.append({'row': row_idx, 'error': str(e)})

    return {
        'records': records,
        'errors': errors,
        'row_count': len(records),
    }
