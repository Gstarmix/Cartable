from __future__ import annotations
import argparse
from pathlib import Path
import matieres
ROOT = Path(__file__).resolve().parent.parent
DROIT = ROOT / "DROIT"
LEAVES_COMMON = ["CM/audio", "CM/transcriptions", "CM/fiches", "methodo", "arrets"]
LEAVES_TD = ["TD"]
def leaves_for(m: matieres.Matiere) -> list[str]:
    return LEAVES_COMMON + (LEAVES_TD if m.has_td else [])
def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--semestre", choices=["S1", "S2"], help="Limiter à un semestre")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    created = 0
    for m in matieres.MATIERES:
        if args.semestre and m.semestre != args.semestre:
            continue
        for leaf in leaves_for(m):
            d = DROIT / m.slug / leaf
            keep = d / ".gitkeep"
            if keep.exists():
                continue
            if args.dry_run:
                print(f"   + {d.relative_to(ROOT)}")
                created += 1
                continue
            d.mkdir(parents=True, exist_ok=True)
            keep.touch()
            print(f"   + {d.relative_to(ROOT)}")
            created += 1
    verb = "à créer" if args.dry_run else "créés"
    print(f"{created} dossier(s) {verb}"
          + (f" (semestre {args.semestre})" if args.semestre else " (S1+S2)"))
    return 0
if __name__ == "__main__":
    raise SystemExit(main())