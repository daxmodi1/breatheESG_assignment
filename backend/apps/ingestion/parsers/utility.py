"""
Utility CSV Parser — Green Button / portal CSV exports.
Normalises billing periods, units, and calculates Scope 2 emissions.
"""
import io, csv
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from datetime import date
from apps.ingestion.normalizers.dates import parse_date
from apps.ingestion.normalizers.units import normalise_energy

ELECTRICITY_EF = Decimal('0.20700')
ELECTRICITY_EF_SOURCE = 'DEFRA 2023 UK Grid'


def _pro_rate(quantity, period_start, period_end):
    if period_start.year == period_end.year and period_start.month == period_end.month:
        return [{'period_start': period_start, 'period_end': period_end,
                 'quantity': quantity, 'activity_date': period_start}]
    total_days = (period_end - period_start).days
    if total_days <= 0:
        return [{'period_start': period_start, 'period_end': period_end,
                 'quantity': quantity, 'activity_date': period_start}]
    result, current = [], period_start
    while current <= period_end:
        month_end = date(current.year + (1 if current.month == 12 else 0),
                         1 if current.month == 12 else current.month + 1, 1)
        chunk_end = min(month_end, period_end)
        days = (chunk_end - current).days + (1 if chunk_end == period_end else 0)
        pro_rated = (quantity * Decimal(days) / Decimal(total_days)).quantize(
            Decimal('0.000001'), rounding=ROUND_HALF_UP)
        result.append({'period_start': current, 'period_end': chunk_end,
                       'quantity': pro_rated, 'activity_date': current})
        current = month_end
        if current > period_end:
            break
    return result


def parse_utility_file(file_content, filename=''):
    if isinstance(file_content, bytes):
        file_content = file_content.decode('utf-8-sig')
    reader = csv.DictReader(io.StringIO(file_content))
    if reader.fieldnames:
        reader.fieldnames = [h.strip().lower().replace(' ', '_').replace('-', '_') for h in reader.fieldnames]
    records, errors = [], []
    for row_idx, row in enumerate(reader, start=1):
        try:
            raw_dict = dict(row)
            qty_str = row.get('quantity') or row.get('usage') or row.get('consumption') or ''
            unit_raw = row.get('unit') or row.get('uom') or 'kWh'
            start_str = row.get('period_start') or row.get('start_date') or row.get('billing_start') or ''
            end_str = row.get('period_end') or row.get('end_date') or row.get('billing_end') or ''
            meter_id = row.get('meter_id') or row.get('meter') or ''
            site_name = row.get('site_name') or row.get('site') or row.get('facility') or ''
            tariff = row.get('tariff_code') or row.get('tariff') or ''
            if not qty_str:
                errors.append({'row': row_idx, 'error': 'Missing quantity'}); continue
            try:
                quantity_raw = Decimal(str(qty_str).replace(',', '').strip())
            except (InvalidOperation, ValueError):
                errors.append({'row': row_idx, 'error': f'Invalid quantity: "{qty_str}"'}); continue
            try:
                period_start = parse_date(start_str)
            except ValueError:
                errors.append({'row': row_idx, 'error': f'Invalid period_start: "{start_str}"'}); continue
            try:
                period_end = parse_date(end_str)
            except ValueError:
                errors.append({'row': row_idx, 'error': f'Invalid period_end: "{end_str}"'}); continue
            try:
                quantity_normalised, unit_normalised = normalise_energy(quantity_raw, unit_raw)
            except ValueError:
                errors.append({'row': row_idx, 'error': f'Unknown unit: "{unit_raw}"'}); continue
            for chunk in _pro_rate(quantity_normalised, period_start, period_end):
                co2e_kg = (chunk['quantity'] * ELECTRICITY_EF).quantize(Decimal('0.0001'), rounding=ROUND_HALF_UP)
                records.append({
                    'source_row_index': row_idx, 'source_row_raw': raw_dict,
                    'activity_date': chunk['activity_date'],
                    'period_start': chunk['period_start'], 'period_end': chunk['period_end'],
                    'scope': 2, 'category': 'electricity', 'subcategory': 'grid_electricity',
                    'quantity_raw': quantity_raw, 'unit_raw': unit_raw,
                    'quantity_normalised': chunk['quantity'], 'unit_normalised': 'kWh',
                    'emission_factor': ELECTRICITY_EF, 'emission_factor_source': ELECTRICITY_EF_SOURCE,
                    'co2e_kg': co2e_kg,
                    'metadata': {'meter_id': meter_id, 'site_name': site_name, 'tariff_code': tariff,
                                 'original_period': f"{period_start} to {period_end}"},
                })
        except Exception as e:
            errors.append({'row': row_idx, 'error': str(e)})
    return {'records': records, 'errors': errors, 'row_count': len(records)}
