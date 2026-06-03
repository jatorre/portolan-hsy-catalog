#!/usr/bin/env python3
"""Publish this repo's catalog to an object-storage bucket as a static Apache Iceberg
REST catalog — so DuckDB / Snowflake can ATTACH it.

The git repo is the *source* (collision-free: STAC + Iceberg table files). The Iceberg
REST API responses (config / namespaces / tables / table-load) are *generated* here and
written straight to the bucket as object keys via `mc pipe`. They are never materialized
on a filesystem — which is why this works on a flat-keyspace object store but not on a
filesystem-backed host like GitHub Pages (where `namespaces` can't be both file and dir).

Env:
  MC_TARGET    mc path prefix to publish under, e.g. upcloud/bucket/repo/portolan-hsy-catalog
  PUBLIC_BASE  the public HTTPS URL of that same prefix (baked into the table metadata)
Usage: python tools/publish.py   (run from the repo root)
"""
import json, os, subprocess, sys, glob

MC_TARGET = os.environ["MC_TARGET"].rstrip("/")
PUBLIC_BASE = os.environ["PUBLIC_BASE"].rstrip("/")
PREFIX = "sdi"  # Iceberg REST catalog prefix (see /v1/config overrides)
REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(REPO)


def put(key: str, body: str):
    """Write `body` to <MC_TARGET>/<key> as a single object (no filesystem, no collision)."""
    dest = f"{MC_TARGET}/{key}"
    p = subprocess.run(["mc", "pipe", dest], input=body.encode(), capture_output=True)
    if p.returncode != 0:
        sys.exit(f"mc pipe {dest} failed: {p.stderr.decode()}")
    print(f"  put {key}")


def discover_tables():
    """Each data/<namespace>/<table>/metadata/v1.metadata.json is a table."""
    tables = {}
    for mp in glob.glob("data/*/*/metadata/v1.metadata.json"):
        _, ns, table, _, _ = mp.split("/")
        tables.setdefault(ns, {})[table] = mp
    return tables


def main():
    tables = discover_tables()

    # 1) Mirror only the Iceberg METADATA (small: metadata.json + manifests) from git.
    #    The DATA bytes (parquet) live ONLY on the bucket and are uploaded out-of-band
    #    (see README "Contributing data"), so we never push or prune them here.
    print("mirroring metadata ->", MC_TARGET + "/data/  (data/*.parquet excluded)")
    subprocess.run(["mc", "mirror", "--overwrite", "data/", f"{MC_TARGET}/data/",
                    "--exclude", "**/data/**"], check=True)

    # sanity: warn (don't fail) if a table's data bytes aren't on the bucket yet
    for ns, tbls in tables.items():
        for table in tbls:
            r = subprocess.run(["mc", "ls", f"{MC_TARGET}/data/{ns}/{table}/data/"],
                               capture_output=True, text=True)
            if r.returncode != 0 or not r.stdout.strip():
                print(f"  ::warning:: no data bytes on bucket for {ns}.{table} — "
                      f"upload the parquet to {MC_TARGET}/data/{ns}/{table}/data/")

    # 2) generate the Iceberg REST catalog responses, write them as object keys
    print("generating REST catalog tree")
    put(f"v1/config", json.dumps({
        "defaults": {}, "overrides": {"prefix": PREFIX},
        "endpoints": [
            "GET /v1/{prefix}/namespaces",
            "GET /v1/{prefix}/namespaces/{namespace}",
            "GET /v1/{prefix}/namespaces/{namespace}/tables",
            "GET /v1/{prefix}/namespaces/{namespace}/tables/{table}",
        ],
    }))
    put(f"v1/{PREFIX}/namespaces",
        json.dumps({"namespaces": [[ns] for ns in tables]}))
    for ns, tbls in tables.items():
        put(f"v1/{PREFIX}/namespaces/{ns}",
            json.dumps({"namespace": [ns], "properties": {}}))
        put(f"v1/{PREFIX}/namespaces/{ns}/tables",
            json.dumps({"identifiers": [{"namespace": [ns], "name": t} for t in tbls]}))
        for table, mp in tbls.items():
            metadata = json.load(open(mp))
            put(f"v1/{PREFIX}/namespaces/{ns}/tables/{table}", json.dumps({
                "metadata-location": f"{PUBLIC_BASE}/{mp}",
                "metadata": metadata,
                "config": {},
            }))

    # 3) mirror the catalogue metadata documents (STAC + OGC API - Records views).
    #    Same GeoJSON model, two vocabularies — both served as static files on the bucket.
    print("mirroring catalogue docs (STAC catalog.json/items + OGC API - Records records/)")
    subprocess.run(["mc", "cp", "catalog.json", f"{MC_TARGET}/catalog.json"], check=True)
    for d in ("items", "records"):
        if os.path.isdir(d):
            subprocess.run(["mc", "mirror", "--overwrite", f"{d}/", f"{MC_TARGET}/{d}/"], check=True)

    print(f"\nPublished. ATTACH endpoint:\n  {PUBLIC_BASE}")
    print("  ATTACH 'cat' (TYPE iceberg, ENDPOINT '%s', AUTHORIZATION_TYPE 'none');" % PUBLIC_BASE)


if __name__ == "__main__":
    main()
