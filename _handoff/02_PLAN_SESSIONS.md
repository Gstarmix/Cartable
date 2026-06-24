# 02 · Plan de sessions

> Multi-session, sans plafond. On s'arrête toujours à une frontière **propre**
> (incrément qui marche). Cocher au fur et à mesure, écrire le handoff `_reprise/`
> tôt (connexion instable).

## Définition du DONE v1

À la rentrée, Gaylord dépose un audio de cours et obtient, sans effort :
transcription + fiche de révision, rangées dans `DROIT/<mat>/` et postées sur le
bon salon Discord, exploitables dans CompagnonRevision.

## Phases

| # | Phase | Contenu | État |
|---|---|---|---|
| **S0** | Fondation | Arbo projet, mémoire de travail, serveur Discord, 1er push GitHub. | ✅ 2026-06-22 |
| **S1** | Transcription | Figer l'arbo de contenu ; porter `transcribe.py` (épuré) ; `publish_discord.py` ; test sur un audio réel. | ⏳ |
| **S2** | Fiches | `fiche.py` : transcription/poly → fiche de révision PDF/MD (via claude CLI). Dépôt salon `resumes`. | ⏳ |
| **S3** | Méthodo | Templates méthodo juridique (dissertation, commentaire/fiche d'arrêt, cas pratique, consultation). Salon `methodo`. | ⏳ |
| **S4** | Intégration CompagnonRevision | Ajouter `CARTABLE_ROOT` + adapter `cours_resolver.py` pour réviser sur l'arbo droit. Cf. 04. | ⏳ |
| **S5** | Confort | Auto-routage `_inbox/`, lanceur, ce qui rend l'usage quotidien fluide. | ⏳ |

## Frontières propres

Chaque phase doit laisser le dépôt dans un état qui tourne. Pas de demi-brique
cassée laissée en plan. Si une coupure survient, `_reprise/` doit déjà refléter
l'état réel.