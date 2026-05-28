# Technical Decisions — DECISIONS.md

Every significant fork in the road, documented as it happened.

---

## 1. SAP IDoc Flat File over OData or BAPI

**Decision:** Accept pipe-delimited flat file uploads, not live OData/BAPI connections.

**Because:**
- Real sustainability teams receive flat file exports via email or SFTP — not live API access
- OData requires SAP Gateway configuration and credentials, which we can't simulate
- Flat files let us handle German column headers (`MENGE`, `MEINS`, `WERKS`) realistically
- The parser includes a header mapping dict that can be extended for other SAP configs

**What I'd ask the PM:** "Do clients have standardised SAP report layouts, or does each plant export with different column orders?"

---

## 2. Green Button CSV over PDF Bill Parsing

**Decision:** Support structured CSV exports, not scanned/electronic PDF bills.

**Because:**
- Green Button CSV is the US standard for utility data portability
- PDF parsing requires `pdfplumber` + layout heuristics that vary per utility company
- CSV gives us structured columns (meter_id, period, quantity, unit) immediately
- Error rate on PDF extraction is high and hard to validate

**Tradeoff:** Some clients only have PDF bills. This is documented in TRADEOFFS.md.

---

## 3. Concur CSV Export over Live API

**Decision:** Parse Concur-style CSV exports, not integrate with Concur's REST API.

**Because:**
- Concur API requires partner registration and OAuth tokens we can't provision
- CSV exports are what finance teams actually generate for expense reconciliation
- The format is well-documented and consistent across clients
- Flight distance computation from IATA codes (via `airportsdata` + haversine) is more interesting than just reading a distance field from an API

---

## 4. Non-Calendar Billing Periods → Pro-Rating

**Decision:** When a utility billing period spans multiple calendar months, pro-rate the consumption by days.

**Formula:** `monthly_quantity = total_quantity × (days_in_month_overlap / total_billing_days)`

**Because:**
- ESG reports need monthly breakdowns; billing periods are often 28–35 days
- Pro-rating by day count is the standard approach (used by CDP, GRI)
- Alternative: assign entire quantity to the start month — inaccurate for cross-month periods

---

## 5. Scope 1/2/3 Assignment Logic

**Decision:** Assign scope based on source type + SAP material group code.

- SAP fuel materials (ROE=diesel, ROG=natural gas) → **Scope 1** (direct combustion)
- SAP electricity materials (ELE*, ELEK) and all utility data → **Scope 2** (purchased energy)
- All travel data → **Scope 3** (business travel, Category 6)

**Because:**
- GHG Protocol defines scopes by operational control
- The simplification here is that all SAP fuel is Scope 1 — in reality, some may be Scope 3 if purchased for resale
- Travel is always Scope 3 under the GHG Protocol

---

## 6. DEFRA 2023 Emission Factors

**Decision:** Use UK DEFRA emission factors as the primary source.

**Because:**
- DEFRA publishes annual, detailed factors covering fuels, electricity, travel, and more
- They're freely available as structured Excel files
- Alternative sources (EPA, IPCC) are either less granular or harder to parse
- For a real deployment, the factor database should be region-specific (e.g., eGRID for US electricity)

---

## 7. SQLite for Dev, PostgreSQL for Prod

**Decision:** Use SQLite locally, PostgreSQL in production (via `DATABASE_URL`).

**Because:**
- SQLite has zero setup — `python manage.py migrate` just works
- PostgreSQL via Render's free tier for production
- Split settings (`settings/dev.py` vs `settings/prod.py`) keeps config clean
- Django ORM abstracts the difference — no raw SQL needed

---

## 8. JWT Authentication over Session Auth

**Decision:** Use `djangorestframework-simplejwt` for API authentication.

**Because:**
- Stateless — works cleanly with a React SPA on a different origin
- No CSRF token dance needed
- Auto-refresh with rotating refresh tokens for UX
- Standard Bearer token flow

---

## 9. Anomaly Detection via Z-Score

**Decision:** Auto-flag records where `|value - mean| > 3 × std` for the same category.

**Because:**
- Simple, well-understood statistical method
- Runs at ingest time — no separate ML pipeline needed
- Threshold of 3σ catches extreme outliers without excessive false positives
- Flagged records get `status=FLAGGED` + `anomaly_reason` for analyst review

**Limitation:** Needs ≥5 existing records per category to compute meaningful statistics.

---

## 10. Bulk `EmissionRecord` Creation

**Decision:** Use `bulk_create()` after parsing, not individual `create()` calls.

**Because:**
- A single SAP file can have hundreds of rows
- `bulk_create` sends one SQL INSERT vs N individual inserts
- 10x+ faster for large files
- Trade-off: `auto_now_add` fields work, but signals don't fire (acceptable here)
