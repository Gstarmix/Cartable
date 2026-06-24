from __future__ import annotations
import argparse
import json
import mimetypes
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path
import matieres
API = "https://discord.com/api/v10"
ROOT = Path(__file__).resolve().parent.parent
ABOEKA_ENV = ROOT.parent / "AboekaBot" / ".env"
CHANNELS = ROOT / "_contexte" / "discord_channels.json"
DISCORD_MAX_BYTES = 25 * 1024 * 1024
def get_token() -> str:
    tok = os.environ.get("DISCORD_BOT_TOKEN")
    if tok:
        return tok.strip()
    if ABOEKA_ENV.is_file():
        for line in ABOEKA_ENV.read_text(encoding="utf-8").splitlines():
            if line.startswith("DISCORD_BOT_TOKEN="):
                return line.split("=", 1)[1].strip()
    sys.exit(f"[ERR] Token introuvable (ni $DISCORD_BOT_TOKEN ni {ABOEKA_ENV}).")
def resolve_channel(slug: str, salon: str) -> str:
    if not CHANNELS.is_file():
        sys.exit(f"[ERR] {CHANNELS} introuvable (lance setup_discord_cartable.py).")
    mat = matieres.get(slug)
    if mat is None:
        sys.exit(f"[ERR] Slug inconnu : '{slug}'. Slugs : {', '.join(matieres.slugs())}")
    data = json.loads(CHANNELS.read_text(encoding="utf-8"))
    cat = data.get(mat.categorie_discord)
    if not cat:
        sys.exit(f"[ERR] Catégorie '{mat.categorie_discord}' absente de {CHANNELS.name}.")
    cid = cat["channels"].get(salon)
    if not cid:
        dispo = ", ".join(cat["channels"])
        sys.exit(f"[ERR] Salon '{salon}' absent de {mat.slug}. Dispo : {dispo}")
    return cid
def _multipart(file_path: Path, content: str) -> tuple[bytes, str]:
    boundary = "----CartablePublish7f3b2a"
    payload = json.dumps({"content": content} if content else {}).encode()
    ctype = mimetypes.guess_type(file_path.name)[0] or "application/octet-stream"
    b = boundary.encode()
    parts = [
        b"--" + b + b"\r\n",
        b'Content-Disposition: form-data; name="payload_json"\r\n',
        b"Content-Type: application/json\r\n\r\n", payload, b"\r\n",
        b"--" + b + b"\r\n",
        f'Content-Disposition: form-data; name="files[0]"; filename="{file_path.name}"\r\n'
        .encode(),
        f"Content-Type: {ctype}\r\n\r\n".encode(),
        file_path.read_bytes(), b"\r\n",
        b"--" + b + b"--\r\n",
    ]
    return b"".join(parts), boundary
def post_file(token: str, channel_id: str, file_path: Path, content: str) -> dict:
    body, boundary = _multipart(file_path, content)
    req = urllib.request.Request(
        f"{API}/channels/{channel_id}/messages", data=body, method="POST")
    req.add_header("Authorization", f"Bot {token}")
    req.add_header("Content-Type", f"multipart/form-data; boundary={boundary}")
    req.add_header("User-Agent", "CartablePublish (https://github.com/Gstarmix, 0.1)")
    try:
        with urllib.request.urlopen(req) as r:
            return json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        sys.exit(f"[ERR] HTTP {e.code} : {e.read().decode()}")
def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("file", type=Path, help="Fichier à poster")
    ap.add_argument("--matiere", help="Slug matière (cf. matieres.py)")
    ap.add_argument("--salon", help="Nom du salon (ex: transcript-cm, resumes)")
    ap.add_argument("--channel", help="ID de salon explicite (court-circuite --matiere/--salon)")
    ap.add_argument("--message", default="", help="Texte accompagnant le fichier")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    f = args.file.resolve()
    if not f.is_file():
        print(f"[ERR] Fichier introuvable : {f}", file=sys.stderr)
        return 1
    size = f.stat().st_size
    if size > DISCORD_MAX_BYTES:
        print(f"[ERR] {f.name} fait {size/1024/1024:.1f} Mo > limite Discord "
              f"({DISCORD_MAX_BYTES/1024/1024:.0f} Mo). Non posté.", file=sys.stderr)
        return 1
    if args.channel:
        channel_id, where = args.channel, f"channel {args.channel}"
    elif args.matiere and args.salon:
        channel_id = resolve_channel(args.matiere, args.salon)
        where = f"{args.matiere}/{args.salon} ({channel_id})"
    else:
        print("[ERR] Donne --channel <id> OU --matiere <slug> --salon <nom>.",
              file=sys.stderr)
        return 2
    print(f"[*] Fichier : {f.name} ({size/1024:.0f} Ko)")
    print(f"[*] Cible   : {where}")
    if args.dry_run:
        print("[*] Dry-run : pas d'envoi.")
        return 0
    token = get_token()
    msg = post_file(token, channel_id, f, args.message)
    print(f"[OK] Posté : message {msg.get('id')} dans le salon {channel_id}.")
    return 0
if __name__ == "__main__":
    raise SystemExit(main())