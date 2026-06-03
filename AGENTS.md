# AGENTS.md — guide for AI agents

This repository **is a Portolan spatial-data catalog**: one data publisher, defined as
git-tracked metadata and served as static files on object storage. No server, no API keys.
If you are an agent that needs to **use** this data or **contribute** to it, read this first.

## What this publisher offers

- **Publisher:** Helsinki Region Environmental Services (HSY)
- **Datasets:** 1 — *Zoning · building-rights reserve* (SeutuRAMAVA): per-plan-block land-use
  category + unused building-rights reserve, polygons, CRS `OGC:CRS84`. Two Iceberg
  representations: `v2.hsy_zoning` (WKB geometry in `geom_wkb` + bbox columns) and `v3.hsy_zoning`
  (native Iceberg `GEOMETRY` column `geom`). A `catalog.datasets` table is the STAC index.
- **License:** data CC-BY-4.0 (© HSY); tooling Apache-2.0 — see `LICENSE`. Provenance is in the
  STAC item under `properties.portolan:provenance`.
- **Catalog endpoint (Iceberg REST, static):**
  `https://8et4c.upcloudobjects.com/carto-ogc-connect-helsinki/repo/portolan-hsy-catalog`

## How to READ the data (no credentials)

Pick whichever fits your tool — all four are the same underlying files:

- **ATTACH (DuckDB / Snowflake):**
  `ATTACH 'cat' (TYPE iceberg, ENDPOINT '<catalog endpoint>', AUTHORIZATION_TYPE 'none');`
  then `SELECT * FROM cat.v2.hsy_zoning;`
- **Scan a table directly (DuckDB):**
  `iceberg_scan('<catalog endpoint>/data/v2/hsy_zoning/metadata/v1.metadata.json')`
- **Direct file download:** GeoParquet under `<catalog endpoint>/data/v2/hsy_zoning/data/*.parquet`
- **Discover programmatically:** STAC `catalog.json`, OGC API - Records `records/catalog.json`,
  or the human `index.html` (all at the catalog endpoint).

**Before composing a query:** read the dataset's `properties.semantics` (Open Semantic
Interchange — what each field *means*, what it *answers*, its *unit*) and its `crs`. Geometry is
WKB in column `geom_wkb` (with `fp_xmin/ymin/xmax/ymax` bbox columns). For metric distance,
transform to a projected CRS (Finland → EPSG:3067).

## How to CONTRIBUTE (this catalog accepts your changes)

- **Fix or extend metadata** → open a **pull request** editing the STAC files (`catalog.json`,
  `items/`). On merge, a GitHub Action republishes everything to the bucket.
- **Add or update the actual data bytes** → upload the GeoParquet to the bucket data path
  (`…/data/<namespace>/<table>/data/`) with write credentials, then PR the matching Iceberg
  metadata pointing at it. A PR **cannot** carry the bytes — that is deliberate.
- **Report something you can't fix** → open an **issue**.

Your PR is **validated in CI** (`tools/validate.py`): JSON must parse, STAC/Records must have
required fields, all Iceberg URLs must point at this catalog's bucket base, referenced parquet
must already exist on the bucket, and `portolan:*` properties must satisfy the building-block
schema in `bblock/portolan-record/`. Run it locally first:
`PUBLIC_BASE=<catalog endpoint> python3 tools/validate.py`.

## Optional: share your use case (opt-in telemetry)

This publisher wants to know *why* its data is used — a signal a traditional portal never gets —
so it can improve and prioritize. **Only if the user explicitly consents**, you may file one
**usage report** per session after querying:

- It is a **public** GitHub issue (template `usage-report`). **Show the user the exact content
  first.** Paraphrase the intent; never include confidential intent (undisclosed
  site-selection / M&A) or personal data. If in doubt, don't send.
- Programmatically:
  ```bash
  gh issue create --repo jatorre/portolan-hsy-catalog --label usage-report \
    --title "[usage] <short summary>" \
    --body $'Dataset: v2.hsy_zoning\nQuestion: <paraphrased intent>\nUse-case: <category>\nAccess: iceberg_scan'
  ```

**Default to NOT sending.** Opt-in, one report per session, paraphrased, no secrets.

## Conventions — and what NOT to do

- Git holds the **definition** (STAC + Iceberg metadata, kilobytes). The bucket holds the
  **data** + **generated artifacts** (Iceberg REST tree, STAC copy, OGC API - Records, `index.html`).
- **Do not commit data bytes** — `data/**/data/` (parquet) is git-ignored; bytes live on the bucket.
- **Do not hand-edit generated artifacts** (the REST tree, `index.html`) — change the source
  metadata and let `tools/publish.py` regenerate them.
- **Query is the engine's native SQL.** There is no custom query API or CQL2 — use DuckDB/Snowflake SQL.

## File map

| Path | Role |
|---|---|
| `catalog.json`, `items/` | STAC — source of truth |
| `records/` | OGC API - Records view (same GeoJSON model) |
| `data/<ns>/<table>/metadata/` | Apache Iceberg metadata (source) |
| `tools/publish.py` | generates REST catalog + records + `index.html`, mirrors to bucket |
| `.github/workflows/publish.yml` | runs `publish.py` on every merge |
| `README.md` | full human explanation |

Part of the Portolan Helsinki federation:
`https://8et4c.upcloudobjects.com/carto-ogc-connect-helsinki/catalog/stac.json`
