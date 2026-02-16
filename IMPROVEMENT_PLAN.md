# Plan d'Amélioration de la Qualité - APMLive

Ce document détaille les étapes techniques pour passer le projet **APMLive** d'un script "prototype" à une application de production robuste, maintenable et performante.

## 1. Architecture et Refactoring (Réalisé)

L'objectif était de séparer la logique métier de l'interface graphique pour faciliter la maintenance et les tests.

*   [x] **Séparation des responsabilités (MVC)** :
    *   `src/core/calculator.py` : Logique de calcul APM (Thread-safe).
    *   `src/ui/main_window.py` : Interface Tkinter.
    *   `src/core/exporter.py` : Gestion des exports de données.
    *   `src/utils/config.py` : Configuration centralisée.
    *   `src/main.py` : Point d'entrée unique.

*   [x] **Gestion de la Configuration** :
    *   Utilisation de `src/utils/config.py` pour les constantes.

## 2. Stabilité et Concurrence (Réalisé)

Le projet utilise des threads (via `pynput`) qui modifient des données lues par le thread principal (Tkinter).

*   [x] **Thread Safety** :
    *   Utilisation de `threading.Lock()` dans `APMCalculator` pour protéger `self.actions`.
    *   **Pattern Snapshot** implémenté pour minimiser la contention (verrouillage < 3µs).
    *   Export de données déplacé dans un thread dédié (`threading.Thread`) pour ne pas bloquer l'UI.

*   [x] **Optimisation Mémoire** :
    *   Nettoyage automatique de la liste `self.actions` implémenté (suppression des actions > window_size).

## 3. Tests et Qualité du Code (Réalisé)

Mettre en place des garde-fous pour éviter les régressions.

*   [x] **Tests Unitaires (Pytest)** :
    *   `tests/test_calculator.py` créé et fonctionnel.
    *   Couvre les cas nominaux : état initial, enregistrement, calcul APM, reset.

*   [x] **Tests de Performance (Benchmark)** :
    *   Script `tests/benchmark.py` créé.
    *   Validation des performances : > 4M actions/sec en input, latence de calcul < 10µs.

*   [x] **Typage Statique** :
    *   Ajout des **Type Hints** Python sur toutes les fonctions (`src/core`, `src/ui`).
    *   Vérification réussie avec `mypy` (Strict).

*   [x] **Formatage et Linting** :
    *   Code formaté avec `black`.
    *   Qualité validée avec `pylint` (Note: 9.80/10).

## 4. Packaging et Distribution (Réalisé)

Améliorer la façon dont l'application est construite et distribuée.

*   [x] **Gestion des Dépendances** :
    *   Figer les versions exactes dans `requirements.txt`.

*   [x] **Exécutable (PyInstaller)** :
    *   Créer un fichier `.spec` personnalisé pour PyInstaller.
    *   Ajouter une icône et des métadonnées de version au binaire.

## 5. Performance et Algorithmes 

Optimisations majeures pour garantir une fluidité parfaite et une consommation CPU minimale.

*   [x] **Moteur Graphique Vectoriel** :
    *   Remplacement de `matplotlib` (lourd) par `tkinter.Canvas` (natif, léger).
    *   Création du widget personnalisé `src/ui/graph_widget.py`.
    *   Résultat : Rendu fluide à 60+ FPS, consommation CPU négligeable.

*   [x] **Optimisation de la Concurrence (Snapshot Pattern)** :
    *   Réduction drastique de la contention sur le verrou global.
    *   Le calcul des métriques ne bloque plus l'enregistrement des inputs.
    *   Latence d'input améliorée (+4.3% de débit).

## 6. Recommandations Techniques Restantes (Roadmap)

Pour garantir la scalabilité et la robustesse en production à long terme :

*   [ ] **Optimisation de l'Export (Threading)** :
    *   **Problème** : `Exporter.export` crée un nouveau `threading.Thread` à chaque appel. Risque de saturation si la fréquence est élevée.
    *   **Solution** : Implémenter un pattern **Producer-Consumer** avec une `queue.Queue`. Le thread principal dépose les métriques, un thread worker unique (démon) les consomme et écrit sur le disque.

*   [ ] **Configuration Unifiée (pyproject.toml)** :
    *   Centraliser la configuration des outils (Black, Pylint, MyPy, Pytest) dans un fichier standard `pyproject.toml` à la racine du projet, remplaçant les configurations implicites.

*   [ ] **Intégration Continue (CI)** :
    *   Mettre en place un pipeline (GitHub Actions ou GitLab CI) pour exécuter automatiquement :
        1.  Installation des dépendances.
        2.  Linting (Black/Pylint).
        3.  Tests unitaires (Pytest).
        4.  Vérification de type (MyPy).
