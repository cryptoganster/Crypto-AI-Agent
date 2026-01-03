# Implementation Plan: Configure Pre-Commit Hooks

## Overview

Este plan implementa la configuración completa de pre-commit hooks para el proyecto, incluyendo refactorización de estructura hacia `apps/researcher/` y configuración de pre-push hooks.

## Tasks

- [ ] 0. Preparación inicial - Commit de estado actual
  - Ejecutar `git add .` para stagear todos los cambios actuales
  - Hacer commit: `git commit -m "chore: save current state before pre-commit setup"`
  - Verificar que working directory está limpio
  - _Requirements: Preparación_

- [ ] 1. Refactorizar estructura del proyecto hacia `apps/researcher/`
  - [ ] 1.1 Crear directorio `apps/researcher/`
  - [ ] 1.2 Mover `src/` → `apps/researcher/src/`
  - [ ] 1.3 Mover `tests/` → `apps/researcher/tests/`
  - [ ] 1.4 Mover `venv/` → `apps/researcher/venv/`
  - [ ] 1.5 Mover `logs/` → `apps/researcher/logs/`
  - [ ] 1.6 Mover `htmlcov/` → `apps/researcher/htmlcov/`
  - [ ] 1.7 Mover `alembic/` → `apps/researcher/alembic/`
  - [ ] 1.8 Mover `.hypothesis/` → `apps/researcher/.hypothesis/`
  - [ ] 1.9 Mover `.mypy_cache/` → `apps/researcher/.mypy_cache/`
  - [ ] 1.10 Mover `.pytest_cache/` → `apps/researcher/.pytest_cache/`
  - [ ] 1.11 Mover `.coverage` → `apps/researcher/.coverage`
  - [ ] 1.12 Mover `.dockerignore` → `apps/researcher/.dockerignore`
  - [ ] 1.13 Mover `.env` → `apps/researcher/.env`
  - [ ] 1.14 Mover `.env.example` → `apps/researcher/.env.example`
  - [ ] 1.15 Mover `alembic.ini` → `apps/researcher/alembic.ini`
  - [ ] 1.16 Mover `Dockerfile` → `apps/researcher/Dockerfile`
  - [ ] 1.17 Mover `pyproject.toml` → `apps/researcher/pyproject.toml`
  - [ ] 1.18 Mover `pytest.ini` → `apps/researcher/pytest.ini`
  - [ ] 1.19 Mover `requirements.txt` → `apps/researcher/requirements.txt`
  - [ ] 1.20 Mover `run.py` → `apps/researcher/run.py`
  - [ ] 1.21 Actualizar imports en código si es necesario
  - [ ] 1.22 Actualizar paths en archivos de configuración
  - [ ] 1.23 Actualizar .gitignore para nueva estructura
  - [ ] 1.24 Hacer commit: `git commit -m "refactor: move researcher app to apps/researcher/"`
  - _Requirements: Refactorización de estructura_

- [ ] 2. Crear archivo de configuración principal `.pre-commit-config.yaml`
  - Configurar repos de Black, isort, Flake8, MyPy
  - Configurar hooks de validación de archivos
  - Configurar detección de secretos
  - Configurar CI settings
  - Configurar pre-push hooks
  - _Requirements: 1.1, 2.1, 3.1, 4.1, 5.1, 6.1-6.5, 7.1-7.3_

- [ ] 3. Configurar pre-push hooks
  - [ ] 3.1 Agregar configuración de pre-push en `.pre-commit-config.yaml`
  - [ ] 3.2 Configurar hook para ejecutar tests antes de push
  - [ ] 3.3 Configurar hook para verificar que no hay TODOs críticos
  - [ ] 3.4 Configurar hook para verificar que branch está actualizado
  - [ ] 3.5 Instalar pre-push hooks: `pre-commit install --hook-type pre-push`
  - [ ] 3.6 Documentar uso de pre-push hooks en README.md
  - _Requirements: Pre-push hooks_

- [ ] 4. Crear archivo de configuración de Flake8 `.flake8`
  - Configurar max-line-length=88 (compatible con Black)
  - Configurar extend-ignore para E203, W503
  - Configurar exclusiones de directorios
  - Configurar per-file-ignores para __init__.py
  - _Requirements: 4.1, 4.2, 4.4_

- [ ] 5. Crear baseline de secretos `.secrets.baseline`
  - Ejecutar detect-secrets scan inicial
  - Generar archivo baseline vacío
  - Documentar cómo actualizar baseline
  - _Requirements: 7.1, 7.2, 7.4_

- [ ] 6. Actualizar `requirements.txt` con pre-commit
  - Agregar pre-commit a dependencias de desarrollo
  - Verificar versiones de herramientas (black, isort, flake8, mypy)
  - _Requirements: 1.3_

- [ ] 7. Actualizar `README.md` con documentación de pre-commit
  - Agregar sección "Development Setup"
  - Documentar instalación de pre-commit
  - Documentar uso de hooks (pre-commit y pre-push)
  - Documentar bypass de hooks
  - Documentar solución de errores comunes
  - _Requirements: 1.4, 11.1, 11.2, 11.3, 11.4, 11.5_

- [ ] 8. Instalar y configurar pre-commit en el proyecto
  - Activar virtualenv
  - Instalar dependencias de desarrollo: `pip install -e ".[dev]"`
  - Instalar pre-commit hooks: `pre-commit install`
  - Instalar pre-push hooks: `pre-commit install --hook-type pre-push`
  - Verificar instalación: `pre-commit --version`
  - _Requirements: 1.2_

- [ ] 9. Ejecutar pre-commit en todos los archivos existentes
  - Ejecutar: `pre-commit run --all-files`
  - Revisar y corregir errores encontrados
  - Hacer commit de cambios auto-corregidos
  - _Requirements: 2.3, 3.3, 6.5_

- [ ] 10. Crear script de instalación para nuevos desarrolladores
  - Crear `scripts/setup-dev.sh`
  - Incluir instalación de virtualenv
  - Incluir instalación de dependencias
  - Incluir instalación de pre-commit hooks
  - Incluir instalación de pre-push hooks
  - _Requirements: 11.1_

- [ ] 11. Crear documentación de troubleshooting
  - Crear `docs/pre-commit-troubleshooting.md`
  - Documentar errores comunes y soluciones
  - Incluir ejemplos de uso
  - Documentar troubleshooting de pre-push hooks
  - _Requirements: 11.3_

- [ ] 12. Configurar CI/CD para ejecutar pre-commit
  - Crear workflow de GitHub Actions (si aplica)
  - Configurar para ejecutar en push y PR
  - Usar mismas versiones que local
  - _Requirements: 10.1, 10.2, 10.3, 10.4_

- [ ] 13. Checkpoint - Verificar configuración completa
  - Verificar que `.pre-commit-config.yaml` existe
  - Verificar que `.flake8` existe
  - Verificar que `.secrets.baseline` existe
  - Verificar que hooks están instalados (pre-commit y pre-push)
  - Verificar que README.md está actualizado
  - Ejecutar `pre-commit run --all-files` exitosamente
  - Hacer commit de prueba para verificar hooks
  - Hacer push de prueba para verificar pre-push hooks

- [ ] 14. Crear guía de contribución `CONTRIBUTING.md`
  - Documentar proceso de desarrollo
  - Incluir sección de pre-commit hooks
  - Incluir sección de pre-push hooks
  - Documentar estándares de código
  - _Requirements: 11.1, 11.2_

- [ ] 15. Optimizar performance de hooks
  - Configurar cache de pre-commit
  - Verificar que hooks solo corren en archivos staged
  - Medir tiempo de ejecución de hooks
  - Optimizar si excede 10 segundos
  - _Requirements: 8.1, 8.2, 8.3, 8.4_

- [ ] 16. Documentar proceso de bypass de hooks
  - Agregar sección en README.md
  - Documentar cuándo es apropiado usar --no-verify
  - Documentar cómo ejecutar hooks manualmente después
  - Documentar bypass de pre-push hooks
  - _Requirements: 9.1, 9.2, 9.3, 9.4_

- [ ] 17. Crear tests de validación de configuración
  - Test: Verificar que .pre-commit-config.yaml es válido
  - Test: Verificar que todas las herramientas están instaladas
  - Test: Verificar que hooks se ejecutan correctamente
  - Test: Verificar que pre-push hooks funcionan
  - _Requirements: 8.3_

- [ ] 18. Final checkpoint - Validación completa
  - Todos los archivos de configuración creados
  - Estructura refactorizada a `apps/researcher/`
  - Documentación completa
  - Hooks funcionando correctamente (pre-commit y pre-push)
  - CI/CD configurado (si aplica)
  - Equipo puede instalar y usar sin problemas
  - Tiempo de ejecución < 10 segundos

## Notes

- **Refactorización**: Toda la app se moverá a `apps/researcher/` para preparar estructura multi-app
- **Pre-commit hooks**: Se ejecutan automáticamente después de `git commit`
- **Pre-push hooks**: Se ejecutan automáticamente antes de `git push`
- Algunos hooks auto-corrigen archivos (Black, isort, trailing whitespace)
- Otros hooks requieren corrección manual (Flake8, MyPy)
- El bypass con `--no-verify` debe usarse solo en emergencias
- Pre-commit cachea herramientas en `~/.cache/pre-commit`
- La primera ejecución puede tardar más (descarga herramientas)
- Ejecutar `pre-commit autoupdate` mensualmente para actualizar versiones
- Pre-push hooks pueden tardar más (ejecutan tests)

## Success Criteria

- ✅ Estructura refactorizada a `apps/researcher/`
- ✅ Archivo `.pre-commit-config.yaml` creado y funcional
- ✅ Pre-push hooks configurados y funcionando
- ✅ Todos los hooks configurados ejecutan correctamente
- ✅ Documentación completa en README.md
- ✅ Pre-commit instalado en dependencias de desarrollo
- ✅ Tiempo de ejecución de pre-commit hooks < 10 segundos
- ✅ Cero falsos positivos en hooks
- ✅ Equipo puede instalar y usar sin problemas
- ✅ CI/CD ejecuta mismos checks que local
