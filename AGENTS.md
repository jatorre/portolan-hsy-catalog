# AGENTS.md — guide for AI agents

This repository **is a Portolan spatial-data catalog**: one data publisher, defined as
git-tracked metadata and served as static files on object storage. No server, no API keys.
It follows the **git-backed Portolan spec** (model 3): git holds the catalog *definition*
(`catalog.json`, `versions.json`, `<id>/collection.json`, `<id>/versions.json`, `.portolan/`);
the bucket holds the *data bytes* (GeoParquet + the Apache Iceberg tables). If you are an agent
that needs to **use** this data or **contribute** to it, read this first.

## What this publisher offers

- **Publisher:** Helsinki Region Environmental Services (HSY)
- **Datasets:** 1 — *Zoning · building-rights reserve* (`seuturamava_kortteli`, SeutuRAMAVA):
  per-plan-block land-use category + unused building-rights reserve, polygons, CRS `OGC:CRS84`.
  Two Iceberg representations: `v2.hsy_zoning` (WKB geometry) and `v3.hsy_zoning` (native Iceberg
  `GEOMETRY` column `geom`). The collection points at the **v3** table.
- **License:** data CC-BY-4.0 (© HSY); tooling Apache-2.0 — see `LICENSE`.
- **Catalog endpoint (Iceberg REST + STAC, static):**
  `https://8et4c.upcloudobjects.com/carto-ogc-connect-helsinki/repo/portolan-hsy-catalog`

## How to READ the data (no credentials)

The same underlying files are reachable several ways — all at the catalog endpoint above:

- **ATTACH (DuckDB / Snowflake):**
  `ATTACH 'cat' (TYPE iceberg, ENDPOINT '<catalog endpoint>', AUTHORIZATION_TYPE 'none');`
  then `SELECT * FROM cat.v3.hsy_zoning;`
- **Scan a table directly (DuckDB):**
  `iceberg_scan('<catalog endpoint>/data/v3/hsy_zoning/metadata/v1.metadata.json')`
- **GeoParquet snapshot:** `read_parquet('<catalog endpoint>/seuturamava_kortteli/seuturamava_kortteli.parquet')`
- **Discover programmatically:** STAC `catalog.json` (root) → `seuturamava_kortteli/collection.json`.

The collection carries the **stac-iceberg-extension** (`iceberg:catalog_uri`, `iceberg:table_id`,
`iceberg:current_snapshot_id`) and an `iceberg` asset, so an agent can go straight from STAC to
the live table. **Before composing a query:** read `properties.semantics` (Open Semantic
Interchange — what each field *means*, what it *answers*, its *unit*) and the `crs`. For metric
distance, transform to a projected CRS (Finland → EPSG:3067).

## How to CONTRIBUTE (this catalog accepts your changes)

- **Fix or extend metadata** → open a **pull request** editing `catalog.json` or
  `seuturamava_kortteli/collection.json` (each collection carries a `git:edit_url`). On merge, the
  definition is republished to the bucket.
- **Add or update the actual data bytes** → upload the new GeoParquet / Iceberg table to the
  bucket, then PR the matching `collection.json` (bump `iceberg:current_snapshot_id` and
  `versions.json`). A PR **cannot** carry the bytes — that is deliberate (model 3).
- **Report something you can't fix** → open an **issue**.

## Optional: share your use case (opt-in telemetry)

This publisher wants to know *why* its data is used — a signal a traditional portal never gets.
**Only if the user explicitly consents**, you may file one **usage report** per session after
querying:

- It is a **public** GitHub issue (template `usage-report`). **Show the user the exact content
  first.** Paraphrase the intent; never include confidential intent (undisclosed
  site-selection / M&A) or personal data. If in doubt, don't send.
- Programmatically:
  ```bash
  gh issue create --repo jatorre/portolan-hsy-catalog --label usage-report \
    --title "[usage] <short summary>" \
    --body $'Dataset: v3.hsy_zoning\nQuestion: <paraphrased intent>\nUse-case: <category>\nAccess: iceberg_scan'
  ```

**Default to NOT sending.** Opt-in, one report per session, paraphrased, no secrets.

## Conventions — and what NOT to do

- Git holds the **definition** (`catalog.json`, `versions.json`, `<id>/collection.json`,
  `<id>/versions.json`, `.portolan/`). The bucket holds the **data bytes** + the live Iceberg
  REST/`data/` tree.
- **Do not commit data bytes** — `*.parquet` is git-ignored; bytes live on the bucket.
- **Never delete the bucket's `v1/` (Iceberg REST) or `data/` (Iceberg tables)** — that is the
  live `ATTACH` layer.
- **Query is the engine's native SQL.** There is no custom query API or CQL2 — use DuckDB/Snowflake SQL.

## File map

| Path | Role |
|---|---|
| `catalog.json` | STAC root + git-backed-catalog extension (`git:repository`, links) |
| `seuturamava_kortteli/collection.json` | STAC collection + stac-iceberg extension |
| `seuturamava_kortteli/versions.json` | per-collection asset version log |
| `versions.json` | catalog-level version index |
| `.portolan/` | Portolan CLI config + version lock |
| `README.md` | full human explanation |

Part of the Portolan Helsinki federation:
`https://8et4c.upcloudobjects.com/carto-ogc-connect-helsinki/catalog/stac.json`
