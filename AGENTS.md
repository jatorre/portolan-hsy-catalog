# AGENTS.md — guide for AI agents

This repository **is a Portolan spatial-data catalog**: one data publisher, defined as
git-tracked metadata and served as static files on object storage. No server, no API keys.
If you are an agent that needs to **use** this data or **contribute** to it, read this first.

## What this publisher offers

- **Publisher:** Helsinki Region Environmental Services (HSY)
- **Datasets:** 1 — `v2.hsy_zoning` — *Zoning · building-rights reserve* (SeutuRAMAVA):
  per-plan-block land-use category + unused building-rights reserve, polygons, CRS `OGC:CRS84`.
- **License:** CC-BY-4.0.
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
