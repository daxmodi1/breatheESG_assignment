# Tradeoffs — TRADEOFFS.md

Three honest tradeoffs made during development, with specific technical reasoning.

---

## 1. No Live API Pull — File Upload Only

**What we built:** File upload with manual parse. Users select a source type and drag-and-drop a CSV/TXT.

**What a production system needs:** Scheduled API pulls from SAP (OData), utility company portals (Green Button API), and travel platforms (Concur/Navan REST API) with OAuth2 flows, retry logic, and webhook-based change detection.

**Why we didn't build it:**
- SAP OData requires a configured Gateway endpoint with specific authorisations
- Concur Partner API requires application registration and client credentials we can't provision
- File upload covers the same parsing + normalisation logic — the "hard part" is the same
- Adding scheduled pulls is an infrastructure concern (Celery + Redis), not a data-model concern

**Impact:** Users must manually export and upload files. In production, this should be automated.

---

## 2. No PDF Utility Bill Parsing

**What we built:** CSV-only utility data ingestion (Green Button / portal export format).

**What a production system needs:** PDF bill parsing using OCR or structured PDF extraction (pdfplumber, AWS Textract, or Google Document AI).

**Why we didn't build it:**
- PDF layouts vary wildly per utility company (PG&E, EDF, British Gas all look different)
- Reliable extraction requires template-per-provider or ML-based field detection
- `pdfplumber` gets ~80% accuracy on structured PDFs but fails on scanned images
- The ROI is low for a prototype — CSV covers 90% of clients who use portal exports

**Impact:** Clients who only have PDF bills can't use the platform without manual data entry.

---

## 3. No Multi-User Concurrent Review Locking

**What we built:** Optimistic concurrency — any authorised analyst can approve/reject any record at any time. The last write wins.

**What a production system needs:** Pessimistic locking or record-level assignment. When Analyst A opens a record, Analyst B should see it as "in review" and be blocked from conflicting actions.

**Why we didn't build it:**
- Pessimistic locking requires WebSocket connections or polling for lock status
- Django doesn't have built-in record locking — would need `select_for_update()` + timeout logic
- For a single-analyst prototype, the conflict scenario doesn't occur
- The `is_locked` field partially mitigates this: once approved and locked, no further changes are possible

**Impact:** In a team of 5+ analysts reviewing simultaneously, two could approve/reject the same record. The audit log preserves both actions, but the final state is non-deterministic.

---

## Additional Limitations (Acknowledged)

| Limitation | Why | Production fix |
|-----------|-----|---------------|
| No real-time updates | Polling, not WebSockets | Django Channels + SSE |
| Single emission factor set | DEFRA 2023 only | Region-specific factor database with versioning |
| No data export | Dashboard only | CSV/Excel export endpoint + PDF report generation |
| No role-based permissions | All analysts can do everything | Django permissions + per-field access control |
| No i18n | English only | django-modeltranslation + react-intl |
