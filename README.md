# Portolan catalog — Helsinki Region (HSY)

**The repository *is* the catalog.** This is a [Portolan](https://github.com/portolan-sdi/portolan)
spatial-data infrastructure node published as nothing more than static files in a git repo,
served over **GitHub Pages**. No server, no database, no REST catalog endpoint, no credentials —
just open files (STAC + Apache Iceberg + GeoParquet) that any modern engine can read directly
over HTTPS.

It holds one dataset from **Helsinki Region Environmental Services (HSY)**: `seuturamava_kortteli`
— per-plan-block land-use category and unused building-rights reserve (SeutuRAMAVA), across
Espoo / Vantaa / Kauniainen.

## Layout

```
catalog.json                                  STAC Catalog — the directory
items/seuturamava_kortteli.json               STAC Item — metadata, bbox, semantics, data href
data/v2/hsy_zoning/
  metadata/v1.metadata.json                   Apache Iceberg table metadata
  metadata/snap-*-manifest-list.avro          Iceberg manifest list
  metadata/snap-*-manifest.avro               Iceberg manifest
  data/hsy_zoning.parquet                     GeoParquet data (WKB + bbox)
```

## Query it directly with DuckDB

The Iceberg table is read straight from its metadata file over HTTPS — no catalog server:

```sql
INSTALL iceberg; LOAD iceberg; INSTALL httpfs; LOAD httpfs; INSTALL spatial; LOAD spatial;
SET geometry_always_xy = true;

SELECT kunta, korttunnus,
       laskvar_ak AS unused_apartment_rights_m2,
       laskvar_t  AS unused_industrial_rights_m2,
       ST_AsText(ST_GeomFromWKB(geom_wkb)) AS geom
FROM iceberg_scan('https://jatorre.github.io/portolan-hsy-catalog/data/v2/hsy_zoning/metadata/v1.metadata.json')
WHERE laskvar_ak > 0
LIMIT 5;
```

Discover it the Portolan way — read [`catalog.json`](https://jatorre.github.io/portolan-hsy-catalog/catalog.json),
follow the item link, take the asset `data.href`, and `iceberg_scan()` it.

## Contributing — closing the loop

Found a data or metadata error, or want to improve this catalog? **Open an issue or a pull
request on this repository.** Because the catalog is a git repo, contributing to the *data*
works exactly like contributing to *software*: a PR that updates the Iceberg files or the STAC
metadata, reviewed and merged by the maintainer, with full version history.

> ⚠️ **Interim, not sovereign.** GitHub Pages is US-hosted (Fastly CDN). This repo demonstrates
> the *repo-as-catalog* model; it is **not** a sovereign deployment. The sovereign form is the
> identical static files hosted on European infrastructure (e.g. UpCloud object storage, or a
> self-hosted Forgejo/GitLab Pages on EU infra) — same bytes, different host.

## Part of a federation

This catalog is one child of the Portolan Helsinki *catalog of catalogs*:
`https://8et4c.upcloudobjects.com/carto-ogc-connect-helsinki/catalog/stac.json`

Data: HSY, licensed CC-BY-4.0.
