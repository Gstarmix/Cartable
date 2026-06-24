from __future__ import annotations
import argparse
import json
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path
API = "https://discord.com/api/v10"
GUILD_ID = "1475846763909873727"
PROJECT_ROOT = Path(__file__).resolve().parent.parent
ABOEKA_ENV = PROJECT_ROOT.parent / "AboekaBot" / ".env"
CHANNELS_OUT = PROJECT_ROOT / "_contexte" / "discord_channels.json"
MATIERES: list[tuple[str, str, bool]] = [
    ("S1", "Droit des personnes", True),
    ("S1", "Droit constitutionnel 1", True),
    ("S1", "Histoire des institutions publiques", True),
    ("S1", "Introduction au droit & juridictions", False),
    ("S1", "Organisations européennes", False),
    ("S2", "Droit de la famille", True),
    ("S2", "Droit constitutionnel 2", True),
    ("S2", "Histoire des sources du droit", False),
    ("S2", "Institutions administratives", False),
    ("S2", "Histoire du droit des personnes et de la famille", False),
    ("S2", "Relations internationales", False),
    ("S2", "Introduction à la science politique", False),
    ("S2", "Anglais", False),
]
CHANS_TD = ["audio-cm", "audio-td", "transcript-cm", "transcript-td",
            "resumes", "methodo", "arrets-annales", "inbox"]
CHANS_CM = ["audio-cm", "transcript-cm", "resumes", "inbox"]
EMOJI_SEM = {"S1": "📕", "S2": "📗"}
def _build_structure() -> list[tuple[str, list[str]]]:
    out: list[tuple[str, list[str]]] = [
        ("🎓 GÉNÉRAL", ["annonces", "methodo-juridique", "cartable-logs"]),
    ]
    for sem, nom, has_td in MATIERES:
        cat = f"{EMOJI_SEM[sem]} {sem} · {nom}"
        out.append((cat, CHANS_TD if has_td else CHANS_CM))
    return out
STRUCTURE: list[tuple[str, list[str]]] = _build_structure()
def get_token() -> str:
    import os
    tok = os.environ.get("DISCORD_BOT_TOKEN")
    if tok:
        return tok.strip()
    if ABOEKA_ENV.is_file():
        for line in ABOEKA_ENV.read_text(encoding="utf-8").splitlines():
            if line.startswith("DISCORD_BOT_TOKEN="):
                return line.split("=", 1)[1].strip()
    sys.exit(f"Token introuvable (ni $DISCORD_BOT_TOKEN ni {ABOEKA_ENV})")
def api(method: str, path: str, token: str, body: dict | None = None) -> object:
    url = f"{API}{path}"
    data = json.dumps(body).encode() if body is not None else None
    for attempt in range(6):
        req = urllib.request.Request(url, data=data, method=method)
        req.add_header("Authorization", f"Bot {token}")
        req.add_header("Content-Type", "application/json")
        req.add_header("User-Agent", "CartableSetup (https://github.com/Gstarmix, 0.1)")
        try:
            with urllib.request.urlopen(req) as r:
                raw = r.read().decode()
                return json.loads(raw) if raw else None
        except urllib.error.HTTPError as e:
            if e.code == 429:
                retry = 1.5
                try:
                    retry = float(json.loads(e.read().decode()).get("retry_after", 1.5))
                except Exception:
                    pass
                print(f"   …rate-limit, pause {retry:.1f}s")
                time.sleep(retry + 0.3)
                continue
            raise SystemExit(f"HTTP {e.code} sur {method} {path} : {e.read().decode()}")
    raise SystemExit(f"Abandon apres 6 essais sur {method} {path}")
def list_channels(token: str) -> list[dict]:
    return api("GET", f"/guilds/{GUILD_ID}/channels", token)
def cmd_list(token: str) -> None:
    chans = list_channels(token)
    types = {0: "text", 2: "voice", 4: "CATEGORY", 5: "announce", 15: "forum"}
    cats = {c["id"]: c["name"] for c in chans if c["type"] == 4}
    for c in sorted(chans, key=lambda x: x.get("position", 0)):
        if c["type"] == 4:
            print(f"\n[{c['name']}]")
        else:
            print(f"   {types.get(c['type'], c['type']):8} #{c['name']}  "
                  f"(parent={cats.get(c.get('parent_id'), '-')})")
def disable_community(token: str) -> None:
    g = api("GET", f"/guilds/{GUILD_ID}", token)
    feats = list(g.get("features", []))
    if "COMMUNITY" in feats:
        feats.remove("COMMUNITY")
        api("PATCH", f"/guilds/{GUILD_ID}", token, {"features": feats})
        print("   mode Communaute desactive")
        time.sleep(0.5)
def cmd_wipe(token: str) -> None:
    disable_community(token)
    chans = list_channels(token)
    non_cat = [c for c in chans if c["type"] != 4]
    cat = [c for c in chans if c["type"] == 4]
    for c in non_cat + cat:
        print(f"   ✗ delete #{c['name']} ({c['id']})")
        api("DELETE", f"/channels/{c['id']}", token)
        time.sleep(0.4)
    print(f"Wipe termine : {len(chans)} salons/categories supprimes.")
def cmd_rename(token: str, name: str = "Cartable") -> None:
    api("PATCH", f"/guilds/{GUILD_ID}", token, {"name": name})
    print(f"Serveur renomme en « {name} ».")
def cmd_create(token: str) -> None:
    chans = list_channels(token)
    cats_by_name = {c["name"]: c for c in chans if c["type"] == 4}
    by_parent_name = {(c.get("parent_id"), c["name"]): c
                      for c in chans if c["type"] == 0}
    result: dict[str, dict] = {}
    for cat_name, salons in STRUCTURE:
        if cat_name in cats_by_name:
            cat = cats_by_name[cat_name]
            print(f"   = categorie existe : {cat_name}")
        else:
            cat = api("POST", f"/guilds/{GUILD_ID}/channels", token,
                      {"name": cat_name, "type": 4})
            print(f"   + categorie : {cat_name}")
            time.sleep(0.4)
        result[cat_name] = {"id": cat["id"], "channels": {}}
        for s in salons:
            key = (cat["id"], s)
            if key in by_parent_name:
                ch = by_parent_name[key]
                print(f"      = #{s}")
            else:
                ch = api("POST", f"/guilds/{GUILD_ID}/channels", token,
                         {"name": s, "type": 0, "parent_id": cat["id"]})
                print(f"      + #{s}")
                time.sleep(0.4)
            result[cat_name]["channels"][s] = ch["id"]
    CHANNELS_OUT.parent.mkdir(parents=True, exist_ok=True)
    CHANNELS_OUT.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"IDs ecrits dans {CHANNELS_OUT}")
def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--wipe", action="store_true")
    p.add_argument("--rename", action="store_true")
    p.add_argument("--create", action="store_true")
    p.add_argument("--list", action="store_true")
    a = p.parse_args()
    token = get_token()
    if not any([a.wipe, a.rename, a.create, a.list]):
        cmd_list(token)
        return
    if a.wipe:
        print("== WIPE =="); cmd_wipe(token)
    if a.rename:
        print("== RENAME =="); cmd_rename(token)
    if a.create:
        print("== CREATE =="); cmd_create(token)
    if a.list:
        print("== LIST =="); cmd_list(token)
if __name__ == "__main__":
    main()