from __future__ import annotations
import argparse
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path
import matieres
ROOT = Path(__file__).resolve().parent.parent
DROIT = ROOT / "DROIT"
CANONICAL_RE = re.compile(
    r"^(?P<type>CM|TD)(?P<num>\d+)_(?P<slug>[a-z0-9-]+)_(?P<date>\d{3,8})$",
    re.IGNORECASE,
)
PROMPT_SYSTEME = """\
Tu es un assistant pédagogique pour un étudiant en L1 Droit (parcours général,
université de Rennes). On te donne le TEXTE BRUT d'un cours de droit (transcription
audio d'un CM/TD, ou poly). Produis une FICHE DE RÉVISION en Markdown, en français,
claire et fidèle au contenu, sans rien inventer qui ne soit pas dans le texte.
Structure attendue de la fiche :
# <Titre du cours / thème principal>
## Plan du cours
Le plan logique (parties, sous-parties) tel qu'il ressort du cours.
## Notions clés
Les concepts essentiels, en puces concises.
## Définitions
Le terme suivi de sa définition, pour chaque terme juridique important du cours.
## Jurisprudence & textes cités
Arrêts, articles de loi/code, textes fondamentaux mentionnés (avec ce que le
cours en dit). Mettre « Aucun cité explicitement » si rien.
## Points de méthodo
Conseils de méthode juridique évoqués (dissertation, commentaire/fiche d'arrêt,
cas pratique...). Omettre la section si rien.
## Questions de révision
5 à 8 questions courtes permettant de s'auto-interroger sur le cours.
Contraintes :
- Markdown pur, pas de bloc de code englobant.
- Rester synthétique : une fiche, pas une retranscription.
- Si la transcription est confuse/bruitée par endroits, lisser sans extrapoler.
"""
def strip_header(text: str) -> str:
    lines = text.splitlines()
    if lines and set(lines[0].strip()) == {"="}:
        for i in range(1, len(lines)):
            if set(lines[i].strip()) == {"="}:
                return "\n".join(lines[i + 1:]).lstrip("\n")
    return text
def resolve_target(src: Path, slug: str | None, typ: str | None,
                   out: Path | None) -> tuple[Path, matieres.Matiere | None, str]:
    if out:
        return out, (matieres.get(slug) if slug else None), (typ or "CM").upper()
    m = CANONICAL_RE.match(src.stem)
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
    subdir = "CM/fiches" if typ == "CM" else "TD"
    target = DROIT / mat.slug / subdir / f"fiche_{src.stem}.md"
    return target, mat, typ
def claude_env() -> dict[str, str]:
    env = os.environ.copy()
    env.pop("ANTHROPIC_API_KEY", None)
    env.pop("ANTHROPIC_AUTH_TOKEN", None)
    return env
def generate(prompt: str) -> str:
    try:
        with tempfile.TemporaryDirectory(prefix="cartable_fiche_") as tmp:
            proc = subprocess.run(
                ["claude", "--print"],
                input=prompt, capture_output=True, text=True,
                encoding="utf-8", env=claude_env(), cwd=tmp,
            )
    except FileNotFoundError:
        sys.exit("[ERR] CLI 'claude' introuvable dans le PATH.")
    if proc.returncode != 0:
        sys.exit(f"[ERR] claude --print exit={proc.returncode} :\n"
                 f"{(proc.stderr or proc.stdout).strip()}")
    out = (proc.stdout or "").strip()
    if not out:
        sys.exit("[ERR] claude --print n'a rien renvoyé "
                 "(abonnement épuisé ? ANTHROPIC_API_KEY interférente ?).")
    if out.startswith("```"):
        out = re.sub(r"^```[a-zA-Z]*\n", "", out)
        out = re.sub(r"\n```$", "", out)
    return out.strip() + "\n"
def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("source", type=Path, help="Transcription .txt (ou poly texte)")
    ap.add_argument("--matiere", help="Slug matière (cf. matieres.py) si nom non canonique")
    ap.add_argument("--type", choices=["CM", "TD", "cm", "td"], help="CM ou TD")
    ap.add_argument("--out", type=Path, help="Fichier .md cible explicite (override routage)")
    ap.add_argument("--publish", action="store_true",
                    help="Poste la fiche sur Discord (#resumes) après génération")
    ap.add_argument("--force", action="store_true", help="Régénère même si la fiche existe")
    ap.add_argument("--dry-run", action="store_true", help="Montre le prompt, n'appelle pas claude")
    args = ap.parse_args()
    src = args.source.resolve()
    if not src.is_file():
        print(f"[ERR] Source introuvable : {src}", file=sys.stderr)
        return 1
    typ_arg = args.type.upper() if args.type else None
    out_md, mat, typ = resolve_target(src, args.matiere, typ_arg, args.out)
    print(f"[*] Source : {src}")
    print(f"[*] Cible  : {out_md}")
    if mat:
        print(f"[*] Matiere : {mat.slug} ({typ}), {mat.libelle}")
    if out_md.exists() and out_md.stat().st_size > 0 and not args.force and not args.dry_run:
        print(f"[SKIP] Fiche déjà présente : {out_md} (-force pour régénérer).")
    else:
        contenu = strip_header(src.read_text(encoding="utf-8"))
        if not contenu.strip():
            print("[ERR] Source vide après retrait de l'en-tête.", file=sys.stderr)
            return 1
        prompt = f"{PROMPT_SYSTEME}\n\n=== TEXTE DU COURS ===\n{contenu}\n=== FIN ==="
        if args.dry_run:
            print("-" * 70)
            print(prompt[:1500] + ("\n[…tronqué…]" if len(prompt) > 1500 else ""))
            print("-" * 70)
            print(f"[*] Dry-run : {len(contenu)} caractères de cours, pas d'appel claude.")
            return 0
        print("[*] Génération via claude --print (abonnement)…")
        fiche = generate(prompt)
        out_md.parent.mkdir(parents=True, exist_ok=True)
        out_md.write_text(fiche, encoding="utf-8")
        print(f"[OK] Fiche écrite ({len(fiche)} car.) : {out_md}")
    if args.publish:
        if not mat:
            print("[WARN] --publish ignoré : matière inconnue (donne --matiere).",
                  file=sys.stderr)
        else:
            print(f"[*] Publication Discord -> {mat.slug}/resumes")
            rc = subprocess.run([
                sys.executable, str(Path(__file__).with_name("publish_discord.py")),
                str(out_md), "--matiere", mat.slug, "--salon", "resumes",
            ]).returncode
            if rc != 0:
                print(f"[WARN] publish_discord.py exit={rc}", file=sys.stderr)
    return 0
if __name__ == "__main__":
    raise SystemExit(main())