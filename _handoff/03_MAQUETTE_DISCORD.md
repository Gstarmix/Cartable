# 03 · Maquette Discord

Serveur **Cartable**, guild `1475846763909873727` (ex-« Veille »).
Bot : `aboeka-bot` (token dans `AboekaBot/.env`).
Géré par `_scripts/setup_discord_cartable.py`. IDs réels :
`_contexte/discord_channels.json`.

## Principe

- **Une catégorie par matière** (nom complet, préfixe `📕 S1 ·` / `📗 S2 ·`).
- À l'intérieur, salons **fonctionnels** (mêmes noms d'une matière à l'autre,
  scopés par catégorie).
- Catégorie transverse `🎓 GÉNÉRAL`.

## Salons par matière

**Majeure (CM + TD)** (8 salons) :
`audio-cm` · `audio-td` · `transcript-cm` · `transcript-td` · `resumes` ·
`methodo` · `arrets-annales` · `inbox`

**Mineure / matière CM seul** (4 salons) :
`audio-cm` · `transcript-cm` · `resumes` · `inbox`

**🎓 GÉNÉRAL** : `annonces` · `methodo-juridique` · `cartable-logs`

## Matières créées (défauts maquette L1 général Rennes 2023-2027)

| Sem | Matière | TD ? |
|---|---|---|
| S1 | Droit des personnes | ✅ |
| S1 | Droit constitutionnel 1 | ✅ |
| S1 | Histoire des institutions publiques | ✅ |
| S1 | Introduction au droit & juridictions | CM |
| S1 | Organisations européennes | CM |
| S2 | Droit de la famille | ✅ |
| S2 | Droit constitutionnel 2 | ✅ |
| S2 | Histoire des sources du droit | CM |
| S2 | Institutions administratives | CM |
| S2 | Histoire du droit des personnes et de la famille | CM |
| S2 | Relations internationales | CM |
| S2 | Introduction à la science politique | CM |
| S2 | Anglais | CM |

## À ajuster

- **Mineure S2** : par défaut « science politique » (Relations internationales +
  Intro science politique). Si Gaylord choisit éco-gestion (Macroéconomie +
  Comptabilité) ou environnement, éditer `MATIERES` dans le script puis relancer
  `--create` (idempotent : n'efface rien, ajoute le manquant).
- Pour ajouter/retirer une matière : éditer `MATIERES`, relancer `--create`.
- Pour repartir de zéro : `--wipe --create` (destructif).