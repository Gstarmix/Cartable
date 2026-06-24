from __future__ import annotations
import argparse
import os
import re
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
import matieres
ROOT = Path(__file__).resolve().parent.parent
DROIT = ROOT / "DROIT"
MODEL = "large-v3"
LANG = "fr"
BEAM_SIZE = 5
TEMPERATURE = 0.0
VAD_THRESHOLD = 0.35
CANONICAL_RE = re.compile(
    r"^(?P<type>CM|TD)(?P<num>\d+)_(?P<slug>[a-z0-9-]+)_(?P<date>\d{3,8})$",
    re.IGNORECASE,
)
def fmt_duration(seconds: float) -> str:
    if seconds < 60:
        return f"{seconds:.0f}s"
    m, s = divmod(int(seconds), 60)
    if m < 60:
        return f"{m}m{s:02d}s"
    h, m = divmod(m, 60)
    return f"{h}h{m:02d}m"
def detect_date(basename: str, fallback: datetime) -> str:
    if m := re.search(r"(\d{2})(\d{2})(\d{4})$", basename):
        jj, mm, aaaa = m.groups()
        return f"{jj}/{mm}/{aaaa}"
    if m := re.search(r"(\d{2})(\d{2})$", basename):
        jj, mm = m.groups()
        return f"{jj}/{mm}/{fallback.year}"
    return fallback.strftime("%d/%m/%Y") + " (date fichier)"
def resolve_target(audio: Path, slug: str | None, typ: str | None,
                   out: Path | None) -> tuple[Path, matieres.Matiere | None, str]:
    if out:
        return out, (matieres.get(slug) if slug else None), (typ or "CM").upper()
    m = CANONICAL_RE.match(audio.stem)
    if not slug and m:
        slug = m.group("slug")
    if not typ and m:
        typ = m.group("type")
    typ = (typ or "CM").upper()
    if not slug:
        sys.exit("[ERR] Matière indéterminée : nom de fichier non canonique. "
                 "Donne --matiere <slug> (et --type CM|TD).")
    mat = matieres.get(slug)
    if mat is None:
        sys.exit(f"[ERR] Slug inconnu : '{slug}'. "
                 f"Slugs valides : {', '.join(matieres.slugs())}")
    if typ == "TD" and not mat.has_td:
        sys.exit(f"[ERR] '{mat.slug}' n'a pas de TD (mineure CM seul).")
    subdir = "CM/transcriptions" if typ == "CM" else "TD"
    target = DROIT / mat.slug / subdir / f"{audio.stem}.txt"
    return target, mat, typ
def setup_nvidia_dlls() -> int:
    site = next((p for p in sys.path if "site-packages" in p and os.path.isdir(p)), None)
    if not site:
        return 0
    nvidia = os.path.join(site, "nvidia")
    if not os.path.isdir(nvidia):
        return 0
    dirs = [r for r, _, _ in os.walk(nvidia) if os.path.basename(r) in ("bin", "lib")]
    if dirs:
        os.environ["PATH"] = ";".join(dirs) + ";" + os.environ.get("PATH", "")
        if hasattr(os, "add_dll_directory"):
            for d in dirs:
                try:
                    os.add_dll_directory(d)
                except OSError:
                    pass
    return len(dirs)
def detect_device() -> tuple[str, str]:
    try:
        import ctranslate2
        if ctranslate2.get_cuda_device_count() > 0:
            return "cuda", "int8_float16"
    except Exception:
        pass
    return "cpu", "int8"
def transcribe(audio: Path, out_txt: Path) -> None:
    n = setup_nvidia_dlls()
    if n:
        print(f"[*] DLL NVIDIA ajoutées au PATH ({n} dirs).")
    from faster_whisper import WhisperModel
    device, compute = detect_device()
    print("=" * 70)
    print(f"transcribe.py : faster-whisper {MODEL}")
    print(f"  Audio  : {audio.name}")
    print(f"  Sortie : {out_txt}")
    print(f"  Device : {device.upper()} ({compute}) | beam {BEAM_SIZE} | VAD on")
    print("=" * 70)
    sys.stdout.flush()
    t0 = time.monotonic()
    print(f"[*] Chargement du modèle…")
    sys.stdout.flush()
    model = WhisperModel(MODEL, device=device, compute_type=compute,
                         cpu_threads=os.cpu_count() if device == "cpu" else 4)
    print(f"[OK] Modèle chargé en {time.monotonic() - t0:.1f}s")
    t1 = time.monotonic()
    segments, info = model.transcribe(
        str(audio), language=LANG, task="transcribe",
        beam_size=BEAM_SIZE, temperature=TEMPERATURE, best_of=1,
        vad_filter=True,
        vad_parameters={"threshold": VAD_THRESHOLD, "min_speech_duration_ms": 250,
                        "min_silence_duration_ms": 1000, "speech_pad_ms": 250},
        condition_on_previous_text=False,
        no_speech_threshold=0.6, log_prob_threshold=-1.0,
        compression_ratio_threshold=2.4, word_timestamps=False,
    )
    duration = info.duration or 0
    print(f"[*] Durée audio {fmt_duration(duration)} | langue {info.language} "
          f"({info.language_probability:.2f})")
    sys.stdout.flush()
    out_txt.parent.mkdir(parents=True, exist_ok=True)
    count, last = 0, 0.0
    with out_txt.open("w", encoding="utf-8") as fh:
        for seg in segments:
            count += 1
            fh.write(seg.text.strip() + "\n")
            fh.flush()
            elapsed = time.monotonic() - t1
            if duration > 0 and (seg.end - last >= 30.0 or seg.end >= duration):
                last = seg.end
                pct = min(100.0, seg.end / duration * 100)
                speed = seg.end / elapsed if elapsed > 0 else 0
                eta = (duration - seg.end) / speed if speed > 0 else 0
                bar = "#" * int(30 * pct / 100) + "-" * (30 - int(30 * pct / 100))
                print(f"  [{bar}] {pct:5.1f}% | {fmt_duration(seg.end)}/"
                      f"{fmt_duration(duration)} | x{speed:.1f} | ETA {fmt_duration(eta)}")
                sys.stdout.flush()
    elapsed = time.monotonic() - t1
    ratio = duration / elapsed if elapsed > 0 else 0
    print(f"[OK] {count} segments en {fmt_duration(elapsed)} (x{ratio:.1f} realtime)")
    fallback = datetime.fromtimestamp(audio.stat().st_mtime)
    sep = "=" * 70
    header = "\n".join([
        sep,
        f"FICHIER SOURCE   : {audio.stem}",
        f"DATE DU COURS    : {detect_date(audio.stem, fallback)}",
        f"TRANSCRIPTION    : {datetime.now():%d/%m/%Y %H:%M}",
        f"MODELE           : {MODEL} ({compute} / {device.upper()})",
        f"DUREE AUDIO      : {fmt_duration(duration)}",
        f"TEMPS TRAITEMENT : {fmt_duration(elapsed)} (x{ratio:.1f} realtime)",
        f"SEGMENTS         : {count}",
        sep, "", "",
    ])
    out_txt.write_text(header + out_txt.read_text(encoding="utf-8"), encoding="utf-8")
    print(f"[OK] {out_txt}")
def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("audio", type=Path, help="Fichier audio à transcrire")
    ap.add_argument("--matiere", help="Slug matière (cf. matieres.py) si nom non canonique")
    ap.add_argument("--type", choices=["CM", "TD", "cm", "td"], help="CM ou TD")
    ap.add_argument("--out", type=Path, help="Fichier .txt cible explicite (override routage)")
    ap.add_argument("--publish", action="store_true",
                    help="Poste la transcription sur Discord (transcript-cm/td) après coup")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    audio = args.audio.resolve()
    if not audio.exists():
        print(f"[ERR] Audio introuvable : {audio}", file=sys.stderr)
        return 1
    out_txt, mat, typ = resolve_target(audio, args.matiere, args.type, args.out)
    print(f"[*] Audio  : {audio}")
    print(f"[*] Cible  : {out_txt}")
    if mat:
        print(f"[*] Matière : {mat.slug} ({typ}), {mat.libelle}")
    if out_txt.exists() and out_txt.stat().st_size > 0:
        print(f"[SKIP] Sortie déjà présente : {out_txt}")
    elif args.dry_run:
        print("[*] Dry-run : pas d'exécution.")
        return 0
    else:
        if out_txt.exists():
            out_txt.unlink()
        transcribe(audio, out_txt)
    if args.publish:
        if not mat:
            print("[WARN] --publish ignoré : matière inconnue (donne --matiere).",
                  file=sys.stderr)
        else:
            salon = "transcript-cm" if typ == "CM" else "transcript-td"
            print(f"[*] Publication Discord -> {mat.slug}/{salon}")
            rc = subprocess.run([
                sys.executable, str(Path(__file__).with_name("publish_discord.py")),
                str(out_txt), "--matiere", mat.slug, "--salon", salon,
            ]).returncode
            if rc != 0:
                print(f"[WARN] publish_discord.py exit={rc}", file=sys.stderr)
    return 0
if __name__ == "__main__":
    raise SystemExit(main())