# Compte Rendu - SAÉ Graphes-IHM : Projet Neonaure

> BUT Informatique - IUT du Littoral Cote d'Opale - 2025-2026
> Modules R2-07 (IHM) et R2-02 (Graphes)
> Responsable : L. Conoir | Intervenants : R. Cozot, J. Hermilier
> Equipe : Jean-Francois L., Adrien R., Florian S.

---

## Table des matieres

1. [Sujet et regles du jeu](#1-sujet-et-regles-du-jeu)
2. [Analyse detaillee des fonctionnalites requises](#2-analyse-detaillee-des-fonctionnalites-requises)
3. [Etat actuel du projet](#3-etat-actuel-du-projet)
4. [Plan de developpement detaille - Etape par etape](#4-plan-de-developpement-detaille---etape-par-etape)
5. [Architecture technique](#5-architecture-technique)
6. [Axes d'amelioration](#6-axes-damelioration)
7. [Point de vue et recommandations](#7-point-de-vue-et-recommandations)

---

## 1. Sujet et regles du jeu

### 1.1 Description

Le **Neonaure** est une variante du Sudoku. Le jeu se presente sous forme d'une grille carree (generalement 8x8 = 64 cases) ou rectangulaire, divisee en **motifs** (regions delimites par des traits gras).

### 1.2 Les 3 contraintes du jeu

| # | Contrainte | Description |
|---|-----------|-------------|
| 1 | **Une valeur par case** | Chaque case contient exactement un chiffre |
| 2 | **Voisinage** | Un chiffre doit etre entoure de chiffres **differents** (y compris en diagonale, donc 8 voisins max) |
| 3 | **Motif** | Un motif de N cases doit contenir tous les chiffres de 1 a N (sans doublon) |

### 1.3 Consequences logiques des regles

- **Contrainte 1** : Impossible d'avoir une case vide ou avec plusieurs valeurs.
- **Contrainte 2 (voisinage)** : Deux cases adjacentes (horizontale, verticale ou diagonale) ne peuvent PAS avoir la meme valeur. Cela inclut les 8 directions : haut, bas, gauche, droite, et les 4 diagonales.
- **Contrainte 3 (motif)** : Si un motif a 5 cases, il doit contenir exactement les chiffres {1, 2, 3, 4, 5}. Un motif de 1 case contient forcement {1}. Un motif de 8 cases contient {1, 2, 3, 4, 5, 6, 7, 8}.
- **Deduction importante** : La valeur maximale dans la grille est egale a la taille du plus grand motif.

### 1.4 Format des donnees JSON

Chaque grille est stockee au format JSON :

```json
{
  "motif1": [[x, y, valeur], [x, y, valeur], ...],
  "motif2": [[x, y, valeur], ...],
  ...
}
```

- `x` = indice de colonne
- `y` = indice de ligne
- `valeur` = 0 (case vide a remplir) ou un entier positif (indice pre-rempli)

### 1.5 Grilles disponibles

| Fichier | Dimensions | Nb motifs | Nb indices |
|---------|-----------|-----------|------------|
| `default.json` | 5 x 13 | 14 | ~10 |
| `grid1.json` | 8 x 8 | 15 | ~8 |
| `grid2.json` | 8 x 8 | 15 | ~8 |
| `grid3.json` | 8 x 8 | 14 | ~8 |
| `grid4.json` | 8 x 8 | 15 | ~7 |
| `grid5.json` | 8 x 8 | 14 | ~9 |
| `grid6.json` | 8 x 8 | 14 | ~8 |
| `grid7.json` | 5 x 6 | 7 | ~7 |
| `grid8.json` | 6 x 4 | 6 | ~3 |

---

## 2. Analyse detaillee des fonctionnalites requises

Le sujet exige **3 fonctionnalites minimum** :

### 2.1 Fonctionnalite 1 : Charger et sauvegarder une grille

#### Chargement (Load)
- Ouvrir un fichier JSON depuis le dossier `data/grids/`
- Parser le JSON et construire les objets `Grid` et `Pattern`
- Gerer les erreurs :
  - Fichier inexistant ou illisible
  - JSON mal forme
  - Donnees incoherentes (motifs qui se chevauchent, cellules hors limites, valeurs invalides)
- Valider la grille a l'ouverture :
  - Verifier que chaque case appartient a exactement un motif
  - Verifier que les indices pre-remplis respectent les 3 contraintes

#### Sauvegarde (Save)
- Sauvegarder l'etat actuel de la grille en JSON dans `data/saves/`
- Preserver le format original (motifs, positions, valeurs)
- Pouvoir recharger une partie sauvegardee
- Gerer l'ecriture dans un fichier (permissions, espace disque)

#### Ce qu'il faut coder :
1. `Grid.load_from_json(filepath: str) -> Grid` - Constructeur alternatif qui parse un JSON
2. `Grid.save_to_json(filepath: str) -> None` - Serialise la grille en JSON
3. Validation du format JSON (schema checking)
4. Gestion des erreurs et messages utilisateur

---

### 2.2 Fonctionnalite 2 : Jouer en remplissant une grille

#### Interface de jeu
- Afficher la grille avec ses motifs (bordures distinctes)
- Permettre de cliquer sur une case vide pour la selectionner
- Permettre de saisir un chiffre (clavier ou boutons)
- Afficher les indices pre-remplis de maniere differente (non modifiables)
- Indiquer visuellement la case selectionnee

#### Validation en temps reel
- **Contrainte voisinage** : Quand un joueur place un chiffre, verifier qu'aucun des 8 voisins n'a la meme valeur. Si conflit, signaler visuellement (case en rouge, animation, etc.)
- **Contrainte motif** : Verifier que le chiffre place ne duplique pas une valeur deja presente dans le motif. Signaler si conflit.
- **Contrainte valeur** : Verifier que le chiffre est entre 1 et N (taille du motif)

#### Gestion de la partie
- Detecter la **victoire** : toutes les cases remplies ET toutes les contraintes respectees
- Detecter les **erreurs** : signaler sans necessairement empecher (le joueur peut se tromper)
- Historique : pouvoir **annuler** (undo) un coup et le **refaire** (redo)
- Chronometre optionnel

#### Ce qu'il faut coder :
1. Systeme de selection de case (clic souris)
2. Systeme de saisie de valeur (clavier + boutons IHM)
3. Verification des 3 contraintes a chaque placement
4. Affichage visuel des conflits
5. Detection de victoire
6. Systeme undo/redo (pile d'actions)

---

### 2.3 Fonctionnalite 3 : Determiner et proposer la solution d'une grille

#### Resolution automatique
- Implementer un algorithme de **backtracking** (retour sur trace) adapte aux 3 contraintes du Neonaure
- Pour chaque case vide, essayer les valeurs de 1 a N (N = taille du motif) et verifier les contraintes
- Si une valeur mene a une impasse, revenir en arriere (backtrack)
- L'algorithme doit etre capable de resoudre n'importe quelle grille valide

#### Proposition de solution
- Pouvoir afficher la solution complete d'un coup
- OU pouvoir proposer **un seul coup** (aide ponctuelle) : remplir une case pour aider le joueur
- Indiquer si la grille a une solution unique, plusieurs solutions, ou aucune solution

#### Performance
- Le solveur doit etre suffisamment rapide pour des grilles 8x8 (64 cases max)
- Optimisations possibles :
  - Ordonnancement des cases a remplir (MRV - Minimum Remaining Values)
  - Propagation de contraintes (forward checking)
  - Pruning anticipé

#### Ce qu'il faut coder :
1. Classe `Solver` avec methode `solve(grid: Grid) -> Grid | None`
2. Algorithme de backtracking avec verification des 3 contraintes
3. Methode `hint(grid: Grid) -> tuple[int, int, int] | None` pour proposer un coup
4. Methode `count_solutions(grid: Grid) -> int` pour compter les solutions
5. Integration avec l'IHM (bouton "Resoudre", bouton "Indice")

---

## 3. Etat actuel du projet

### 3.1 Resume

| Composant | Fichier | Etat | Avancement |
|-----------|---------|------|-----------|
| Point d'entree | `main.py` | Fonctionnel | 100% |
| Package init | `neonaure/__init__.py` | Partiel (bugs) | 40% |
| Modele | `neonaure/model.py` | Squellette | 15% |
| Vue | `neonaure/view.py` | Vide (docstring) | 0% |
| Controleur | `neonaure/controller.py` | Vide (docstring) | 0% |
| Grilles | `data/grids/*.json` | Complets | 100% |
| Requirements | `requirements.txt` | Vide | 0% |

### 3.2 Bugs identifies

| Bug | Fichier | Description | Gravite |
|-----|---------|-------------|---------|
| Chemin incorrect | `__init__.py` | `"./data/grid/default.json"` au lieu de `"./data/grids/default.json"` (il manque le 's') | Haute |
| Version typo | `__init__.py` | `__version__ = "O.1"` utilise un 'O' majuscule au lieu de '0' | Basse |
| `run()` vide | `__init__.py` | La fonction `run()` ne fait rien (`pass`) | Haute |
| Wildcard imports | `__init__.py` | `from .controller import *` et `from .view import *` | Moyenne |
| `Cell` commentee | `model.py` | La classe Cell est en commentaire au lieu d'etre implementee ou supprimee | Moyenne |

### 3.3 Classes actuelles

```
Pattern
  ├─ __init__(cells: list)
  └─ cells: list

Grid (stub)
  ├─ __init__(height, width, patterns) -> pass
  └─ neighbours(x, y) -> pass

Solver (stub)
  └─ __init__() -> pass
```

---

## 4. Plan de developpement detaille - Etape par etape

> **Principe** : Toujours coder etape par etape, diviser chaque tache en sous-taches, et tester apres chaque etape.

### ETAPE 1 : Fondations du Modele (model.py)

#### 1.1 - Corriger les bugs existants
- [ ] Corriger le chemin `DEFAULT_GRID` dans `__init__.py`
- [ ] Corriger la version `"O.1"` -> `"0.1"`
- [ ] Decider si la classe `Cell` est necessaire et l'implementer ou la supprimer

#### 1.2 - Implementer la classe Cell
- [ ] Attributs : `x: int`, `y: int`, `value: int`, `is_fixed: bool` (indice pre-rempli)
- [ ] Methode `is_empty() -> bool` : retourne True si value == 0
- [ ] Methode `set_value(v: int)` : modifie la valeur si non fixe
- [ ] Representation `__repr__` et `__str__`

#### 1.3 - Completer la classe Pattern
- [ ] Attribut `cells: list[Cell]`
- [ ] Attribut `id: int` ou `name: str` pour identifier le motif
- [ ] Methode `size() -> int` : nombre de cases dans le motif
- [ ] Methode `values() -> list[int]` : liste des valeurs deja presentes
- [ ] Methode `missing_values() -> list[int]` : chiffres de 1 a N manquants
- [ ] Methode `contains_value(v: int) -> bool`
- [ ] Methode `get_cell(x: int, y: int) -> Cell | None`

#### 1.4 - Implementer la classe Grid
- [ ] Constructeur `__init__(height, width, patterns)` : initialiser la grille 2D
- [ ] Attributs : `height`, `width`, `patterns: list[Pattern]`, `cells: list[list[Cell]]` (grille 2D)
- [ ] Methode `get_cell(x, y) -> Cell`
- [ ] Methode `set_cell(x, y, value) -> bool`
- [ ] Methode `neighbours(x, y) -> list[Cell]` : retourner les 8 voisins (ou moins si au bord)
- [ ] Methode `get_pattern_of(x, y) -> Pattern` : trouver le motif contenant cette case
- [ ] Methode `is_valid_placement(x, y, value) -> bool` : verifier les 3 contraintes
- [ ] Methode `is_complete() -> bool` : toutes les cases remplies
- [ ] Methode `is_solved() -> bool` : complete ET toutes contraintes respectees
- [ **Tests unitaires** : tester chaque methode independamment avec des petites grilles

#### 1.5 - Charger/Sauvegarder (JSON)
- [ ] `Grid.from_json(filepath: str) -> Grid` : methode statique de chargement
  - Parser le JSON
  - Determiner les dimensions de la grille (max x + 1, max y + 1)
  - Creer les objets Cell et Pattern
  - Construire la grille 2D
  - Valider la coherence (pas de chevauchement, pas de cellule orpheline)
- [ ] `Grid.to_json(filepath: str) -> None` : methode de sauvegarde
  - Reconvertir les objets en dictionnaire JSON
  - Ecrire dans le fichier avec indentation
- [ ] Tester avec toutes les grilles de `data/grids/`
- [ ] Tester la sauvegarde et le rechargement (round-trip)

---

### ETAPE 2 : Solveur (model.py - classe Solver)

#### 2.1 - Backtracking basique
- [ ] `Solver.solve(grid: Grid) -> Grid | None`
  - Trouver la premiere case vide
  - Essayer les valeurs de 1 a N (N = taille du motif de la case)
  - Pour chaque valeur, verifier `grid.is_valid_placement(x, y, value)`
  - Si valide, placer la valeur et recursivement resoudre le reste
  - Si echec, backtrack (remettre a 0 et essayer la valeur suivante)
  - Retourner la grille resolue ou None si impossible
- [ ] **Tests** : verifier que le solveur resout grid7.json (5x6, petite grille)
- [ ] **Tests** : verifier sur grid8.json (6x4, plus petite)

#### 2.2 - Optimisations du solveur
- [ ] Heuristique MRV (Minimum Remaining Values) : choisir en priorite la case avec le moins de valeurs possibles
- [ ] Forward checking : quand on place une valeur, eliminer les valeurs impossibles pour les voisins et le motif
- [ ] Methode `hint(grid: Grid) -> tuple[int, int, int] | None` : resoudre partiellement pour donner un indice
- [ ] Methode `count_solutions(grid: Grid, max_count: int = 2) -> int` : compter les solutions (utile pour verifier l'unicite)
- [ ] **Tests** : verifier que toutes les grilles de `data/grids/` ont une solution

---

### ETAPE 3 : Interface graphique - Vue (view.py)

#### 3.1 - Fenetre principale
- [ ] Creer la fenetre principale Qt (QMainWindow)
- [ ] Barre de menus : Fichier (Ouvrir, Sauvegarder, Quitter), Aide (Regles, A propos)
- [ ] Zone centrale pour la grille
- [ ] Barre de statut (informations, chronometre)

#### 3.2 - Affichage de la grille
- [ ] Creer un widget personnalisé pour dessiner la grille (QPainter ou QWidget custom)
- [ ] Dessiner les cases avec leurs valeurs
- [ ] Dessiner les bordures de motifs en gras (distinction visuelle entre motifs)
- [ ] Colorer les indices pre-remplis differemment des cases joueur
- [ ] Afficher la case selectionnee (surbrillance)

#### 3.3 - Interaction joueur
- [ ] Clic souris pour selectionner une case
- [ ] Saisie clavier (touches 1-9) pour placer un chiffre
- [ ] Touche Suppr/Backspace pour effacer une case
- [ ] Navigation clavier (fleches) entre les cases
- [ ] Boutons numerotes (1 a N) cliquables

#### 3.4 - Retour visuel
- [ ] Case en surbrillance quand selectionnee
- [ ] Case en rouge quand conflit (voisin ou motif)
- [ ] Animation ou message de victoire
- [ ] Cases du meme motif colorees legerement pour guider le joueur

---

### ETAPE 4 : Controleur (controller.py)

#### 4.1 - Liaison Modele-Vue
- [ ] Classe `Controller` qui possede une reference a `Grid` (modele) et a la Vue
- [ ] Connecter les signaux Qt (clics, touches) aux methodes du controleur
- [ ] Methode `on_cell_selected(x, y)` : mettre a jour la selection
- [ ] Methode `on_value_input(value)` : placer une valeur si valide
- [ ] Mettre a jour la vue apres chaque action

#### 4.2 - Actions de jeu
- [ ] Nouvelle partie (charger une grille)
- [ ] Sauvegarder la partie en cours
- [ ] Charger une partie sauvegardee
- [ ] Annuler (undo) / Refaire (redo)
- [ ] Demander un indice (appel au Solver)
- [ ] Resoudre automatiquement

#### 4.3 - Fonction run()
- [ ] Implementer `run()` dans `__init__.py`
- [ ] Creer l'application Qt (QApplication)
- [ ] Instancier le Modele, la Vue, le Controleur
- [ ] Charger la grille par defaut
- [ ] Lancer la boucle evenementielle Qt

---

### ETAPE 5 : Finalisation et tests

#### 5.1 - Tests globaux
- [ ] Tester le chargement de toutes les grilles
- [ ] Tester le solveur sur toutes les grilles
- [ ] Tester le parcours joueur complet (jouer une partie entiere)
- [ ] Tester la sauvegarde et le chargement d'une partie en cours
- [ ] Tester les cas limites (grille vide, grille deja remplie, grille sans solution)

#### 5.2 - Qualite
- [ ] Completer `requirements.txt` avec les dependances (PyQt6 ou PySide6)
- [ ] Verifier les type hints partout
- [ ] Verifier les docstrings
- [ ] Nettoyer le code (supprimer les TODO, commentaires inutiles)
- [ ] Mettre a jour le README.md avec des captures d'ecran

---

## 5. Architecture technique

### 5.1 Stack technique

| Composant | Technologie | Justification |
|-----------|------------|---------------|
| Langage | Python >= 3.10 | Impose par le contexte academique |
| GUI | PyQt6 ou PySide6 | Modules R2-07 IHM, Qt est le standard |
| Format de donnees | JSON | Impose par le sujet |
| Architecture | MVC (Modele-Vue-Controleur) | Separation claire des responsabilites |

### 5.2 Diagramme MVC

```
┌─────────────┐      signaux      ┌──────────────┐     appels      ┌─────────────┐
│             │ ──────────────────> │              │ ──────────────> │             │
│    VUE      │                    │  CONTROLEUR  │                 │   MODELE    │
│  (view.py)  │ <------------------│(controller.py)│ <-------------- │ (model.py)  │
│             │   mise a jour      │              │   notifications │             │
└─────────────┘                    └──────────────┘                 └─────────────┘
                                         │
                                         v
                                  ┌──────────────┐
                                  │   SOLVEUR    │
                                  │  (Solver)    │
                                  └──────────────┘
```

### 5.3 Structure des fichiers

```
SAE_Graphe/
├── main.py                    # Point d'entree
├── requirements.txt           # Dependances
├── README.md                  # Documentation
├── data/
│   ├── grids/                 # Grilles de jeu (JSON)
│   │   ├── default.json
│   │   ├── grid1.json ... grid8.json
│   └── saves/                 # Sauvegardes (cree a l'execution, ignore par git)
├── neonaure/
│   ├── __init__.py            # Package + fonction run()
│   ├── model.py               # Grid, Pattern, Cell, Solver
│   ├── view.py                # Interface graphique Qt
│   └── controller.py          # Logique de coordination
└── rule/
    ├── sae_sujet.md           # Sujet officiel
    ├── convention.md          # Conventions de code
    └── compte_rendu.md        # Ce fichier
```

### 5.4 Schema des classes du Modele

```
Cell
  ├── x: int
  ├── y: int
  ├── value: int              # 0 = vide, >0 = valeur
  ├── is_fixed: bool          # True si indice pre-rempli
  ├── is_empty() -> bool
  └── set_value(v: int) -> None

Pattern
  ├── id: int
  ├── cells: list[Cell]
  ├── size() -> int
  ├── values() -> list[int]
  ├── missing_values() -> list[int]
  ├── contains_value(v: int) -> bool
  └── get_cell(x, y) -> Cell | None

Grid
  ├── height: int
  ├── width: int
  ├── cells: list[list[Cell]]     # Grille 2D [y][x]
  ├── patterns: list[Pattern]
  ├── from_json(filepath) -> Grid  # Chargement
  ├── to_json(filepath) -> None    # Sauvegarde
  ├── get_cell(x, y) -> Cell
  ├── set_cell(x, y, value) -> bool
  ├── neighbours(x, y) -> list[Cell]
  ├── get_pattern_of(x, y) -> Pattern
  ├── is_valid_placement(x, y, value) -> bool
  ├── is_complete() -> bool
  └── is_solved() -> bool

Solver
  ├── solve(grid: Grid) -> Grid | None
  ├── hint(grid: Grid) -> tuple[int, int, int] | None
  └── count_solutions(grid: Grid, max_count: int) -> int
```

---

## 6. Axes d'amelioration

> Ces ameliorations vont au-dela du minimum requis mais restent dans le cadre du sujet et enrichissent le projet.

### 6.1 Ameliorations de jouabilite

| Amelioration | Description | Priorite |
|-------------|-------------|----------|
| **Notes/Pencil marks** | Permettre au joueur de noter des candidats dans une case (comme au Sudoku) | Haute |
| **Surbrillance intelligente** | Quand un chiffre est selectionne, surligner toutes les cases avec la meme valeur dans la grille | Haute |
| **Indicateur de progression** | Barre de progression ou compteur (X/64 cases remplies) | Moyenne |
| **Chronometre** | Afficher le temps ecoule depuis le debut de la partie | Moyenne |
| **Niveaux de difficulte** | Classer les grilles en facile/moyen/difficile selon le nombre d'indices | Moyenne |
| **Tutoriel interactif** | Guide pas-a-pas pour les nouveaux joueurs | Basse |

### 6.2 Ameliorations visuelles

| Amelioration | Description | Priorite |
|-------------|-------------|----------|
| **Themes de couleurs** | Mode clair/sombre, palettes de couleurs | Moyenne |
| **Animations** | Animation de placement de chiffre, celebration de victoire | Basse |
| **Coloration des motifs** | Couleurs pastel differentes pour chaque motif | Haute |
| **Responsive** | Adaptation de la taille de la grille a la fenetre | Moyenne |

### 6.3 Ameliorations techniques

| Amelioration | Description | Priorite |
|-------------|-------------|----------|
| **Generateur de grilles** | Algorithme capable de generer de nouvelles grilles valides aleatoirement | Haute |
| **Validation de grille** | Detecter les grilles mal formes ou sans solution avant de les proposer | Haute |
| **Export PDF/PNG** | Exporter la grille en image ou PDF | Basse |
| **Internationalisation** | Support multilingue (FR/EN) | Basse |
| **Statistiques** | Nombre de parties jouees, meilleur temps, etc. | Basse |

### 6.4 Ameliorations du solveur

| Amelioration | Description | Priorite |
|-------------|-------------|----------|
| **Resolution pas-a-pas** | Montrer le processus de resolution etape par etape (animé) | Moyenne |
| **Techniques avancees** | Implementer des techniques de resolution logique (naked singles, hidden singles) en plus du backtracking | Moyenne |
| **Generation avec unicite** | Generer des grilles avec une solution unique garantie | Moyenne |

---

## 7. Point de vue et recommandations

### 7.1 Analyse du projet

Le Neonaure est un excellent projet pedagogique qui combine deux competences fondamentales en informatique :

1. **Algorithmique et theorie des graphes (R2-02)** : Le solveur est un probleme de satisfaction de contraintes (CSP) classique. Les contraintes de voisinage et de motif se pretent parfaitement a l'apprentissage du backtracking, de la propagation de contraintes et des heuristiques de recherche. Le voisinage (8 directions) est un concept directement lie a la theorie des graphes (graphe de proximite).

2. **Interface Homme-Machine (R2-07)** : L'implementation en Qt avec une architecture MVC force a penser la separation des responsabilites, la gestion des evenements, et le design d'interface utilisateur.

### 7.2 Recommandations strategiques

**Prioriser le modele avant la vue.** C'est tentant de commencer par l'interface graphique parce que c'est ce qu'on voit, mais un modele solide est la fondation. Si `Grid`, `Pattern`, `Cell` et les methodes de validation fonctionnent parfaitement, l'IHM sera beaucoup plus simple a implementer.

**L'ordre ideal de developpement** :
1. Modele complet (Cell, Pattern, Grid, validation) avec tests unitaires
2. Solveur avec tests sur toutes les grilles
3. IHM basique (affichage + saisie)
4. Controleur (liaison modele-vue)
5. Polish (animations, undo/redo, sauvegarde)

**Le solveur est la piece maitresse du cote algorithmique.** Il prouve que les regles sont bien comprises et implementees. Si le solveur ne peut pas resoudre une grille, c'est probablement que la validation (`is_valid_placement`) a un bug. C'est pourquoi il faut coder le modele et le solveur AVANT l'IHM.

### 7.3 Points d'attention

- **Le format JSON est un dict de motifs, pas une grille 2D** : Il faut reconstruire la grille 2D a partir des motifs. Penser a gerer les cas ou des cellules sont manquantes ou en double.
- **La contrainte de voisinage inclut les diagonales** : C'est la difference majeure avec le Sudoku classique. Ne pas l'oublier dans `neighbours()`.
- **Les motifs de taille 1** : grid6.json a un motif d'une seule case (motif4 = `[[7,0,0]]`). Cela signifie que cette case doit contenir 1. C'est un bon test pour verifier que le solveur gere les cas limites.
- **Grille rectangulaire (default.json)** : La grille par defaut est 5x13, pas carree. Le code ne doit pas supposer que la grille est carree.

### 7.4 Note sur la complexite

- **8x8 avec motifs de 5 cases en moyenne** : Le backtracking pur devrait resoudre ces grilles en moins d'une seconde. Pas besoin d'optimisations avancees pour les tailles exigees.
- Si on implemente un generateur de grilles, la complexite explose. C'est un axe d'amelioration, pas une obligation du sujet.

---

*Derniere mise a jour : 10/06/2026*

---

## 8. Journal de developpement

### 10/06/2026 - Session 1 : Fondations du Modele + Solveur

#### Bugs corriges
- `__init__.py` : `"O.1"` → `"0.1"` (lettre O majuscule au lieu du chiffre 0)
- `__init__.py` : `"./data/grid/default.json"` → `"./data/grids/default.json"` (s manquant dans le chemin)

#### Model (`neonaure/model.py`) - refonte complete

**Classe Cell** (nouvelle) :
- `__slots__` pour optimiser la memoire
- `is_empty()` : verifie si la valeur est 0
- `__hash__` : hashable par position (x, y) pour usage dans des sets
- `__eq__` : comparaison par valeur (ignore les cellules vides)
- `set_value()` : leve `CellIsImmuable` si la case est un indice fixe

**Classe Pattern** (methodes ajoutees) :
- `size()` → nombre de cases
- `values()` → liste des valeurs deja placees (ignore les vides)
- `missing_values()` → chiffres manquants de 1 a N
- `contains_value(v)` → verifie si une valeur est deja dans le motif
- `get_cell(x, y)` → recupere une cellule par coordonnees, ou None

**Classe Grid** (methodes ajoutees) :
- `get_cell(x, y)` → acces O(1) via la matrice 2D
- `get_pattern_of(x, y)` → trouve le motif contenant une cellule
- `is_valid_placement(x, y, value)` → verification des 3 contraintes Neonaure :
  - Contrainte motif : pas de doublon dans le meme motif (exclut la cellule elle-meme)
  - Contrainte voisinage : pas de meme valeur parmi les 8 voisins (exclut la cellule elle-meme)
  - Contrainte plage : valeur entre 1 et la taille du motif
- `is_complete()` → toutes les cases remplies
- `is_solved()` → complete + toutes contraintes respectees
- `set_cell_value(x, y, value)` → modifie une cellule si non fixe
- `_compute_dimensions()` → remplace `get_dimensions()`, utilise `max()` (corrige le bug)

**Classe Solver** (implementee) :
- Algorithme de **backtracking** avec heuristique **MRV** (Minimum Remaining Values)
- `_possible_values(cell)` → calcule les valeurs candidates en excluant voisins et motif
- `_select_mrv(empties)` → choisit la cellule la plus contrainte en premier
- `solve()` → resolution complete, retourne True/False
- `hint()` → propose un seul coup valide (utilise `deepcopy` pour preserver l'etat)
- `count_solutions(max_count=2)` → compte les solutions (arrete a max_count)

#### Tests unitaires (`tests/test_model.py`) - 44 tests

| Categorie | Nb tests | Couverture |
|-----------|----------|------------|
| Cell | 6 | creation, immuabilite, egalite, serialisation |
| Pattern | 10 | size, values, missing, contains, get_cell, from_raw_cells, set_cell |
| Grid | 13 | dimensions, acces, voisins, validation, completion, resolution, JSON roundtrip |
| Chargement grilles | 2 | toutes les grilles se chargent + roundtrip JSON |
| Solver | 6 | petite grille, impossible, grid7, grid8, toutes grilles, hint |

**Resultat : 44/44 tests passent en ~1 seconde.**

#### Grilles : resultat du solveur

| Grille | Dimensions | Resolue ? | Temps |
|--------|-----------|-----------|-------|
| default.json | 8x8 | Oui | 0.132s |
| grid1.json | 8x8 | Oui | 0.049s |
| grid2.json | 8x8 | Oui | 0.016s |
| grid3.json | 8x8 | Oui | 0.045s |
| grid4.json | 8x8 | Oui | 0.287s |
| grid5.json | 8x8 | Oui | 0.027s |
| grid6.json | 8x8 | **Non** | 0.278s |
| grid7.json | 5x6 | Oui | 0.003s |
| grid8.json | 6x4 | Oui | 0.002s |

> **grid6.json n'a pas de solution** avec les indices actuels. Probablement une grille mal formee ou des indices contradictoires. A verifier avec le sujet.

#### .gitignore
- Ajout du dossier `tests` dans le `.gitignore`

#### Etat du projet apres cette session

| Composant | Fichier | Avancement |
|-----------|---------|-----------|
| Modele | `neonaure/model.py` | **90%** (Cell, Pattern, Grid, Solver complets) |
| Tests | `tests/test_model.py` | **100%** (44 tests verts) |
| Package init | `neonaure/__init__.py` | 60% (bugs corriges, `run()` encore vide) |
| Vue | `neonaure/view.py` | 0% |
| Controleur | `neonaure/controller.py` | 0% |

### 10/06/2026 - Session 2 : Vue responsive

#### Vue (`neonaure/view.py`) - Rendu responsive

**Classe GridView** (rendue responsive) :
- `_compute_cell_size()` : calcule dynamiquement la taille des cellules en fonction de la taille du widget (`min(w/cols, h/rows)` pour garder des cases carrées)
- `_compute_offset()` : centre la grille dans le widget (offset horizontal et vertical dynamiques)
- `resizeEvent()` : recalcule `cell_size` et offset à chaque redimensionnement de la fenêtre
- `set_data()` : utilise le calcul dynamique au lieu d'un `setMinimumSize` figé
- `paintEvent()` : police proportionnelle (`cell_size * 0.35`), épaisseur des bordures proportionnelle (`cell_size * 0.08`)
- `mouseMoveEvent()` / `mousePressEvent()` : utilisent `_offset_x` et `_offset_y` au lieu du hardcoded `10`

**Classe NumberSelector** (rendue proportionnelle) :
- Taille des boutons : `max(25, cell_size * 0.7)`
- Taille de police : `max(8, cell_size * 0.3)`

**Classes MainWindow / TestWindow** :
- Taille initiale de fenêtre : `800x800`

#### Fichiers modifiés
- `neonaure/view.py`

#### Etat du projet apres cette session

| Composant | Fichier | Avancement |
|-----------|---------|-----------|
| Modele | `neonaure/model.py` | **90%** |
| Tests | `tests/test_model.py` | **100%** (44 tests verts) |
| Vue | `neonaure/view.py` | **60%** (grille responsive, popup, hover ; manque menu, barre de statut) |
| Controleur | `neonaure/controller.py` | 0% |

### 10/06/2026 - Session 3 : Detection des doublons dans un motif

#### Fonctionnalite ajoutee
- **Conflit de doublon dans un motif** : si deux cases du meme motif contiennent la meme valeur, elles sont affichees en rouge (en plus du conflit voisinage existant)

#### Modifications
- `neonaure/view.py` :
  - `GridView` : ajout de `pattern_membership: dict`, passe via `set_data()` pour connaitre l'appartenance de chaque cellule a un motif
  - `_compute_conflicts()` : ajout d'une boucle qui detecte les doublons de valeur au sein d'un meme motif et les ajoute au set de conflits
  - `TestWindow` : passage de `pattern_membership` aux appels `set_data()`
- `neonaure/controller.py` :
  - `update_view()` : passage de `pattern_membership` et `immutable_cells` a `set_data()`

#### Etat du projet apres cette session

| Composant | Fichier | Avancement |
|-----------|---------|-----------|
| Modele | `neonaure/model.py` | **90%** |
| Tests | `tests/test_model.py` | **100%** (44 tests verts) |
| Vue | `neonaure/view.py` | **65%** (grille responsive, popup, hover, conflits motif+voisinage) |
| Controleur | `neonaure/controller.py` | **10%** (liaison modele-vue, gestion clic) |

### 10/06/2026 - Session 4 : Application du stash + Type hints complets + Bugfixes modele

#### Actions realisees
- **Application du stash** `stash@{0}` (pattern_membership) sur controller.py et view.py
- **Resolution du conflit** dans controller.py (la methode `handle_click` avait perdu sa signature lors du merge)
- **Ajout de type hints complets** sur tous les fichiers du package `neonaure/`

#### Fichiers modifies
- `neonaure/__init__.py` : correction bugs (`"O.1"` -> `"0.1"`, chemin `"grid"` -> `"grids"`), remplacement wildcard imports par imports explicites, type hints
- `neonaure/model.py` : `from __future__ import annotations`, `__slots__` sur Cell, `__repr__` sur Cell et Pattern, `__eq__` Cell corrigé (retourne `NotImplemented` au lieu de `False` pour non-Cell, les deux zéros ne sont pas égaux), ajout `InvalidGrid`, `Cell.is_empty()`, `Pattern.size()`, `Pattern.values()`, `Pattern.missing_values()`, `Pattern.contains_value()`, `Pattern.get_cell()`, `Grid.get_cell()`, `Grid.get_pattern_of()`, `Grid.is_valid_placement()`, `Grid.is_complete()`, `Grid.is_solved()`, `Grid.set_cell_value()`, `Solver.solve()`, `Solver.hint()`, `Solver.count_solutions()`, fix `get_dimensions()` (`>` -> `>=`), fix `solve_grid()` (validation initiale des conflits), type hints complets partout
- `neonaure/view.py` : `from __future__ import annotations`, imports `QResizeEvent`, `QMouseEvent`, `QPaintEvent`, `QEvent`, `TYPE_CHECKING`, type hints complets sur toutes les classes et methodes (NumberSelector, GridView, MainWindow, TestWindow, prepare_test_data)
- `neonaure/controller.py` : `from __future__ import annotations`, remplacement `from typing import Dict, Tuple, List, Set, Optional` par syntaxe moderne (`dict`, `tuple`, `list`, `set`, `X | None`), import `Pattern` et `Cell` pour le typage, type hints complets, correction indentation `handle_click`

#### Resultats de tests
- **44/44 tests passent** en 0.37s

#### Etat du projet apres cette session

| Composant | Fichier | Avancement |
|-----------|---------|-----------|
| Modele | `neonaure/model.py` | **95%** (Cell, Pattern, Grid, Solver complets + type hints) |
| Tests | `tests/test_model.py` | **100%** (44 tests verts) |
| Vue | `neonaure/view.py` | **65%** (grille responsive, popup, hover, conflits motif+voisinage + type hints) |
| Controleur | `neonaure/controller.py` | **10%** (liaison modele-vue, gestion clic + type hints) |
 | Package init | `neonaure/__init__.py` | **70%** (bugs corriges, imports explicites, type hints, `run()` vide) |

### 10/06/2026 - Session 5 : Bouton reset (poubelle)

#### Fonctionnalite ajoutee
- **Bouton poubelle** a droite de la grille : icone dessinee programmatiquement (QPainter), effet hover/pressed, click reset toutes les cellules non immuables a 0

#### Modifications
- `neonaure/view.py` :
  - Nouvelle fonction `_create_trash_icon(size)` : genere une icone poubelle rouge via QPainter (couvercle, poignee, corps, lignes verticales)
  - `MainWindow` : remplacement de `setCentralWidget(grid_view)` par un `QHBoxLayout` (grid_view + bouton reset)
  - `TestWindow` : meme layout avec bouton reset + methode `reset_grid()` locale
  - Nouveaux imports : `QHBoxLayout`, `QVBoxLayout`, `QSizePolicy`, `QPixmap`, `QIcon`, `QSize`
- `neonaure/controller.py` :
  - Nouvelle methode `Controller.reset_grid()` : remet a 0 toutes les cellules non immuables et rafraichit la vue

#### Etat du projet apres cette session

| Composant | Fichier | Avancement |
|-----------|---------|-----------|
| Modele | `neonaure/model.py` | **95%** |
| Tests | `tests/test_model.py` | **100%** (44 tests verts) |
| Vue | `neonaure/view.py` | **70%** (grille responsive, popup, hover, conflits, bouton reset) |
| Controleur | `neonaure/controller.py` | **15%** (liaison modele-vue, gestion clic, reset grille) |
| Package init | `neonaure/__init__.py` | **70%** |

### 10/06/2026 - Session 6 : Bouton undo

#### Fonctionnalite ajoutee
- **Bouton undo** au-dessus du bouton poubelle : icone fleche courbe dessinee via QPainterPath, click annule le dernier coup joue

#### Modifications
- `neonaure/view.py` :
  - Nouvelle fonction `_create_undo_icon()` : fleche courbe bleue (arc 270 degres + pointe de fleche)
  - `MainWindow` : panneau vertical (`QVBoxLayout`) avec undo en haut, trash en bas, stretch en dessous
  - `TestWindow` : meme layout + attribut `history` pour tracker les coups, methode `undo()` locale
- `neonaure/controller.py` :
  - Attribut `_history: list[tuple[int, int, int]]` : pile des coups joues (x, y, ancienne_valeur)
  - `handle_click()` : enregistre l'ancienne valeur dans `_history` avant modification
  - `undo()` : depile la derniere action et restaure l'ancienne valeur
  - `reset_grid()` : vide aussi `_history`

#### Etat du projet apres cette session

| Composant | Fichier | Avancement |
|-----------|---------|-----------|
| Modele | `neonaure/model.py` | **95%** |
| Tests | `tests/test_model.py` | **100%** (44 tests verts) |
| Vue | `neonaure/view.py` | **75%** (grille responsive, popup, hover, conflits, boutons undo+reset) |
| Controleur | `neonaure/controller.py` | **20%** (liaison modele-vue, clic, undo, reset) |
| Package init | `neonaure/__init__.py` | **70%** |

### 11/06/2026 - Session 7 : Generateur de grilles + bouton nouvelle carte

#### Fonctionnalites ajoutees
- **Generateur de grilles aleatoires** (`generate_grid.py`) : cree des grilles valides de taille configurable en decoupant la grille en regions connexes (random walk), en resolvant avec le Solver, puis en masquant des valeurs
- **Bouton carte** (icone `map.png`) dans la barre laterale : ouvre un dialogue pour choisir la taille X/Y de la nouvelle grille, puis la genere et l'affiche
- **Dialogue `GridSizeDialog`** : popup avec 2 QSpinBox (largeur/hauteur, de 3 a 12) et un bouton "Generer"

#### Fichiers modifies
- `generate_grid.py` (nouveau) : generateur de grilles avec `generate_regions()`, `solve_and_strip()`, `generate_grid()`, CLI via `argparse`
- `neonaure/view.py` : ajout de `QSpinBox` et `QFormLayout` aux imports, nouvelle classe `GridSizeDialog`, bouton `map_button` dans `MainWindow`, methode `_on_map_clicked()`
- `neonaure/controller.py` : nouvelle methode `generate_new_grid(width, height)` qui appelle `generate_grid()` et met a jour le modele + la vue

#### Etat du projet apres cette session

| Composant | Fichier | Avancement |
|-----------|---------|-----------|
| Modele | `neonaure/model.py` | **95%** |
| Tests | `tests/test_model.py` | **100%** (44 tests verts) |
| Vue | `neonaure/view.py` | **80%** (grille responsive, popup, hover, conflits, boutons undo+reset+map, dialogue taille) |
| Controleur | `neonaure/controller.py` | **25%** (liaison modele-vue, clic, undo, reset, generation grille) |
| Package init | `neonaure/__init__.py` | **70%** |
| Generateur | `generate_grid.py` | **100%** (nouveau) |
