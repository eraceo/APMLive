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
    *   Export de données déplacé dans un thread dédié (`threading.Thread`) pour ne pas bloquer l'UI.

*   [x] **Optimisation Mémoire** :
    *   Nettoyage automatique de la liste `self.actions` implémenté (suppression des actions > window_size).

## 3. Tests et Qualité du Code (Réalisé)

Mettre en place des garde-fous pour éviter les régressions.

*   [x] **Tests Unitaires (Pytest)** :
    *   `tests/test_calculator.py` créé et fonctionnel.
    *   Couvre les cas nominaux : état initial, enregistrement, calcul APM, reset.

*   [x] **Typage Statique** :
    *   Ajout des **Type Hints** Python sur toutes les fonctions (`src/core`, `src/ui`).
    *   Vérification réussie avec `mypy` (Strict).

*   [x] **Formatage et Linting** :
    *   Code formaté avec `black`.
    *   Qualité validée avec `pylint` (Note: 9.80/10).

## 4. Packaging et Distribution (Réalisé)

Améliorer la façon dont l'application est construite et distribuée.

*   [x] **Gestion des Dépendances** :
    *   Figer les versions exactes dans `requirements.txt` (déjà fait, à maintenir).

*   [x] **Exécutable (PyInstaller)** :
    *   Créer un fichier `.spec` personnalisé pour PyInstaller.
    *   Ajouter une icône et des métadonnées de version au binaire.

## 5. Nouvelles Recommandations (Analyse v2.0)

Suite à la refactorisation, voici les nouveaux points d'amélioration identifiés :

*   [x] **Gestion des Exceptions (Logging)** :
    *   Actuellement, `exporter.py` utilise `print()` en cas d'erreur.
    *   Il faut implémenter un module `logging` pour écrire les erreurs dans un fichier de log (ex: `%LOCALAPPDATA%\APMLive\error.log`).

*   [x] **Tests d'Intégration UI** :
    *   Ajouter des tests vérifiant le lancement correct de l'interface et le binding des callbacks, même sans interaction humaine.

*   [x] **Design Pattern Observer** :
    *   Remplacer le polling (100ms) de `MainWindow` par une approche événementielle si la charge CPU devient un problème (actuellement acceptable pour Tkinter).

## 6. Recommandations Techniques Approfondies (Analyse v3.0)

Pour garantir la scalabilité et la robustesse en production :

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
