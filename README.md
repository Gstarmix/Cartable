# Cartable

> Un cartable numérique : transformer ses cours en révisions.

Cartable prend la matière brute d'un cours (l'enregistrement audio d'un cours
magistral ou d'un TD, un polycopié, un énoncé) et la transforme en contenu que
l'on peut réellement réviser : transcriptions propres, fiches de révision
synthétiques, et supports de méthodologie. Tout est ensuite rangé, publié sur un
serveur Discord dédié, et mis à disposition d'un compagnon de révision à voix
haute, [`CompagnonRevision`](../CompagnonRevision).

L'idée tient en une phrase : on parle à son micro pendant le cours, et on
ressort avec de quoi réviser le soir même.

> Glossaire express : un **CM** (cours magistral) est le cours en amphi, un
> **TD** (travaux dirigés) la séance d'exercices en petit groupe.

## Ce que Cartable sait faire

- **Transcrire** un enregistrement de cours en texte fidèle, en local et
  gratuitement (modèle Whisper large-v3, sur GPU si disponible).
- **Ficher** : transformer une transcription (ou un poly) en fiche de révision
  Markdown structurée (plan, notions clés, définitions, jurisprudence citée,
  questions d'auto-évaluation).
- **Outiller la méthode** : générer les supports de méthodologie juridique
  (dissertation, commentaire d'arrêt, fiche d'arrêt, cas pratique, consultation).
- **Distribuer** : publier automatiquement transcriptions, fiches et méthodo
  dans les bons salons d'un serveur Discord rangé par matière.
- **Réviser** : alimenter `CompagnonRevision`, qui interroge l'étudiant à l'oral
  sur ce contenu (modes colle, guidé, découverte).

## Prise en main (sans toucher au terminal)

À la racine du dépôt se trouve **`Cartable.vbs`** : c'est le lanceur. Un simple
double-clic dessus ouvre l'interface graphique, sans console ni ligne de
commande (le script appelle `pythonw` pour démarrer `_scripts/cartable_gui.py`,
une fenêtre Tkinter sans dépendance supplémentaire). Sous Windows, c'est le seul
fichier à connaître pour utiliser Cartable au quotidien.

Dans la fenêtre, on choisit la matière, le type (CM ou TD), le numéro et la date
de la séance, on sélectionne un fichier audio, puis on coche les étapes voulues,
qui sont toutes indépendantes :

1. Transcrire l'audio
2. Générer la fiche de révision
3. Publier la transcription sur Discord
4. Publier la fiche sur Discord

(plus deux options pratiques : régénérer une fiche existante, et un mode
simulation qui n'écrit ni ne publie rien.)

On peut donc lancer la chaîne complète d'un coup, ou n'exécuter qu'un seul
maillon. La fenêtre nomme les fichiers de façon canonique
(`<TYPE><n>_<matiere>_<JJMM>`) pour que `CompagnonRevision` retrouve ensuite le
contenu sans effort.

> Prérequis : Python 3 installé (avec Tkinter, inclus par défaut sous Windows).

## En ligne de commande

```
python _scripts/transcribe.py <audio.m4a>                 # audio vers transcription
python _scripts/fiche.py <transcription.txt> --publish     # fiche de revision (#resumes)
python _scripts/methodo.py --all --publish                 # supports de methodo (#methodo-juridique)
python _scripts/init_content.py [--semestre S1|S2]         # (re)cree l'arborescence DROIT/
```

Note technique : `fiche.py` et `methodo.py` appellent `claude --print` depuis un
dossier temporaire vide et sans `ANTHROPIC_API_KEY`. Sans cette précaution, la
CLI chargerait le contexte du projet (et se comporterait en agent) ou facturerait
l'API au lieu d'utiliser l'abonnement (coût nul).

## Organisation du dépôt

```
_scripts/    le pipeline (Python)
DROIT/       l'arborescence du contenu, rangée par matiere
_handoff/    le plan directeur (vision, architecture, maquettes)
docs/        specifications ponctuelles
Cartable.vbs lanceur de l'interface graphique
```

## Discord

Le serveur « Cartable » est monté et synchronisé par
`_scripts/setup_discord_cartable.py`. Le jeton du bot est lu depuis un fichier
d'environnement local et n'est jamais versionné.

```
python _scripts/setup_discord_cartable.py --list       # etat courant
python _scripts/setup_discord_cartable.py --create      # ajoute ce qui manque (idempotent)
```

## Statut

Projet personnel, développé par itérations. Ce n'est pas un produit : pas
d'installeur, pas de support, mais le code est lisible et réutilisable.