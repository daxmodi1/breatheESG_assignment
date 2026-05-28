# Data Sources Research — SOURCES.md

Research notes on each of the three data sources, what I learned, and what would break in production.

---

## Source 1: SAP — Fuel & Procurement Data

### What I researched
- SAP BAPI export format (IDoc flat files)
- SAP transaction codes: ME2M (purchase orders), MB52 (warehouse stock), MIGO (goods movements)
- German field naming conventions in SAP standard tables (MARA, EKPO, MSEG)

### Key learnings
- SAP exports use pipe (`|`) or tab delimiters, not comma — because German decimal notation uses commas
- Column headers are SAP internal names: `MENGE` (quantity), `MEINS` (unit of measure), `WERKS` (plant), `MATKL` (material group), `BLDAT` (document date)
- Material group codes (MATKL) are client-configured — there's no universal standard. `ROE` for diesel is common in German SAP systems but not guaranteed
- Date format is `YYYYMMDD` (SAP internal), not ISO 8601
- Units follow SAP unit codes: `L` (litre), `M3` (cubic metre), `KWH`, `KG`, `ST` (Stück = pieces)

### Why the sample data looks the way it does
- Pipe-delimited to match real SAP exports
- German field names in the header row
- Mix of fuel types (diesel, natural gas, petrol, LPG) and electricity
- Multiple plants (PL01, PL02, PL03) to demonstrate multi-site reporting
- Realistic quantities (5,000L diesel, 12,000 m³ gas, 45,000 kWh electricity)

### What would break in production
- Client-specific column mappings — every SAP instance has different report layouts
- Unit code variants (SAP has 100+ unit codes, we handle ~15)
- Fiscal year vs calendar year date handling
- Negative quantities for credit notes / returns
- Multi-currency conversion (our prototype ignores monetary values for emission purposes)

---

## Source 2: Utility Data — Electricity

### What I researched
- Green Button standard (NAESB REQ.21 / ESPI)
- UK utility portal CSV exports (British Gas, EDF Energy, SSE)
- Billing period structures for commercial accounts

### Key learnings
- Green Button is a US standard (since 2012) that provides structured XML or CSV electricity usage data
- Most UK/EU utilities don't implement Green Button — they have proprietary portal exports
- Commercial accounts have non-calendar billing periods (e.g., Jan 15 – Feb 14), requiring pro-rating
- Units vary: kWh (most common), MWh (large industrial), kVAh (reactive power), therms (gas)
- Tariff codes are essential metadata — TOU (Time-of-Use) vs flat rate affects cost analysis but not emissions

### Why the sample data looks the way it does
- Standard CSV with headers that match common portal exports
- Includes a cross-month billing period (MTR-002: Jan 15 – Feb 14) to test pro-rating
- Mix of building types (HQ, Warehouse, Data Centre, Branch Office)
- One MWh entry (Manufacturing Plant) to test unit conversion
- Realistic kWh quantities for commercial buildings

### What would break in production
- Multiple meters per building with different billing cycles
- Estimated vs actual reads (utilities flag this, we don't handle it)
- Feed-in tariffs / solar generation offsets (negative consumption)
- Gas bills mixed into electricity CSV exports
- Currency and tax fields that need to be ignored

---

## Source 3: Corporate Travel — Concur Expense Data

### What I researched
- SAP Concur Standard Accounting Extract (SAE) format
- IATA airport code database (airportsdata Python package)
- DEFRA 2023 conversion factors for business travel
- Great-circle distance calculation (Haversine formula)

### Key learnings
- Concur exports include all expense types — need to filter to travel-relevant categories (AIR, HOTEL, CAR, RAIL)
- Flight entries often have airport codes but **no distance** — must calculate from coordinates
- `airportsdata` package provides lat/lon for 7,500+ airports, updated regularly
- Travel class significantly affects emission factor: Business class is ~2.25x Economy per km (DEFRA 2023)
- Hotels are measured in nights × country-average factor, not energy consumption
- IATA codes are 3-letter (LHR, JFK). ICAO codes are 4-letter (EGLL, KJFK) — Concur uses IATA

### DEFRA 2023 Emission Factors Used
| Travel Type          | Factor              | Unit          |
|---------------------|---------------------|---------------|
| Air (Economy, <3700km) | 0.255             | kgCO₂e / km   |
| Air (Business)       | 0.573              | kgCO₂e / km   |
| Air (First)          | 0.745              | kgCO₂e / km   |
| Hotel (UK average)   | 36.0               | kgCO₂e / night |
| Car rental           | 0.168              | kgCO₂e / km   |
| Rail (national avg)  | 0.035              | kgCO₂e / km   |
| Taxi                 | 0.148              | kgCO₂e / km   |

### Why the sample data looks the way it does
- Matches Concur Standard Extract column layout
- Flights have origin/destination IATA codes but empty `distance_km` — forces the parser to calculate via Haversine
- Mix of travel types: air (multiple classes), hotel, car, rail, taxi
- International routes (LHR-JFK, CDG-NRT, SIN-HKG) for realistic distance ranges
- One taxi without origin/destination to test edge case handling

### What would break in production
- Airport code typos or non-IATA codes (some regional airports use different codes)
- Multi-leg flights listed as single entries (LHR→DXB→SIN counted as LHR→SIN)
- Personal expenses mixed with business travel
- Missing travel class defaulting to Economy (underestimates for upgrades)
- Currency conversion for cost-based allocation methods
- Non-English expense descriptions

---

## Emission Factor Sources

| Source | Year | Coverage | URL |
|--------|------|----------|-----|
| DEFRA | 2023 | UK + international travel | gov.uk/government/publications/greenhouse-gas-reporting-conversion-factors-2023 |
| IPCC AR6 | 2021 | Global warming potentials | ipcc.ch/assessment-report/ar6 |
| EPA eGRID | 2022 | US regional electricity | epa.gov/egrid |
