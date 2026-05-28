"""
Travel CSV Parser — Concur-style expense exports.
Calculates great-circle distances from IATA codes, applies DEFRA emission factors.
"""
import io, csv, math
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from apps.ingestion.normalizers.dates import parse_date

try:
    import airportsdata
    AIRPORTS = airportsdata.load('IATA')
except Exception:
    AIRPORTS = {}

# DEFRA 2023 emission factors
TRAVEL_EF = {
    'AIR': {
        'ECONOMY':  {'factor': Decimal('0.255'), 'source': 'DEFRA 2023'},
        'PREMIUM':  {'factor': Decimal('0.382'), 'source': 'DEFRA 2023'},
        'BUSINESS': {'factor': Decimal('0.573'), 'source': 'DEFRA 2023'},
        'FIRST':    {'factor': Decimal('0.745'), 'source': 'DEFRA 2023'},
    },
    'HOTEL': {'factor': Decimal('36.0'), 'unit': 'kgCO2e/night', 'source': 'DEFRA 2023'},
    'CAR':   {'factor': Decimal('0.168'), 'unit': 'kgCO2e/km', 'source': 'DEFRA 2023'},
    'RAIL':  {'factor': Decimal('0.035'), 'unit': 'kgCO2e/km', 'source': 'DEFRA 2023'},
    'TAXI':  {'factor': Decimal('0.148'), 'unit': 'kgCO2e/km', 'source': 'DEFRA 2023'},
}


def _haversine_km(lat1, lon1, lat2, lon2):
    R = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat/2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon/2)**2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))


def _iata_distance(origin, destination):
    o = AIRPORTS.get(origin.strip().upper())
    d = AIRPORTS.get(destination.strip().upper())
    if not o or not d:
        return None
    return Decimal(str(round(_haversine_km(o['lat'], o['lon'], d['lat'], d['lon']), 2)))


def parse_travel_file(file_content, filename=''):
    if isinstance(file_content, bytes):
        file_content = file_content.decode('utf-8-sig')
    reader = csv.DictReader(io.StringIO(file_content))
    if reader.fieldnames:
        reader.fieldnames = [h.strip().lower().replace(' ', '_').replace('-', '_') for h in reader.fieldnames]
    records, errors = [], []
    for row_idx, row in enumerate(reader, start=1):
        try:
            raw_dict = dict(row)
            travel_type = (row.get('travel_type') or row.get('type') or '').strip().upper()
            date_str = row.get('travel_date') or row.get('date') or row.get('expense_date') or ''
            origin = (row.get('origin') or '').strip().upper()
            destination = (row.get('destination') or '').strip().upper()
            travel_class = (row.get('travel_class') or row.get('class') or 'ECONOMY').strip().upper()
            distance_str = row.get('distance_km') or row.get('distance') or ''
            nights_str = row.get('nights') or '0'
            if not travel_type:
                errors.append({'row': row_idx, 'error': 'Missing travel_type'}); continue
            try:
                activity_date = parse_date(date_str)
            except ValueError:
                errors.append({'row': row_idx, 'error': f'Invalid date: "{date_str}"'}); continue

            anomaly, anomaly_reason = False, ''

            if travel_type == 'AIR':
                distance = None
                if distance_str:
                    try:
                        distance = Decimal(str(distance_str).replace(',', '').strip())
                    except (InvalidOperation, ValueError):
                        pass
                if distance is None and origin and destination:
                    distance = _iata_distance(origin, destination)
                    if distance is None:
                        anomaly, anomaly_reason = True, f'Unknown airport code: {origin} or {destination}'
                        distance = Decimal('0')
                    else:
                        anomaly_reason = 'distance_estimated_from_iata'
                if distance is None:
                    errors.append({'row': row_idx, 'error': 'No distance and no valid airport codes'}); continue
                ef_info = TRAVEL_EF['AIR'].get(travel_class, TRAVEL_EF['AIR']['ECONOMY'])
                co2e_kg = (distance * ef_info['factor']).quantize(Decimal('0.0001'), rounding=ROUND_HALF_UP)
                records.append({
                    'source_row_index': row_idx, 'source_row_raw': raw_dict,
                    'activity_date': activity_date, 'period_start': activity_date, 'period_end': activity_date,
                    'scope': 3, 'category': 'air_travel', 'subcategory': travel_class.lower(),
                    'quantity_raw': distance, 'unit_raw': 'km',
                    'quantity_normalised': distance, 'unit_normalised': 'km',
                    'emission_factor': ef_info['factor'], 'emission_factor_source': ef_info['source'],
                    'co2e_kg': co2e_kg, 'is_anomaly': anomaly, 'anomaly_reason': anomaly_reason,
                    'metadata': {'origin': origin, 'destination': destination, 'travel_class': travel_class,
                                 'route': f'{origin}-{destination}'},
                })
            elif travel_type == 'HOTEL':
                try:
                    nights = int(nights_str) if nights_str else 0
                except ValueError:
                    nights = 0
                if nights <= 0:
                    errors.append({'row': row_idx, 'error': 'Hotel stay with 0 nights'}); continue
                ef = TRAVEL_EF['HOTEL']
                co2e_kg = (Decimal(nights) * ef['factor']).quantize(Decimal('0.0001'))
                records.append({
                    'source_row_index': row_idx, 'source_row_raw': raw_dict,
                    'activity_date': activity_date, 'period_start': activity_date, 'period_end': activity_date,
                    'scope': 3, 'category': 'hotel_stay', 'subcategory': destination or 'unknown',
                    'quantity_raw': Decimal(nights), 'unit_raw': 'nights',
                    'quantity_normalised': Decimal(nights), 'unit_normalised': 'nights',
                    'emission_factor': ef['factor'], 'emission_factor_source': ef['source'],
                    'co2e_kg': co2e_kg, 'is_anomaly': False, 'anomaly_reason': '',
                    'metadata': {'destination': destination, 'nights': nights},
                })
            else:  # CAR, RAIL, TAXI
                distance = Decimal('0')
                if distance_str:
                    try:
                        distance = Decimal(str(distance_str).replace(',', '').strip())
                    except (InvalidOperation, ValueError):
                        errors.append({'row': row_idx, 'error': f'Invalid distance: "{distance_str}"'}); continue
                ef = TRAVEL_EF.get(travel_type, TRAVEL_EF.get('CAR'))
                co2e_kg = (distance * ef['factor']).quantize(Decimal('0.0001'))
                records.append({
                    'source_row_index': row_idx, 'source_row_raw': raw_dict,
                    'activity_date': activity_date, 'period_start': activity_date, 'period_end': activity_date,
                    'scope': 3, 'category': f'ground_transport_{travel_type.lower()}',
                    'subcategory': travel_type.lower(),
                    'quantity_raw': distance, 'unit_raw': 'km',
                    'quantity_normalised': distance, 'unit_normalised': 'km',
                    'emission_factor': ef['factor'], 'emission_factor_source': ef['source'],
                    'co2e_kg': co2e_kg, 'is_anomaly': False, 'anomaly_reason': '',
                    'metadata': {'origin': origin, 'destination': destination},
                })
        except Exception as e:
            errors.append({'row': row_idx, 'error': str(e)})
    return {'records': records, 'errors': errors, 'row_count': len(records)}
