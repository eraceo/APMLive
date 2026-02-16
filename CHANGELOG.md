# Changelog APMLive

## Version 1.1.0 (2025-02-16)

### Améliorations Techniques (Refactoring & Qualité)
- **Architecture MVC** : Séparation complète de la logique métier (`src/core`) et de l'interface graphique (`src/ui`).
- **Performance** : Migration du système de mise à jour de l'UI vers un **Pattern Observer**, éliminant le polling inefficace.
- **Fiabilité** : Ajout d'un système de **Logging centralisé** (`src/utils/logger.py`) remplaçant les `print()` par des fichiers de logs rotatifs.
- **Thread Safety** : Sécurisation des accès concurrents avec `threading.Lock()` et gestion optimisée des threads.

### Développement & Packaging
- **Tests** : Ajout de tests unitaires (`pytest`) pour le calculateur et de tests d'intégration pour l'UI.
- **Distribution** : Configuration complète **PyInstaller** (`apmlive.spec`) avec gestion des ressources et métadonnées.
- **Dépendances** : Fixation stricte des versions dans `requirements.txt` pour garantir la reproductibilité.
- **Qualité du Code** : Application du typage strict (`mypy`), formatage (`black`) et linting (`pylint`).

---

## Version 1.0.0 (2025)

### Fonctionnalités
- Version initiale
- Interface moderne et intuitive
- Calcul en temps réel des APM (Actions Par Minute)
- Export des données en TXT et JSON
- Compatible Windows 10/11


---

# APMLive Changelog

## Version 1.1.0 (2025-02-16)

### Technical Improvements (Refactoring & Quality)
- **MVC Architecture**: Complete separation of business logic (`src/core`) and user interface (`src/ui`).
- **Performance**: Migrated UI update system to **Observer Pattern**, eliminating inefficient polling.
- **Reliability**: Added **Centralized Logging** system (`src/utils/logger.py`) replacing `print()` with rotating log files.
- **Thread Safety**: Secured concurrent access with `threading.Lock()` and optimized thread management.

### Development & Packaging
- **Tests**: Added unit tests (`pytest`) for calculator and integration tests for UI.
- **Distribution**: Complete **PyInstaller** configuration (`apmlive.spec`) with resource management and metadata.
- **Dependencies**: Strict version pinning in `requirements.txt` to ensure reproducibility.
- **Code Quality**: Applied strict typing (`mypy`), formatting (`black`), and linting (`pylint`).

---

## Version 1.0.0 (2025)

### Features
- Initial release
- Modern and intuitive interface
- Real-time APM (Actions Per Minute) calculation
- Data export in TXT and JSON formats
- Windows 10/11 compatible
