# Portolan catalog — Helsinki Region (HSY)

A [Portolan](https://github.com/portolan-sdi/portolan) spatial-data infrastructure node where
**the git repository is the catalog's source**, and a bucket is its serving layer.

- **This repo holds the catalog *definition*, not the data bytes** — STAC (`catalog.json`,
  `items/`) + the small Apache Iceberg *metadata* (`metadata.json` + manifests, a few KB each).
  No parquet. You fix metadata or propose datasets the way you contribute to software:
  **open an issue or a PR.**
- **The data bytes live on the object-storage bucket**, never in git. Iceberg metadata in the
  repo points at the parquet by its bucket URL. (Git versions kilobytes of definition; the
  bucket holds gigabytes of data — see *Where the data lives*.)
- **On every merge, a GitHub Action publishes to the bucket** — it mirrors the metadata and
  *generates* the Apache Iceberg REST catalog (`/v1/config`, `/v1/.../namespaces`,
  `/v1/.../tables`) as object keys. The bucket is then a fully static, server-less Iceberg
  catalog you can **`ATTACH`** from DuckDB *or* Snowflake.

It holds one dataset from **Helsinki Region Environmental Services (HSY)**: `seuturamava_kortteli`
— per-plan-block land-use category and unused building-rights reserve (SeutuRAMAVA), across
Espoo / Vantaa / Kauniainen — in two Iceberg representations: **`v2.hsy_zoning`** (WKB geometry +
bbox columns) and **`v3.hsy_zoning`** (native Iceberg `GEOMETRY`). Provenance is recorded in the
STAC item (`properties.portolan:provenance`). Licensing is in [`LICENSE`](LICENSE): data CC-BY-4.0
(© HSY), tooling Apache-2.0.

## Read it — two ways, no server in either

**1. `ATTACH` the catalog endpoint** (works in DuckDB and Snowflake):

```sql
INSTALL iceberg; LOAD iceberg; INSTALL httpfs; LOAD httpfs; INSTALL spatial; LOAD spatial;
SET geometry_always_xy = true;

ATTACH 'hsy' (TYPE iceberg,
  ENDPOINT 'https://8et4c.upcloudobjects.com/carto-ogc-connect-helsinki/repo/portolan-hsy-catalog',
  AUTHORIZATION_TYPE 'none');

SELECT kunta, count(*) AS blocks, sum(laskvar_ak) AS unused_apartment_rights_m2
FROM hsy.v2.hsy_zoning
GROUP BY kunta ORDER BY blocks DESC;
```

**2. `iceberg_scan()` a dataset's metadata file directly** (no catalog needed):

```sql
SELECT kunta, korttunnus, laskvar_ak
FROM iceberg_scan('https://8et4c.upcloudobjects.com/carto-ogc-connect-helsinki/repo/portolan-hsy-catalog/data/v2/hsy_zoning/metadata/v1.metadata.json')
WHERE laskvar_ak > 0 LIMIT 5;
```

Or discover it the Portolan way: read [`catalog.json`](catalog.json) → the item → take the
asset's `portolan:iceberg_endpoint` (to `ATTACH`) or `data.href` (to `iceberg_scan`).

## Why the bucket, and not GitHub Pages?

The Iceberg REST catalog needs the same path to be **both a resource and a container**:
`/v1/sdi/namespaces` returns the namespace *list*, while `/v1/sdi/namespaces/v2` is a child of it.
On **object storage** the keyspace is flat — no problem. On a **filesystem** (and git is a
filesystem, and GitHub Pages serves a committed git tree) you can't have a file `namespaces`
*and* a directory `namespaces/`. So the REST catalog is **generated to the bucket**, never stored
in git — which is exactly why `ATTACH` works against the bucket but couldn't from Pages.

## Layout

```
catalog.json                              STAC Catalog (definition)
items/seuturamava_kortteli.json           STAC Item — metadata, bbox, semantics, endpoints
data/v2/hsy_zoning/metadata/              Iceberg metadata, v2 = WKB geometry — IN GIT
data/v3/hsy_zoning/metadata/              Iceberg metadata, v3 = native GEOMETRY — IN GIT
data/catalog/datasets/metadata/           Iceberg metadata for the STAC index table — IN GIT
data/**/data/*.parquet                    the data bytes — ON THE BUCKET ONLY (git-ignored)
LICENSE                                   CC-BY-4.0 (data) + Apache-2.0 (tooling)
tools/publish.py                          mirrors metadata + generates the REST catalog
.github/workflows/publish.yml             runs publish.py on every merge
```

## Where the data lives

Git holds the **definition** (STAC + Iceberg metadata, kilobytes). The object-storage bucket
holds the **data** (the GeoParquet, and a copy of the metadata + the generated REST catalog).
The data bytes are never committed to git — `data/**/data/` is git-ignored. This is what lets
the model scale: a catalog of terabytes is still a tiny, diffable, PR-able git repo.

## Contributing data

- **Fix metadata / propose a dataset:** open a PR or issue — that's a normal git change to the
  definition, reviewed and merged, then auto-published.
- **Add or update the actual data bytes:** upload the GeoParquet to the bucket under
  `…/data/<namespace>/<table>/data/`, then commit the matching Iceberg metadata
  (`metadata.json` + manifests, pointing at that bucket URL) in a PR. On merge, the Action
  republishes the REST catalog. (A PR cannot carry the bytes — that's deliberate; the bytes
  go to the store, the *pointer* goes through review.)

## Publishing (what the Action does)

```bash
MC_TARGET=upcloud/carto-ogc-connect-helsinki/repo/portolan-hsy-catalog \
PUBLIC_BASE=https://8et4c.upcloudobjects.com/carto-ogc-connect-helsinki/repo/portolan-hsy-catalog \
python tools/publish.py
```

CI needs two repo secrets — `UPCLOUD_ACCESS_KEY`, `UPCLOUD_SECRET_KEY` — scoped to write only
this bucket prefix.

## Sovereignty

GitHub (repo + Action runner) is US-hosted; the **bucket** is the part that matters for serving,
and here it is EU object storage (UpCloud 🇫🇮). The same repo can publish to any S3-compatible
bucket — on-prem MinIO, another EU provider — by changing two values. Hosting is a choice;
the catalog is portable.

## Standards: STAC *and* OGC API - Records

This catalogue is published in both vocabularies, because they're the same model — GeoJSON
`Feature`s and Collections, built on the OGC API - Features foundation (and STAC is itself an
OGC Community Standard since 2025):

- **STAC** — [`catalog.json`](catalog.json) + [`items/`](items/)
- **OGC API - Records** — [`records/catalog.json`](records/catalog.json) +
  [`records/seuturamava_kortteli.json`](records/seuturamava_kortteli.json)

The Records record is the STAC item with OGC field names: `properties.datetime` → top-level
`time`, `assets` → `links`, `providers` → `contacts`, plus `properties.type` and `conformsTo`;
OSI semantics map to `themes`. Portolan-specific fields stay as namespaced `portolan:*`
properties (a small building-block extension with its own JSON-LD context).

> **Described by OGC, queried by everyone.** Portolan carries the OGC lineage — STAC and OGC API
> - Records for meaning and discovery — onto the open analytics foundation (Apache Iceberg,
> GeoParquet, DuckDB/Snowflake), so geospatial keeps its standards yet stops being a silo.

## Validation & building-block conformance

Every pull request is validated in CI (`tools/validate.py` via `.github/workflows/validate.yml`,
no credentials needed) before anything can publish:

- every JSON parses; STAC items and OGC API - Records records have their required fields;
- all Iceberg metadata/manifest URLs point at this catalog's bucket base (catches mis-relocated
  tables — the bug that silently breaks `ATTACH`);
- referenced GeoParquet **actually exists on the bucket** (enforces "upload data, then PR the
  metadata");
- the `portolan:*` properties validate against the **OGC building block** in
  [`bblock/portolan-record/`](bblock/) (`schema.json` + JSON-LD `context.jsonld`), which extends
  `ogc.api.records.v1.0.record-core`.

So "anyone can PR into this catalog" is a *gated* claim, not an aspirational one.

## Usage reporting (opt-in)

A traditional portal sees *which* bytes were fetched, never *why*. This catalog adds an opt-in
**usage report** (a `usage-report` issue template): with the user's consent, an agent can file
what it was trying to answer, so the publisher learns real use cases and can prioritize data.
It's a **public** issue — paraphrased, no confidential or personal data; sensitive intent should
not use this channel. Agents: see [`AGENTS.md`](AGENTS.md) (default is *not* to send).

## Part of a federation

One child of the Portolan Helsinki *catalog of catalogs*:
`https://8et4c.upcloudobjects.com/carto-ogc-connect-helsinki/catalog/stac.json`

Data: HSY, licensed CC-BY-4.0.
