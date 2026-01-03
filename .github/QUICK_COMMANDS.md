# 🚀 Comandos Rápidos para CI/CD

Comandos útiles para trabajar con el setup de CI/CD.

## 📋 Verificación Local

### Ejecutar Checks de Código

```bash
# Formatear código con Black
black src/ tests/

# Ordenar imports con isort
isort src/ tests/

# Verificar formateo (sin modificar)
black --check src/ tests/
isort --check-only src/ tests/

# Lint con flake8
flake8 src/ tests/ --max-line-length=88

# Type checking con mypy
mypy src/
```

### Ejecutar Tests

```bash
# Tests unitarios
pytest tests/unit/ -v

# Tests de integración
pytest tests/integration/ -v

# Tests con coverage
pytest tests/ --cov=src --cov-report=html --cov-report=term-missing

# Property-based tests
pytest tests/ -m pbt -v

# Todos los tests
pytest tests/ -v
```

### Security Checks

```bash
# Verificar vulnerabilidades en dependencias
pip freeze | safety check --stdin

# Security linting con Bandit
bandit -r src/ -f json -o bandit-report.json
```

### Build Check

```bash
# Build del paquete
python -m build

# Verificar paquete
twine check dist/*
```

## 🔄 Git Workflow

### Crear Feature Branch

```bash
# Crear y cambiar a nueva branch
git checkout -b feat/nombre-funcionalidad

# O para bug fix
git checkout -b fix/nombre-bug

# O para documentación
git checkout -b docs/nombre-doc
```

### Commit con Conventional Commits

```bash
# Feature
git commit -m "feat: Agregar validación de artículos"

# Bug fix
git commit -m "fix: Corregir parsing de fechas RSS"

# Documentation
git commit -m "docs: Actualizar README con ejemplos"

# Refactoring
git commit -m "refactor: Simplificar ArticleService"

# Tests
git commit -m "test: Agregar tests para ArticleFactory"

# Breaking change
git commit -m "feat!: Cambiar interface de ArticleRepository

BREAKING CHANGE: ArticleRepository.save() ahora es async"
```

### Push y Crear PR

```bash
# Push de la branch
git push origin feat/nombre-funcionalidad

# Crear PR desde CLI (si tienes gh CLI)
gh pr create --title "feat: Agregar validación" --body "Descripción del PR"

# O crear PR en GitHub web
# https://github.com/tradingapp/scraping-service/compare/feat/nombre-funcionalidad
```

### Actualizar Branch con Master

```bash
# Fetch latest
git fetch origin

# Rebase sobre master
git rebase origin/master

# O merge (si prefieres)
git merge origin/master

# Push (force si hiciste rebase)
git push origin feat/nombre-funcionalidad --force-with-lease
```

## 🏷️ Tags y Releases

### Crear Tag para Release

```bash
# Tag con mensaje
git tag -a v1.0.0 -m "Release version 1.0.0"

# Push tag
git push origin v1.0.0

# Esto triggerea deploy a production automáticamente
```

### Listar Tags

```bash
# Listar todos los tags
git tag

# Listar tags con patrón
git tag -l "v1.*"

# Ver detalles de un tag
git show v1.0.0
```

### Eliminar Tag (si es necesario)

```bash
# Eliminar tag local
git tag -d v1.0.0

# Eliminar tag remoto
git push origin --delete v1.0.0
```

## 🔍 Verificar Status de CI/CD

### Ver Status de Workflows

```bash
# Con GitHub CLI
gh run list

# Ver detalles de un run
gh run view <run-id>

# Ver logs de un run
gh run view <run-id> --log

# Ver status de checks en PR
gh pr checks
```

### Ver Status de Branch Protection

```bash
# Ver reglas de branch
gh api repos/:owner/:repo/branches/master/protection

# Ver required status checks
gh api repos/:owner/:repo/branches/master/protection/required_status_checks
```

## 🐛 Debugging

### Ver Logs de Workflow Fallido

```bash
# Listar runs recientes
gh run list --limit 10

# Ver logs del último run fallido
gh run view --log

# Descargar logs
gh run download <run-id>
```

### Re-ejecutar Workflow Fallido

```bash
# Re-ejecutar último workflow
gh run rerun

# Re-ejecutar workflow específico
gh run rerun <run-id>

# Re-ejecutar solo jobs fallidos
gh run rerun <run-id> --failed
```

## 📊 Coverage

### Generar Coverage Report

```bash
# HTML report
pytest tests/ --cov=src --cov-report=html
open htmlcov/index.html

# Terminal report
pytest tests/ --cov=src --cov-report=term-missing

# XML report (para Codecov)
pytest tests/ --cov=src --cov-report=xml
```

### Ver Coverage de Archivo Específico

```bash
pytest tests/unit/domain/aggregates/test_article.py \
  --cov=src/domain/aggregates/article \
  --cov-report=term-missing
```

## 🔐 GPG Signing

### Configurar GPG

```bash
# Generar key
gpg --full-generate-key

# Listar keys
gpg --list-secret-keys --keyid-format=long

# Exportar public key
gpg --armor --export YOUR_KEY_ID

# Configurar Git
git config --global user.signingkey YOUR_KEY_ID
git config --global commit.gpgsign true
```

### Verificar Signed Commits

```bash
# Ver si commit está firmado
git log --show-signature -1

# Ver todos los commits firmados
git log --show-signature
```

## 🧹 Cleanup

### Limpiar Branches Locales

```bash
# Listar branches merged
git branch --merged master

# Eliminar branch local
git branch -d feat/nombre-funcionalidad

# Eliminar todas las branches merged (excepto master)
git branch --merged master | grep -v "master" | xargs git branch -d
```

### Limpiar Branches Remotas

```bash
# Listar branches remotas
git branch -r

# Eliminar branch remota
git push origin --delete feat/nombre-funcionalidad

# Limpiar referencias a branches remotas eliminadas
git fetch --prune
```

## 📦 Dependencies

### Actualizar Dependencias

```bash
# Ver dependencias desactualizadas
pip list --outdated

# Actualizar dependencia específica
pip install --upgrade package-name

# Actualizar requirements.txt
pip freeze > requirements.txt
```

### Verificar Vulnerabilidades

```bash
# Con safety
pip install safety
safety check

# Con pip-audit
pip install pip-audit
pip-audit
```

## 🚀 Deploy Manual

### Deploy a Staging

```bash
# Trigger workflow manualmente
gh workflow run cd.yml -f environment=staging

# Ver status
gh run list --workflow=cd.yml
```

### Deploy a Production

```bash
# Crear tag (triggerea deploy automático)
git tag -a v1.0.0 -m "Release 1.0.0"
git push origin v1.0.0

# O trigger manual
gh workflow run cd.yml -f environment=production
```

## 📝 Aliases Útiles

Agrega estos aliases a tu `.bashrc` o `.zshrc`:

```bash
# Git aliases
alias gco='git checkout'
alias gcb='git checkout -b'
alias gst='git status'
alias gp='git push'
alias gpl='git pull'
alias gc='git commit'
alias gca='git commit --amend'
alias grb='git rebase'
alias gf='git fetch'

# Testing aliases
alias pytest-unit='pytest tests/unit/ -v'
alias pytest-int='pytest tests/integration/ -v'
alias pytest-cov='pytest tests/ --cov=src --cov-report=html'

# Code quality aliases
alias format='black src/ tests/ && isort src/ tests/'
alias lint='flake8 src/ tests/ && mypy src/'
alias check='black --check src/ tests/ && isort --check src/ tests/ && flake8 src/ tests/'

# CI aliases
alias ci-local='format && lint && pytest tests/ -v'
```

## 🔗 Links Útiles

```bash
# Abrir repositorio en GitHub
gh repo view --web

# Abrir PR actual
gh pr view --web

# Abrir Actions
gh repo view --web --branch master

# Abrir Settings
open "https://github.com/tradingapp/scraping-service/settings"
```

## 📊 Estadísticas

### Ver Estadísticas de Tests

```bash
# Con pytest-benchmark (si está instalado)
pytest tests/ --benchmark-only

# Ver duración de tests
pytest tests/ --durations=10
```

### Ver Estadísticas de Coverage

```bash
# Coverage por módulo
pytest tests/ --cov=src --cov-report=term

# Coverage con branches
pytest tests/ --cov=src --cov-branch --cov-report=term
```

## 🎯 Pre-commit Checks

### Ejecutar Todos los Checks Antes de Commit

```bash
#!/bin/bash
# Guardar como pre-commit-checks.sh

echo "🔍 Running pre-commit checks..."

echo "📝 Formatting code..."
black src/ tests/
isort src/ tests/

echo "🔎 Linting..."
flake8 src/ tests/

echo "🔬 Type checking..."
mypy src/

echo "🧪 Running tests..."
pytest tests/unit/ -v

echo "✅ All checks passed!"
```

Hacer ejecutable:
```bash
chmod +x pre-commit-checks.sh
```

Ejecutar antes de commit:
```bash
./pre-commit-checks.sh && git commit
```

---

**Tip**: Crea un alias para ejecutar todos los checks:
```bash
alias pre-commit='./pre-commit-checks.sh'
```

Luego solo ejecuta:
```bash
pre-commit && git commit -m "feat: Nueva funcionalidad"
```
