# 01 · Architecture

> Cible. Rien ici n'est codé en S0 (sauf le script Discord). Sert de référence
> aux sessions de build.

## Vue d'ensemble

```
   audio / poly / énoncé
            │
            ▼
   _inbox/  (dépôt)  ──►  _scripts/ (pipeline lean)
                              │
              ┌───────────────┼────────────────┐
              ▼               ▼                ▼
        transcribe.py     fiche.py        publish_discord.py
        (Whisper)       (résumé/fiche)   (dépôt salon)
              │               │                │
              ▼               ▼                ▼
        DROIT/<MAT>/...  (arbo de contenu, source de vérité disque)
              │
              ▼
        CompagnonRevision  (lit l'arbo pour réviser)
        Discord « Cartable »  (distribue / archive)
```

## Arbo de contenu (proposition à figer en S1)

```
Cartable/
└── DROIT/
    └── <MATIERE>/                 # slug court, ex: droit-personnes, constit1
        ├── CM/
        │   ├── audio/             # .m4a/.mp3 (gitignored)
        │   ├── transcriptions/    # CM{n}_<mat>_<date>.txt
        │   └── fiches/            # fiche_CM{n}_<mat>.{md,pdf}
        ├── TD/
        │   └── TD{n}/             # énoncé, transcription, correction perso
        ├── methodo/               # dissertation, commentaire d'arrêt, etc.
        └── arrets/                # fiches d'arrêt / jurisprudence clé
```

Le mapping `<MATIERE>` ↔ salons Discord ↔ catégorie est dans
`_contexte/discord_channels.json` (clé = nom de catégorie « 📕 S1 · … »).

## Conventions de nommage (simples)

```
CM{n}_<mat>_<JJMM>.txt        transcription de CM
TD{n}_<mat>_<JJMM>.txt        transcription de TD
fiche_CM{n}_<mat>.pdf         fiche de révision
```
- Pas d'accents dans les noms de fichiers. Underscore, jamais d'espace.
- Année implicite (2026-2027).

## Briques (un script = une responsabilité)

| Script | Rôle | État |
|---|---|---|
| `setup_discord_cartable.py` | Crée/maj les salons Discord. | ✅ S0 |
| `matieres.py` | Registre unique des matières (slug ↔ libellé ↔ semestre ↔ TD). Source de vérité partagée arbo / routage / Discord. | ✅ S1 |
| `init_content.py` | Crée l'arbo `DROIT/<slug>/...` depuis `matieres.py` (idempotent, `.gitkeep`). | ✅ S1 |
| `transcribe.py` | Audio → transcription (faster-whisper large-v3, GPU/CPU auto). Épuré : 1 process inline, routage par nom de fichier, en-tête. | ✅ S1 |
| `publish_discord.py` | Poste un fichier dans le bon salon (REST multipart, lookup `matieres.py` + `discord_channels.json`). | ✅ S1 |
| `fiche.py` | Transcription/poly → fiche de révision Markdown (via `claude --print` CLI, 0 €). Routage `matieres.py`, sortie `CM/fiches/fiche_<base>.md`, `--publish` → `#resumes`. | ✅ S2 |
| `methodo.py` | Supports de méthodo juridique (dissertation, commentaire/fiche d'arrêt, cas pratique, consultation) via `claude --print`. Sortie transverse `DROIT/_methodo/methodo_<type>.md`, `--publish` → `#methodo-juridique`. | ✅ S3 |

**Convention de nom** (routage auto `transcribe.py`) : `<CM|TD><n>_<slug>_<JJMM>.<ext>`,
ex. `CM3_droit-personnes_1509.m4a`. Le slug peut contenir des tirets ; l'underscore
sépare les trois champs. Nom non canonique → passer `--matiere <slug> --type CM|TD`.

## Principes techniques

- **Token Discord** : lu depuis `AboekaBot/.env`, jamais en dur ni committé.
- **Pas de bot résident** nécessaire pour publier : on poste via l'API REST
  avec le token du bot (comme `setup_discord_cartable.py`). Un watcher/bot
  pourra venir plus tard si le besoin se confirme.
- **Whisper** : réutiliser les params COURS (large-v3, fr, VAD, beam 5).
- **Génération IA** (fiches, méthodo) : `claude --print` CLI (abonnement, 0 €),
  comme COURS le faisait via `summarize.py`. Deux garde-fous dans `generate()`
  (`fiche.py`, `methodo.py`) :
  1. ⚠ **Retirer `ANTHROPIC_API_KEY`** de l'environnement du sous-processus : si la
     clé est présente, la CLI facture l'API (« Credit balance is too low ») au lieu
     d'utiliser l'abonnement OAuth.
  2. ⚠ **Lancer depuis un cwd temporaire VIDE** (`tempfile.TemporaryDirectory`) :
     lancée depuis le repo, la CLI charge le `CLAUDE.md` de Cartable, explore l'arbo
     avec ses outils et se comporte en agent (demande de permission d'écriture,
     méta-commentaires) au lieu de produire le texte. Un cwd neutre = génération pure.