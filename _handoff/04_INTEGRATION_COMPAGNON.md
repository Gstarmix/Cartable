# 04 · Intégration avec CompagnonRevision

> Objectif : que Gaylord puisse **réviser le droit** dans la GUI
> `CompagnonRevision` (modes colle / guidé / découverte), sur le contenu produit
> par Cartable. Phase S4. Ce doc cadre le travail, ne le code pas.

## État actuel de CompagnonRevision (constat S0)

- `C:\dev\CompagnonRevision`, projet Tkinter + Flask, modes de révision pilotés
  par des prompts système (`_prompts/`).
- **`config.py` pointe en dur** sur `COURS_ROOT = C:\Users\Gstar\OneDrive\Documents\COURS`.
- `_scripts/dialogue/cours_resolver.py` navigue cette arbo (find/list énoncés,
  corrections, transcriptions) pour bâtir le contexte d'une séance.
- Donc en l'état, le Compagnon ne sait réviser **que** l'arbo COURS (L1 Info).

## Ce qu'il faudra faire (S4)

### ✅ Fait en S3 (fondation additive, NON câblée, NON commitée côté Compagnon)

Côté `C:\dev\CompagnonRevision` (changements **additifs**, vérifiés sans régression ;
suite complète : 346 passed inchangé ; les 222 « failed » préexistent et sont dus à
l'absence du repo sibling `Arsenal_Arguments` sur la machine, sans rapport) :

1. ✅ **`config.py`** : ajout de `CARTABLE_ROOT = PROJECT_ROOT.parent / "Cartable" / "DROIT"`
   (additif, coexiste avec `COURS_ROOT`, ne le remplace pas). Résolu et vérifié.
2. ✅ **`_scripts/dialogue/droit_resolver.py`** : NOUVEAU module autonome (pendant
   simple de `cours_resolver.py`) pour l'arbo DROIT markdown. API :
   `list_matieres`, `list_types_for_matiere` (CM / CM+TD), `list_nums_for_type`,
   `find_transcription`, `find_fiche`, `list_arrets`, `list_methodo_matiere`,
   `list_methodo_transverse`. **Rien ne l'importe encore** → impact zéro sur
   l'existant. Choix : resolver SÉPARÉ plutôt que contorsionner `cours_resolver.py`
   (1250 l., PDF/code/TD-TP-CC-centré) : l'arbo droit est trop différente (markdown,
   pas de corrigé officiel, pas d'exo/millésime).
3. ✅ **`tests/test_droit_resolver.py`** : 15 tests (arbo temporaire), tous verts.

> ⚠ Ces 3 changements sont **dans l'arbre de travail de CompagnonRevision, non
> commités**. À relire + commiter par Gaylord en session supervisée (règles strictes
> de ce repo : prompts sacrés, pivots d'archi = arbitrage Gstar, mode économe).

### ✅ Fait en S4 (câblage complet, supervisé, poussé)

Câblage DROIT complet dans CompagnonRevision (commits `0b254c7..438227c` poussés sur
`Gstarmix/CompagnonRevision`), additif, **zéro régression COURS**, **577 passed / 0
failed**, prompts sacrés **non modifiés** :

4. ✅ **Sélecteur de source** côté web (`index.html` + `app.js` : sélecteur 📚 COURS /
   ⚖️ Droit + 3 combos droit, cascade `/api/droit_options`) ET GUI Tk (`gui.py` :
   checkbox ⚖️ Droit + droit_frame, cascade `<<ComboboxSelected>>`, mutex avec
   sujet-libre/workspace). Pas d'exo/millésime.
5. ✅ **Modèle de session** dans `prompt_builder.build_initial_context_message` : branche
   DROIT (early-return) = TRANSCRIPTION + FICHE (la fiche remplace le corrigé), refs
   méthodo/arrêts en pointeurs ; `app.py._build_session_context` short-circuit droit
   via `droit_resolver`. `SessionContext` : champs additifs `droit_source` + chemins.
6. ✅ **session_id / nommage** via `app.py._build_session_id` :
   `YYYY-MM-DD_DROIT_<slug>_<CM|TD><num>_full_{mode}_{format}_{anchor}`. Trace JSON
   additive `source="droit"` + `droit_matiere` (pas de bump schéma). resume_session
   restaure la source droit. cours_root (builder + ClaudeClient) scopé sur la matière.
7. ✅ **Prompts système** : NON édités. La branche droit émet ses propres marqueurs
   ([SOURCE : droit] / [ANCRAGE : fiche…]) et instructions mode-aware dans le message
   de contexte, sans toucher au contenu sacré. Modes colle/guidé/découverte gérés.

### ⏳ Reste (pour Gaylord, hors code)

- **Click-test** web + GUI Tk (non vérifiable en headless). Suppose un VRAI contenu
  fiché sous `Cartable/DROIT/<slug>/...` (transcription + fiche), sinon combos vides.
- **Zone grise pédagogique** (arbitrage Gstar) : ancrage droit = la fiche (pas de
  corrigé officiel). Marqueur + instructions posés sans toucher les prompts ; à
  valider/affiner pédagogiquement.

## Principes

- **Ne pas casser** la révision COURS existante (Gaylord peut vouloir y revenir).
  L'ajout du droit est additif (deux racines coexistent).
- Cartable **produit** une arbo propre ; CompagnonRevision la **consomme** en
  lecture seule. Pas de couplage fort : le contrat, c'est l'arborescence + les
  conventions de nommage (cf. `01_ARCHITECTURE.md`).
- Décider en S4 si on duplique `cours_resolver` ou si on le généralise avec une
  racine paramétrable. Préférence : généraliser (une seule logique de résolution).