# GitHub Configuration

Este directorio contiene toda la configuración de GitHub para el proyecto, incluyendo workflows de CI/CD, templates, y documentación de configuración.

## 📁 Estructura

```
.github/
├── workflows/              # GitHub Actions workflows
│   ├── ci.yml             # Continuous Integration
│   ├── cd.yml             # Continuous Deployment
│   ├── codeql.yml         # Security scanning
│   ├── dependency-review.yml
│   └── pr-checks.yml      # PR validation checks
├── ISSUE_TEMPLATE/        # Templates para issues
│   ├── bug_report.md
│   └── feature_request.md
├── CODEOWNERS             # Code ownership rules
├── pull_request_template.md
├── RULESET_MASTER.md      # Guía de configuración de rulesets
├── SETUP_GUIDE.md         # Guía completa de setup
└── README.md              # Este archivo
```

## 🚀 Quick Start

### Para Nuevos Desarrolladores

1. **Lee la guía de setup**: [SETUP_GUIDE.md](./SETUP_GUIDE.md)
2. **Configura signed commits**: Ver sección en SETUP_GUIDE.md
3. **Familiarízate con el workflow**: Lee [ci.yml](./workflows/ci.yml)

### Para Administradores

1. **Configura el repositorio**: Sigue [SETUP_GUIDE.md](./SETUP_GUIDE.md)
2. **Configura rulesets**: Sigue [RULESET_MASTER.md](./RULESET_MASTER.md)
3. **Configura teams**: Ver sección en SETUP_GUIDE.md

## 📋 Workflows

### CI - Continuous Integration

**Archivo**: [workflows/ci.yml](./workflows/ci.yml)

**Triggers**:
- Push a `master` o `develop`
- Pull requests a `master` o `develop`

**Jobs**:
1. **code-quality**: Black, isort, flake8, mypy
2. **unit-tests**: Tests unitarios con coverage
3. **integration-tests**: Tests de integración con DB
4. **property-tests**: Property-based tests con Hypothesis
5. **security**: Safety y Bandit scans
6. **build**: Build check del paquete
7. **test-summary**: Resumen de todos los tests

**Duración estimada**: 5-10 minutos

### CD - Continuous Deployment

**Archivo**: [workflows/cd.yml](./workflows/cd.yml)

**Triggers**:
- Push a `master`
- Tags `v*.*.*`
- Manual dispatch

**Jobs**:
1. **build-image**: Build Docker image
2. **deploy-staging**: Deploy a staging
3. **deploy-production**: Deploy a production (solo tags)
4. **migrate-database**: Run migrations

**Duración estimada**: 10-15 minutos

### CodeQL Security Analysis

**Archivo**: [workflows/codeql.yml](./workflows/codeql.yml)

**Triggers**:
- Push a `master` o `develop`
- Pull requests
- Schedule: Lunes a las 00:00 UTC

**Análisis**: Python security vulnerabilities

### Dependency Review

**Archivo**: [workflows/dependency-review.yml](./workflows/dependency-review.yml)

**Triggers**: Pull requests

**Checks**:
- Vulnerabilidades en dependencias
- Licencias prohibidas (GPL-2.0, GPL-3.0)

### PR Checks

**Archivo**: [workflows/pr-checks.yml](./workflows/pr-checks.yml)

**Triggers**: Pull requests

**Checks**:
1. **pr-title**: Formato de título (Conventional Commits)
2. **pr-size**: Tamaño del PR (XS/S/M/L/XL)
3. **breaking-changes**: Detecta breaking changes
4. **documentation**: Verifica si docs necesitan actualización
5. **test-coverage**: Verifica que hay tests para código nuevo

## 🛡️ Branch Protection

### Master Branch

**Protecciones activas**:
- ✅ Require pull request (1 approval)
- ✅ Require status checks to pass
- ✅ Require linear history
- ✅ Block force pushes
- ✅ Restrict deletions
- ✅ Require signed commits (recomendado)

**Status checks requeridos**:
- `code-quality`
- `unit-tests`
- `integration-tests`
- `property-tests`
- `security`
- `build`
- `pr-title`
- `dependency-review`

Ver configuración completa en [RULESET_MASTER.md](./RULESET_MASTER.md)

## 📝 Templates

### Pull Request Template

**Archivo**: [pull_request_template.md](./pull_request_template.md)

Incluye secciones para:
- Descripción del cambio
- Tipo de cambio
- Testing realizado
- Checklist de código
- Checklist de arquitectura (DDD, Clean Architecture, CQRS)
- Impacto y breaking changes

### Issue Templates

#### Bug Report
**Archivo**: [ISSUE_TEMPLATE/bug_report.md](./ISSUE_TEMPLATE/bug_report.md)

Para reportar bugs con:
- Pasos para reproducir
- Comportamiento esperado vs actual
- Entorno
- Bounded context afectado

#### Feature Request
**Archivo**: [ISSUE_TEMPLATE/feature_request.md](./ISSUE_TEMPLATE/feature_request.md)

Para proponer nuevas funcionalidades con:
- Descripción y motivación
- Casos de uso
- Impacto en arquitectura
- Estimación de esfuerzo

## 👥 Code Ownership

**Archivo**: [CODEOWNERS](./CODEOWNERS)

Define quién debe revisar cambios en diferentes partes del código:

- **Domain Layer**: `@tradingapp/architects` + `@tradingapp/backend-team`
- **Infrastructure**: `@tradingapp/backend-team` + `@tradingapp/devops`
- **Database**: `@tradingapp/backend-team` + `@tradingapp/dba`
- **API**: `@tradingapp/backend-team` + `@tradingapp/api-team`
- **Documentation**: `@tradingapp/tech-writers`

## 🔐 Secrets y Variables

### Repository Secrets

Configurados en **Settings** → **Secrets and variables** → **Actions**:

```
CODECOV_TOKEN
STAGING_DATABASE_URL
STAGING_REDIS_URL
PRODUCTION_DATABASE_URL
PRODUCTION_REDIS_URL
```

### Environment Secrets

#### Staging
```
DATABASE_URL
REDIS_URL
API_KEY
```

#### Production
```
DATABASE_URL
REDIS_URL
API_KEY
```

## 🎯 Status Checks

### Checks Requeridos para Merge

Todos estos checks deben pasar antes de hacer merge a `master`:

| Check | Descripción | Duración |
|-------|-------------|----------|
| `code-quality` | Black, isort, flake8, mypy | ~2 min |
| `unit-tests` | Tests unitarios + coverage | ~3 min |
| `integration-tests` | Tests con DB real | ~4 min |
| `property-tests` | Property-based tests | ~2 min |
| `security` | Safety + Bandit | ~1 min |
| `build` | Build check | ~1 min |
| `pr-title` | Conventional Commits | ~10 sec |
| `dependency-review` | Vulnerabilidades | ~30 sec |

**Total**: ~13-15 minutos

### Checks Opcionales

Estos checks corren pero no bloquean merge:

- `mypy` (type checking) - puede tener errores inicialmente
- `security` (safety check) - puede tener warnings

## 📊 Badges

Agrega estos badges a tu README.md:

```markdown
![CI](https://github.com/tradingapp/scraping-service/workflows/CI/badge.svg)
![CodeQL](https://github.com/tradingapp/scraping-service/workflows/CodeQL%20Security%20Analysis/badge.svg)
[![codecov](https://codecov.io/gh/tradingapp/scraping-service/branch/master/graph/badge.svg)](https://codecov.io/gh/tradingapp/scraping-service)
```

## 🔄 Workflow de Desarrollo

### 1. Crear Feature Branch

```bash
git checkout -b feat/nueva-funcionalidad
```

### 2. Desarrollar y Commitear

```bash
# Hacer cambios
git add .
git commit -m "feat: Agregar nueva funcionalidad"
```

### 3. Push y Crear PR

```bash
git push origin feat/nueva-funcionalidad
# Crear PR en GitHub
```

### 4. CI Automático

- Workflows se ejecutan automáticamente
- Status checks aparecen en el PR
- Revisores son asignados automáticamente (CODEOWNERS)

### 5. Code Review

- Esperar approval de reviewer
- Resolver comentarios
- Asegurar que todos los checks pasen

### 6. Merge

- Merge solo cuando:
  - ✅ Todos los status checks pasan
  - ✅ Tienes 1+ approval
  - ✅ Branch está actualizada
  - ✅ Conversaciones resueltas

### 7. Deploy Automático

- Merge a `master` → Deploy a staging
- Tag `v*.*.*` → Deploy a production

## 🐛 Troubleshooting

### Workflows no se ejecutan

1. Verifica que Actions estén habilitadas
2. Verifica permisos de workflows
3. Revisa logs en Actions tab

### Status checks no aparecen

1. Los checks solo aparecen después de ejecutarse una vez
2. Crea un PR de prueba
3. Luego agrégalos a required checks

### No puedo hacer merge

Verifica:
- ✅ Todos los required checks pasaron
- ✅ Tienes approval requerido
- ✅ Branch está actualizada
- ✅ Conversaciones resueltas

Ver más en [SETUP_GUIDE.md](./SETUP_GUIDE.md#troubleshooting)

## 📚 Documentación Adicional

- [SETUP_GUIDE.md](./SETUP_GUIDE.md) - Guía completa de configuración
- [RULESET_MASTER.md](./RULESET_MASTER.md) - Configuración de rulesets
- [GitHub Actions Docs](https://docs.github.com/en/actions)
- [GitHub Rulesets Docs](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-rulesets)

## 🤝 Contribuir

Para contribuir al proyecto:

1. Lee [SETUP_GUIDE.md](./SETUP_GUIDE.md)
2. Sigue el workflow de desarrollo
3. Usa los templates de PR e issues
4. Respeta las convenciones de código
5. Asegura que todos los tests pasen

## 📞 Soporte

- **DevOps**: @tradingapp/devops
- **Backend**: @tradingapp/backend-team
- **Arquitectura**: @tradingapp/architects

---

**Última actualización**: 2024-01-03
