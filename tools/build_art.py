#!/usr/bin/env python3
"""The module's art from WoW Forever's own build: the Pack Kodo, the pack mule (the Minimule and the Pack
Mule mount), the signpost toys' posts and signs, the tabards' textures and the icons the client lacks.

    python3 build_art.py --creatures /path/to/wow-mod-retail-creatures --cache <Forever download cache> \\
        --dbc <folder> --client /path/to/3.3.5a/client --work <folder> --out patch-supply-art.MPQ

The models go through wow-mod-retail-creatures' converter (tools/build_patch.py, with this repo's pack.json
and data/looks.tsv), which reads Forever's files from Blizzard's CDN (TACT product wowf) into --cache, and
the DB2 tables of the same build from wago.tools into <cache>/db2. --cache must be Forever's alone: retail
shares its file ids.

--dbc holds the CreatureDisplayInfo.dbc, CreatureModelData.dbc, AnimationData.dbc and ParticleColor.dbc the
players have: the client's, or those of the patch that ships them last. The new display and model rows go
on top of those copies, so the patch with them has to load after that one.

--out gets the models, their textures, those two tables, the tabards' textures and every icon of
catalog.ART_ICONS the client (--client's own archives, not a realm's patch-<name>.MPQ, plus any --have
patches) doesn't have yet. Never pass a patch that holds an earlier build of this art as --have. With --tables-out, the
two tables go there instead, so the art can ship in any patch and the tables in the one loaded last. --sql (by default
data/sql/db-world/mod_supply_logistics_art.sql) gets the server's copy of the display and model rows.

Released under the MIT License.
"""

import argparse
import csv
import io
import os
import re
import sys
import tempfile
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.normpath(os.path.join(HERE, ".."))
sys.path.insert(0, HERE)
import dbcmpq  # noqa: E402
from catalog import art_files  # noqa: E402

FOREVER = "1.60."
WAGO = "https://wago.tools/db2/%s/csv?build=%s"
# Every DB2 table the converter reads (fetch.db2 / db2_rows): its own downloader takes the latest retail
# build, so they are put in the cache first, from Forever's build.
TABLES = ["CreatureDisplayInfo", "CreatureModelData", "CreatureDisplayInfoGeosetData", "ParticleColor",
          "TextureFileData", "ChrModel", "ChrCustomizationOption", "ChrCustomizationChoice", "ChrCustomizationElement",
          "ChrModelTextureLayer", "ChrCustomizationMaterial", "ChrCustomizationGeoset"]


def fetch_tables(cache, version):
    folder = os.path.join(cache, "db2")
    os.makedirs(folder, exist_ok=True)
    for table in TABLES:
        path = os.path.join(folder, table + ".csv")
        if os.path.exists(path) and os.path.getsize(path) > 64:
            continue
        req = urllib.request.Request(WAGO % (table, version), headers={"User-Agent": "wow-mod-supply-logistics/1.0"})
        with urllib.request.urlopen(req, timeout=180) as r:
            data = r.read()
        next(csv.reader(io.StringIO(data[:4096].decode("utf-8", "replace"))))   # a CSV header, not an error page
        with open(path + ".part", "wb") as f:
            f.write(data)
        os.replace(path + ".part", path)
        print("db2 %s (%d bytes)" % (table, len(data)))


def client_has(handles, lib, name):
    return any(lib.SFileHasFile(h, name.encode("latin-1")) for h in handles)


# A realm's own patches (patch-<more than one letter>.MPQ, other than Blizzard's locale ones) may hold this
# art from an earlier build: an icon found only there would be left out of the patch that replaces it.
OWN_PATCH = re.compile(r"^patch-(?!enus)[^.]{2,}\.mpq$", re.I)


def open_client(lib, H, client, have):
    """The client's own archives (Blizzard's, and one-letter patches such as an HD pack's) and the --have
    patches: only to ask whether a file is there."""
    import ctypes
    import glob
    paths = sorted(glob.glob(os.path.join(client, "Data", "*.[mM][pP][qQ]")))
    paths += sorted(glob.glob(os.path.join(client, "Data", "*", "*.[mM][pP][qQ]")))
    paths = [p for p in paths if not OWN_PATCH.match(os.path.basename(p))]
    handles = []
    for path in paths + list(have or []):
        h = H()
        if lib.SFileOpenArchive(path.encode(), 0, 0x100, ctypes.byref(h)):
            handles.append(h)
    return handles


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--creatures", required=True, help="a checkout of wow-mod-retail-creatures")
    ap.add_argument("--cache", required=True, help="the download cache for Forever's build (its own)")
    ap.add_argument("--dbc", required=True)
    ap.add_argument("--client", required=True, help="a 3.3.5a client folder: icons it has are left out")
    ap.add_argument("--have", nargs="*", help="more patches the players have, for the same check")
    ap.add_argument("--work", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--tables-out", help="write the two tables to this patch, not to --out")
    ap.add_argument("--sql", default=os.path.join(REPO, "data", "sql", "db-world", "mod_supply_logistics_art.sql"))
    ap.add_argument("--max-texture", type=int, default=1024)
    args = ap.parse_args()

    os.environ["RETAIL_SOURCE"] = "cdn"
    os.environ.pop("RETAIL_FALLBACK_CACHE", None)
    tools = os.path.join(os.path.abspath(args.creatures), "tools")
    sys.path.insert(0, tools)
    import build_patch as converter  # noqa: E402  (wow-mod-retail-creatures)
    import fetch  # noqa: E402
    from tact import Tact  # noqa: E402

    cache = os.path.abspath(args.cache)
    build = fetch._tact[cache] = Tact(cache, product="wowf")
    if not build.version.startswith(FOREVER):
        sys.exit("%s holds build %s, not Forever's: give Forever a cache of its own" % (cache, build.version))
    print("Forever build", build.version)
    fetch_tables(cache, build.version)

    os.makedirs(args.work, exist_ok=True)
    models = os.path.join(args.work, "models.MPQ")
    sql = os.path.join(args.work, "art.sql")
    sys.argv = ["build_patch.py", "--pack", REPO, "--dbc", args.dbc, "--cache", cache, "--work",
                os.path.join(args.work, "convert"), "--out", models, "--sql", sql, "--max-texture", str(args.max_texture)]
    converter.main()

    lib, H = dbcmpq.stormlib()
    handles = open_client(lib, H, os.path.abspath(args.client), args.have)
    with tempfile.TemporaryDirectory() as tmp:
        files = dbcmpq.unpack(models, tmp)
        added = skipped = 0
        for name, fd in sorted(art_files().items()):
            if name.startswith("Interface\\") and client_has(handles, lib, name):
                skipped += 1
                continue
            local = os.path.join(tmp, "art_%d" % fd)
            with open(local, "wb") as f:
                f.write(fetch.casc(cache, fd, "cdn"))
            files[name] = local
            added += 1
        for h in handles:
            lib.SFileCloseArchive(h)
        tables = {n: f for n, f in files.items() if n.startswith("DBFilesClient\\")} if args.tables_out else {}
        art = {n: f for n, f in files.items() if n not in tables}
        dbcmpq.pack(args.out, [(local, name) for name, local in sorted(art.items())])
        print("%s: %d files (%d textures and icons added, %d icons the client has), %.1f MB" % (
            args.out, len(art), added, skipped, os.path.getsize(args.out) / 1e6))
        if tables:
            dbcmpq.pack(args.tables_out, [(local, name) for name, local in sorted(tables.items())])
            print("%s: %s" % (args.tables_out, ", ".join(sorted(tables))))

    with open(sql, encoding="utf-8") as f:
        text = f.read()
    with open(args.sql, "w", encoding="utf-8") as f:
        f.write("-- mod-supply-logistics: the creature displays and models of the client patch tools/build_art.py writes\n"
                "-- (Forever's Pack Kodo, pack mule, signposts and signs). Generated: run the tool again, don't edit.\n")
        f.write(text)
    print("wrote", args.sql)


if __name__ == "__main__":
    main()
