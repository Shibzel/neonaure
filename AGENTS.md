# AGENTS.md

## Regles du projet

### Compte rendu

Apres chaque session de travail (chaque echange significatif avec des modifications de code), mettre a jour le fichier `compte_rendu/compte_rendu.md` dans la section "8. Journal de developpement" avec :

- Ce qui a ete fait (bugs corriges, fonctionnalites ajoutees, etc.)
- Les fichiers modifies
- Les resultats de tests
- L'etat du projet apres la session

### Code

- ecrire du code de "niveau BUT1" : simple, lisible et comprehensible par un etudiant de 1ere annee. Pas de `__slots__`, pas de comprehensions de liste complexes, pas d'exceptions custom inutiles. Favoriser les boucles `for` classiques et les `if/else` explicites. Pas de one-liners cryptiques. Le code doit pouvoir etre lu et compris facilement sans connaissance avancee de Python.
- Commenter le code de facon naturelle, pas comme un LLM (pas de commentaires obvious type "initialize variable")
- Ecrire des tests unitaires a chaque etape avec pytest
- **Apres chaque modification de code**, relancer les tests avec `python -m pytest tests/test_model.py -v` et verifier que tout passe. Si on ajoute une fonctionnalite, ajouter les tests correspondants. Si on supprime du code, supprimer aussi les tests qui testent ce code.

### Structure

- Modele : `neonaure/model.py`
- Vue : `neonaure/view.py`
- Controleur : `neonaure/controller.py`
- Startup : `neonaure/startup.py`
- Package : `neonaure/__init__.py`
- Tests : `tests/test_model.py`
- Grilles : `data/grids/*.json`
- Compte rendu : `compte_rendu/compte_rendu.md`

### Architecture MVC

Le projet suit le pattern Modele-Vue-Controleur :

#### Modele (`neonaure/model.py`)
- `Cell` : une case de la grille (position x/y, valeur, immuable ou non)
- `Pattern` : un motif/region contenant plusieurs cellules
- `Grid` : la grille complete, avec les patterns, la matrice 2D et la methode `is_complete()` pour verifier la victoire
- `Solver` : solveur par backtracking avec heuristique MRV

#### Vue (`neonaure/view.py`)
- `NumberSelector` : popup pour choisir un nombre dans une cellule (grille de boutons + croix pour fermer)
- `VictoryDialog` : popup de victoire avec bouton "Retour au menu"
- `GridView` : widget d'affichage de la grille (dessin, conflits en rouge, hover, signaux de clic)
- `GridSizeDialog` : popup pour choisir la taille d'une nouvelle grille
- `MainWindow` : fenetre principale du jeu (GridView + boutons undo/reset/map)
- `TestWindow` : fenetre de test standalone sans controleur

#### Controleur (`neonaure/controller.py`)
- `Controller` : fait le pont entre le modele et la vue
  - `__init__` : charge la grille depuis un JSON, cree la vue, initialise l'historique et le flag `_return_to_menu`
  - `update_view()` : synchronise l'affichage avec l'etat du modele (valeurs, bordures, immuables, patterns)
  - `handle_click()` : gere le clic sur une cellule, ouvre le NumberSelector, met a jour la valeur, verifie la victoire
  - `undo()` : annule le dernier coup
  - `reset_grid()` : remet toutes les cellules modifiables a 0
  - `generate_new_grid()` : genere une grille aleatoire aux dimensions donnees

#### Startup (`neonaure/startup.py`)
- `StartupWindow` : ecran de selection de niveau (liste des grilles, cartes avec apercu, progression)
- `LevelCard` : carte cliquable avec apercu miniature d'une grille
- `GenerateCard` : carte speciale pour generer une grille aleatoire 8x8
- `PreviewGridView` : GridView adaptee pour l'apercu sans texte

#### Package (`neonaure/__init__.py`)
- `run()` : boucle principale du jeu (startup → jeu → victoire → retour au menu si voulu)
