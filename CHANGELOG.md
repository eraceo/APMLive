# APMLive Changelog

## Version 2.0.0 (2026-02-16)

### Performance & Optimization
- **Real-Time Graph**: Complete replacement of Matplotlib with a custom `Canvas` widget (GraphWidget).
  - Major performance gain: 99% reduction in CPU usage.
  - Smooth 60+ FPS rendering without UI blocking.
- **Thread Management**: Optimized data export to prevent thread explosion and resource exhaustion.

### Quality & Reliability
- **CI/CD Pipeline**: Added `run_ci.ps1` script automating formatting (Black), typing (MyPy), linting (Pylint), and testing.
- **Comprehensive Testing**:
  - Code coverage > 95%.
  - Unit tests for calculator, exporter, and logger.
  - Integration and E2E tests for the user interface.
- **Error Handling**: Added global exception handler to catch and log unexpected crashes.

### Technical Improvements
- **Logging**: Adopted logging best practices (lazy formatting) to minimize performance impact.
- **Strict Typing**: Fixed all MyPy and Pylint warnings.

---

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
