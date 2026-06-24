# 00 · Vision

## Le produit

**Cartable** transforme la matière brute d'un cours universitaire en contenu
**révisable**, et distribue ce contenu là où Gaylord en a besoin.

Entrée : un audio de CM/TD, un poly, un énoncé de TD.
Sortie : une transcription propre, une fiche de révision, un support de méthodo,
postés sur le serveur Discord **Cartable** et exploitables par
`CompagnonRevision` pour réviser à voix haute.

## Pour qui, pour quoi

Gaylord, **L1 parcours général Droit (Université de Rennes, rentrée 2026)**.
Le droit se révise par la **maîtrise du cours** (définitions, plan, dates,
jurisprudence) et par la **méthodo** (dissertation, commentaire et fiche d'arrêt,
cas pratique, consultation, commentaire de texte). Pas de code à corriger,
contrairement à L1 Info.

## La leçon de COURS (le projet précédent)

`COURS` (L1 Info ISTIC) a marché mais s'est **sur-complexifié** : ~20 scripts,
8 workflows, doc empilée phase après phase, versionnement parallèle
inférence/transcription, blocs PDF natifs ReportLab, etc. Beaucoup de machinerie
pour des besoins qui, en droit, sont plus simples.

**Cartable repart minimal.** Règle : chaque brique doit se justifier par un usage
réel et tenir dans le moins de fichiers possible. On réutilise ce qui a fait ses
preuves dans COURS (transcription Whisper, dépôt Discord), on jette le reste.

## North star

Qu'à la rentrée, déposer un audio de cours suffise pour obtenir, sans effort :
1. la transcription, 2. une fiche de révision, 3. le tout rangé et sur Discord,
4. prêt à être travaillé dans CompagnonRevision.

## Ce qui n'est PAS l'objectif

- Pas un produit multi-utilisateur, pas d'installeur, pas de doc grand public.
  Outil perso (comme CompagnonRevision).
- Pas de portage web pour l'instant (éventuellement plus tard, hors scope).
- Pas de reproduction de la machinerie lourde de COURS.