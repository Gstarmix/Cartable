from __future__ import annotations
import argparse
import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
METHODO_DIR = ROOT / "DROIT" / "_methodo"
CHANNELS = ROOT / "_contexte" / "discord_channels.json"
GENERAL_CATEGORY = "🎓 GÉNÉRAL"
METHODO_SALON = "methodo-juridique"
EXERCICES: dict[str, tuple[str, str]] = {
    "dissertation": (
        "La dissertation juridique",
        "Exercice de réflexion ordonnée sur un sujet de droit. Insister sur "
        "l'analyse du sujet (termes, bornes), la problématique, et la "
        "construction d'un plan en deux parties / deux sous-parties (I/A/B, "
        "II/A/B) apparent et équilibré. Rappeler que le plan « bateau » "
        "(notion/régime, principe/exception) est à manier avec discernement.",
    ),
    "commentaire-arret": (
        "Le commentaire d'arrêt",
        "Commentaire d'une décision de justice. Détailler : lecture et "
        "compréhension de la décision, fiche d'arrêt préalable (cf. support "
        "dédié), dégager le problème de droit et la solution, puis bâtir un "
        "plan qui COMMENTE (sens, valeur, portée de la solution) sans "
        "paraphraser ni faire une dissertation déguisée.",
    ),
    "fiche-arret": (
        "La fiche d'arrêt",
        "Exercice préparatoire : résumer une décision de justice de façon "
        "structurée. Détailler les rubriques : faits, procédure (parcours "
        "judiciaire, prétentions des parties), problème de droit (sous forme "
        "de question), solution de la juridiction et motifs. Donner un "
        "exemple de fiche d'arrêt courte et bien rédigée.",
    ),
    "cas-pratique": (
        "Le cas pratique",
        "Résolution d'un problème concret par le raisonnement juridique. "
        "Mettre l'accent sur le syllogisme juridique (majeure = règle de "
        "droit applicable, mineure = qualification des faits, conclusion = "
        "application au cas). Rappeler la qualification juridique des faits, "
        "le traitement de plusieurs questions, et la rédaction (pas de plan "
        "apparent, mais un raisonnement par étapes).",
    ),
    "consultation": (
        "La consultation juridique",
        "Avis juridique rédigé à la demande d'un « client ». Proche du cas "
        "pratique mais orienté conseil : exposer la situation, identifier les "
        "problèmes de droit, appliquer les règles, et conclure par des "
        "recommandations pratiques et nuancées (risques, options).",
    ),
}
PROMPT_SYSTEME = """\
Tu es un enseignant de méthodologie juridique pour un étudiant en L1 Droit
(parcours général, université de Rennes, programme français). On te demande un
SUPPORT DE MÉTHODE clair, complet et réutilisable pour un exercice juridique
précis. Écris en français, en Markdown pur (pas de bloc de code englobant).
Sujet du support : {titre}
Consigne spécifique : {consigne}
Structure attendue du support :
# {titre}
## À quoi sert cet exercice
But pédagogique, ce que l'examinateur attend, pièges fréquents.
## Méthode pas à pas
Les étapes de travail dans l'ordre (du brouillon à la copie), en détaillant
chaque étape concrètement.
## Structure type de la copie
Le squelette attendu (introduction, développements, etc.), avec ce que doit
contenir chaque partie. Pour l'introduction, détailler ses composantes.
## Conseils de rédaction
Style, formulation, ce qu'il faut faire et surtout NE PAS faire (paraphrase,
hors-sujet, récitation de cours...).
## Exemple court
Un mini-exemple illustratif (extrait d'intro, de syllogisme, ou de fiche selon
l'exercice) pour montrer le rendu attendu. Rester bref et générique.
## Checklist avant de rendre
5 à 8 points de contrôle rapides sous forme de cases à cocher Markdown.
Contraintes :
- Rester fidèle à la méthodologie juridique française classique.
- Synthétique mais opérationnel : un étudiant doit pouvoir s'en servir seul.
- Pas d'invention de jurisprudence ; si tu cites un exemple, garde-le générique.
"""
def claude_env() -> dict[str, str]:
    env = os.environ.copy()
    env.pop("ANTHROPIC_API_KEY", None)
    env.pop("ANTHROPIC_AUTH_TOKEN", None)
    return env
def generate(prompt: str) -> str:
    try:
        with tempfile.TemporaryDirectory(prefix="cartable_methodo_") as tmp:
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
def resolve_methodo_channel() -> str | None:
    if not CHANNELS.is_file():
        return None
    data = json.loads(CHANNELS.read_text(encoding="utf-8"))
    cat = data.get(GENERAL_CATEGORY)
    if not cat:
        return None
    return cat["channels"].get(METHODO_SALON)
def publish(md_path: Path) -> int:
    cid = resolve_methodo_channel()
    if not cid:
        print(f"[WARN] Salon '{GENERAL_CATEGORY}/{METHODO_SALON}' introuvable "
              f"dans {CHANNELS.name}, publication ignorée.", file=sys.stderr)
        return 1
    print(f"[*] Publication Discord -> #{METHODO_SALON} ({cid})")
    return subprocess.run([
        sys.executable, str(Path(__file__).with_name("publish_discord.py")),
        str(md_path), "--channel", cid,
    ]).returncode
def build_one(slug: str, *, force: bool, dry_run: bool) -> Path | None:
    titre, consigne = EXERCICES[slug]
    out_md = METHODO_DIR / f"methodo_{slug}.md"
    print(f"\n=== {slug} : {titre} ===")
    print(f"[*] Cible : {out_md}")
    if out_md.exists() and out_md.stat().st_size > 0 and not force and not dry_run:
        print(f"[SKIP] Déjà présent : {out_md} (-force pour régénérer).")
        return out_md
    prompt = PROMPT_SYSTEME.format(titre=titre, consigne=consigne)
    if dry_run:
        print("-" * 70)
        print(prompt[:1200] + ("\n[…tronqué…]" if len(prompt) > 1200 else ""))
        print("-" * 70)
        print("[*] Dry-run : pas d'appel claude.")
        return None
    print("[*] Génération via claude --print (abonnement)…")
    support = generate(prompt)
    out_md.parent.mkdir(parents=True, exist_ok=True)
    out_md.write_text(support, encoding="utf-8")
    print(f"[OK] Support écrit ({len(support)} car.) : {out_md}")
    return out_md
def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("exercice", nargs="?", choices=sorted(EXERCICES),
                    help="Exercice à ficher (omettre avec --all)")
    ap.add_argument("--all", action="store_true", help="Génère tous les supports")
    ap.add_argument("--publish", action="store_true",
                    help="Poste le(s) support(s) sur #methodo-juridique")
    ap.add_argument("--force", action="store_true", help="Régénère même si présent")
    ap.add_argument("--dry-run", action="store_true", help="Montre le prompt, pas d'appel")
    args = ap.parse_args()
    if not args.all and not args.exercice:
        ap.error("donne un exercice (ex: dissertation) ou --all.")
    cibles = sorted(EXERCICES) if args.all else [args.exercice]
    written: list[Path] = []
    for slug in cibles:
        md = build_one(slug, force=args.force, dry_run=args.dry_run)
        if md:
            written.append(md)
    if args.publish and not args.dry_run:
        print()
        for md in written:
            if publish(md) != 0:
                print(f"[WARN] publication échouée : {md.name}", file=sys.stderr)
    return 0
if __name__ == "__main__":
    raise SystemExit(main())