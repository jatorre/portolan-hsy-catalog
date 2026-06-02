# Portolan catalog — Helsinki Region (HSY)

A [Portolan](https://github.com/portolan-sdi/portolan) spatial-data infrastructure node where
**the git repository is the catalog's source**, and a bucket is its serving layer.

- **This repo is the source of truth** — STAC metadata + the Apache Iceberg table files
  (`metadata.json`, manifests, GeoParquet). All normal, collision-free file paths. You
  contribute data or fix metadata the way you contribute to software: **open an issue or a PR.**
- **On every merge, a GitHub Action publishes to an object-storage bucket** — it mirrors the
  data files and *generates* the Apache Iceberg REST catalog (`/v1/config`, `/v1/.../namespaces`,
  `/v1/.../tables`) as object keys. That bucket is then a fully static, server-less Iceberg
  catalog you can **`ATTACH`** from DuckDB *or* Snowflake.

It holds one dataset from **Helsinki Region Environmental Services (HSY)**: `seuturamava_kortteli`
— per-plan-block land-use category and unused building-rights reserve (SeutuRAMAVA), across
Espoo / Vantaa / Kauniainen.

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
catalog.json                              STAC Catalog (source)
items/seuturamava_kortteli.json           STAC Item — metadata, bbox, semantics, endpoints
data/v2/hsy_zoning/                        Apache Iceberg table (source files)
  metadata/v1.metadata.json, *.avro
  data/hsy_zoning.parquet
tools/publish.py                          generates the REST catalog + pushes to the bucket
.github/workflows/publish.yml             runs publish.py on every merge
```

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

## Part of a federation

One child of the Portolan Helsinki *catalog of catalogs*:
`https://8et4c.upcloudobjects.com/carto-ogc-connect-helsinki/catalog/stac.json`

Data: HSY, licensed CC-BY-4.0.
