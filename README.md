# Portolan catalog — Helsinki Region (HSY)

A [Portolan](https://github.com/portolan-sdi/portolan) spatial-data infrastructure node where
**the git repository is the catalog's definition**, and an object-storage bucket is its serving
layer. It follows the **git-backed Portolan spec** (model 3).

- **This repo holds the catalog *definition*, not the data bytes** — the STAC `catalog.json`
  (with the [git-backed-catalog](https://portolan-sdi.github.io/git-backed-catalog/v1.0.0/schema.json)
  extension) plus, per dataset, a `collection.json` (with the
  [stac-iceberg](https://portolan-sdi.github.io/stac-iceberg-extension/v1.0.0/schema.json)
  extension) and a `versions.json`. No parquet. You fix metadata or propose datasets the way you
  contribute to software: **open an issue or a PR** (each collection carries a `git:edit_url`).
- **The data bytes live on the object-storage bucket**, never in git: a GeoParquet snapshot per
  dataset plus the live Apache Iceberg tables under `data/` and the Iceberg REST tree under `v1/`.
  Git versions kilobytes of definition; the bucket holds the data.

It holds one dataset from **Helsinki Region Environmental Services (HSY)**: `seuturamava_kortteli`
— per-plan-block land-use category and unused building-rights reserve (SeutuRAMAVA) — in two
Iceberg representations: **`v2.hsy_zoning`** (WKB geometry) and **`v3.hsy_zoning`** (native
Iceberg `GEOMETRY`). The collection points at the **v3** table.

## Endpoint

```
https://8et4c.upcloudobjects.com/carto-ogc-connect-helsinki/repo/portolan-hsy-catalog
```

## Read the data (no credentials)

```sql
-- ATTACH the static Iceberg REST catalog
ATTACH 'hsy' (TYPE iceberg,
  ENDPOINT 'https://8et4c.upcloudobjects.com/carto-ogc-connect-helsinki/repo/portolan-hsy-catalog',
  AUTHORIZATION_TYPE 'none');
SELECT * FROM hsy.v3.hsy_zoning;

-- or scan a table directly
SELECT * FROM iceberg_scan('https://8et4c.upcloudobjects.com/carto-ogc-connect-helsinki/repo/portolan-hsy-catalog/data/v3/hsy_zoning/metadata/v1.metadata.json');

-- or read the GeoParquet snapshot
SELECT * FROM read_parquet('https://8et4c.upcloudobjects.com/carto-ogc-connect-helsinki/repo/portolan-hsy-catalog/seuturamava_kortteli/seuturamava_kortteli.parquet');
```

Discover via STAC: the root `catalog.json` → `seuturamava_kortteli/collection.json`.

## License

Data **CC-BY-4.0** (© HSY). Tooling/metadata Apache-2.0 — see `LICENSE`.

## Contribute

- **Fix or extend metadata** → PR `catalog.json` or `seuturamava_kortteli/collection.json`.
- **Add or update data bytes** → upload to the bucket, then PR the matching `collection.json`
  (bump `iceberg:current_snapshot_id` and `versions.json`). A PR cannot carry the bytes — that is
  deliberate (model 3).
- **Report a problem** → open an issue.

## What git tracks

```
catalog.json                              STAC root + git-backed-catalog extension
versions.json                             catalog-level version index
seuturamava_kortteli/collection.json      STAC collection + stac-iceberg extension
seuturamava_kortteli/versions.json        per-collection asset version log
.portolan/                                Portolan CLI config + version lock
AGENTS.md                                 guide for AI agents
```

The data bytes (`*.parquet`) are git-ignored — they live on the bucket only, alongside the live
`v1/` (Iceberg REST) and `data/` (Iceberg tables) serving layer.

Part of the Portolan Helsinki federation:
`https://8et4c.upcloudobjects.com/carto-ogc-connect-helsinki/catalog/stac.json`
