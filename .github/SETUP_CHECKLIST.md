# ✅ Setup Checklist

Usa este checklist para verificar que todo está configurado correctamente.

## 📋 Fase 1: Archivos del Repositorio

- [ ] Todos los workflows están en `.github/workflows/`
  - [ ] `ci.yml`
  - [ ] `cd.yml`
  - [ ] `codeql.yml`
  - [ ] `dependency-review.yml`
  - [ ] `pr-checks.yml`

- [ ] Templates están configurados
  - [ ] `.github/pull_request_template.md`
  - [ ] `.github/ISSUE_TEMPLATE/bug_report.md`
  - [ ] `.github/ISSUE_TEMPLATE/feature_request.md`

- [ ] Archivos de configuración existen
  - [ ] `.github/CODEOWNERS`
  - [ ] `.github/README.md`
  - [ ] `.github/RULESET_MASTER.md`
  - [ ] `.github/SETUP_GUIDE.md`

- [ ] Archivos fueron pusheados a GitHub
  ```bash
  git add .github/
  git commit -m "ci: Configurar CI/CD workflows y rulesets"
  git push origin master
  ```

## 🔧 Fase 2: Configuración de GitHub

### GitHub Actions

- [ ] Actions habilitadas
  - Ruta: `Settings → Actions → General`
  - [ ] "Allow all actions and reusable workflows" seleccionado
  - [ ] "Read and write permissions" seleccionado
  - [ ] "Allow GitHub Actions to create and approve pull requests" marcado

### Secrets

- [ ] Repository secrets configurados
  - Ruta: `Settings → Secrets and variables → Actions → Secrets`
  - [ ] `CODECOV_TOKEN` (opcional, para coverage)
  - [ ] `STAGING_DATABASE_URL`
  - [ ] `STAGING_REDIS_URL`
  - [ ] `PRODUCTION_DATABASE_URL`
  - [ ] `PRODUCTION_REDIS_URL`

### Environments

- [ ] Environment "staging" creado
  - Ruta: `Settings → Environments → New environment`
  - [ ] Name: `staging`
  - [ ] Required reviewers: Ninguno (o según preferencia)
  - [ ] Deployment branches: `master`
  - [ ] Secrets configurados:
    - [ ] `DATABASE_URL`
    - [ ] `REDIS_URL`
    - [ ] `API_KEY`

- [ ] Environment "production" creado
  - [ ] Name: `production`
  - [ ] Required reviewers: 1-2 personas ⚠️ IMPORTANTE
  - [ ] Wait timer: 5 minutes (opcional)
  - [ ] Deployment branches: `master` y tags `v*.*.*`
  - [ ] Secrets configurados:
    - [ ] `DATABASE_URL`
    - [ ] `REDIS_URL`
    - [ ] `API_KEY`

### Code Security

- [ ] Code security habilitado
  - Ruta: `Settings → Code security and analysis`
  - [ ] Dependency graph
  - [ ] Dependabot alerts
  - [ ] Dependabot security updates
  - [ ] Code scanning (CodeQL)
  - [ ] Secret scanning
  - [ ] Push protection

## 🛡️ Fase 3: Branch Protection (Rulesets)

### Crear Ruleset

- [ ] Ruleset creado para master
  - Ruta: `Settings → Rules → Rulesets → New branch ruleset`
  - [ ] Name: `master-protection`
  - [ ] Enforcement status: **Active**
  - [ ] Target: Include by pattern → `master`

### Reglas Configuradas

#### Branch Protection Rules
- [ ] Restrict deletions ✅
- [ ] Require linear history ✅
- [ ] Block force pushes ✅

#### Pull Request Rules
- [ ] Require a pull request before merging ✅
  - [ ] Required approvals: **1**
  - [ ] Dismiss stale pull request approvals ✅
  - [ ] Require review from Code Owners ✅
  - [ ] Require approval of most recent push ✅
  - [ ] Require conversation resolution ✅

#### Status Check Rules
- [ ] Require status checks to pass before merging ✅
  - [ ] Require branches to be up to date ✅
  - [ ] Status checks agregados:
    - [ ] `code-quality`
    - [ ] `unit-tests`
    - [ ] `integration-tests`
    - [ ] `property-tests`
    - [ ] `security`
    - [ ] `build`
    - [ ] `pr-title`
    - [ ] `dependency-review`

#### Commit Rules
- [ ] Require signed commits ✅ (recomendado)

#### Deployment Rules (opcional)
- [ ] Require deployments to succeed
  - [ ] Required environments: `staging`

### Bypass List
- [ ] Repository administrators agregados (solo emergencias)

## 👥 Fase 4: Teams y Permisos (si es organización)

### Crear Teams

- [ ] Teams creados en organización
  - [ ] `@tradingapp/backend-team`
  - [ ] `@tradingapp/architects`
  - [ ] `@tradingapp/devops`
  - [ ] `@tradingapp/dba`
  - [ ] `@tradingapp/api-team`
  - [ ] `@tradingapp/tech-writers`

### Asignar Permisos

- [ ] Permisos asignados
  - Ruta: `Settings → Collaborators and teams`
  - [ ] `@tradingapp/backend-team` → Write
  - [ ] `@tradingapp/architects` → Maintain
  - [ ] `@tradingapp/devops` → Admin
  - [ ] `@tradingapp/dba` → Write
  - [ ] `@tradingapp/api-team` → Write
  - [ ] `@tradingapp/tech-writers` → Write

## 🔐 Fase 5: Developer Setup

### Cada Desarrollador Debe

- [ ] Configurar GPG signing
  ```bash
  # 1. Generar GPG key
  gpg --full-generate-key
  
  # 2. Listar keys
  gpg --list-secret-keys --keyid-format=long
  
  # 3. Exportar public key
  gpg --armor --export YOUR_KEY_ID
  
  # 4. Agregar a GitHub
  # Settings → SSH and GPG keys → New GPG key
  
  # 5. Configurar Git
  git config --global user.signingkey YOUR_KEY_ID
  git config --global commit.gpgsign true
  
  # 6. Configurar GPG_TTY
  echo 'export GPG_TTY=$(tty)' >> ~/.bashrc  # o ~/.zshrc
  source ~/.bashrc
  ```

- [ ] Instalar dependencias de desarrollo
  ```bash
  pip install -e ".[dev]"
  ```

- [ ] Configurar pre-commit hooks (opcional)
  ```bash
  pip install pre-commit
  pre-commit install
  ```

## 🧪 Fase 6: Verificación

### Test 1: Workflows Ejecutan

- [ ] Crear PR de prueba
  ```bash
  git checkout -b test/ci-verification
  echo "# Test CI/CD" >> TEST.md
  git add TEST.md
  git commit -m "test: Verificar CI/CD setup"
  git push origin test/ci-verification
  ```

- [ ] Verificar en GitHub
  - [ ] PR creado exitosamente
  - [ ] Workflows se ejecutan automáticamente
  - [ ] Status checks aparecen en el PR
  - [ ] Todos los checks pasan (o fallan apropiadamente)

### Test 2: Branch Protection Funciona

- [ ] Intentar push directo a master (debe fallar)
  ```bash
  git checkout master
  echo "test" >> README.md
  git commit -am "test: Direct push"
  git push origin master
  # ❌ Debe fallar con error de branch protection
  ```

- [ ] Intentar force push (debe fallar)
  ```bash
  git push --force origin master
  # ❌ Debe fallar
  ```

- [ ] Intentar eliminar branch (debe fallar)
  ```bash
  git push origin --delete master
  # ❌ Debe fallar
  ```

### Test 3: PR Workflow Completo

- [ ] Crear feature branch
  ```bash
  git checkout -b feat/test-workflow
  ```

- [ ] Hacer cambios y commit
  ```bash
  echo "test" >> README.md
  git add README.md
  git commit -m "feat: Test workflow completo"
  ```

- [ ] Push y crear PR
  ```bash
  git push origin feat/test-workflow
  # Crear PR en GitHub
  ```

- [ ] Verificar PR
  - [ ] Workflows ejecutan
  - [ ] Status checks aparecen
  - [ ] PR checks ejecutan (title, size, etc.)
  - [ ] Reviewers asignados automáticamente (CODEOWNERS)
  - [ ] Merge bloqueado hasta que checks pasen
  - [ ] Merge bloqueado hasta tener approval

- [ ] Aprobar y hacer merge
  - [ ] Obtener approval de reviewer
  - [ ] Todos los checks pasan
  - [ ] Merge exitoso
  - [ ] Branch eliminada automáticamente

### Test 4: Deploy Workflow

- [ ] Verificar deploy a staging
  - [ ] Merge a master triggerea deploy a staging
  - [ ] Workflow `cd.yml` ejecuta
  - [ ] Deploy a staging exitoso

- [ ] Verificar deploy a production (opcional)
  ```bash
  git tag -a v0.1.0 -m "Test release"
  git push origin v0.1.0
  ```
  - [ ] Tag triggerea deploy a production
  - [ ] Required reviewers aprueban
  - [ ] Deploy a production exitoso

### Test 5: Security Scanning

- [ ] CodeQL ejecuta
  - [ ] Workflow `codeql.yml` ejecuta
  - [ ] No hay alertas críticas
  - [ ] Alertas visibles en Security tab

- [ ] Dependabot funciona
  - [ ] Dependabot alerts habilitado
  - [ ] Alerts visibles en Security tab
  - [ ] PRs automáticos para updates (si hay)

## 📊 Fase 7: Monitoreo

### Verificar Regularmente

- [ ] Actions ejecutan correctamente
  - Ruta: `Actions` tab
  - [ ] Workflows exitosos
  - [ ] No hay failures persistentes

- [ ] Security alerts
  - Ruta: `Security` tab
  - [ ] Revisar Dependabot alerts
  - [ ] Revisar Code scanning alerts
  - [ ] Revisar Secret scanning alerts

- [ ] Branch protection
  - Ruta: `Settings → Rules → Rulesets`
  - [ ] Ruleset activo
  - [ ] Status checks actualizados

## 📝 Fase 8: Documentación

### Actualizar README

- [ ] Agregar badges al README.md
  ```markdown
  ![CI](https://github.com/tradingapp/scraping-service/workflows/CI/badge.svg)
  ![CodeQL](https://github.com/tradingapp/scraping-service/workflows/CodeQL%20Security%20Analysis/badge.svg)
  [![codecov](https://codecov.io/gh/tradingapp/scraping-service/branch/master/graph/badge.svg)](https://codecov.io/gh/tradingapp/scraping-service)
  ```

- [ ] Agregar sección de CI/CD al README
  ```markdown
  ## CI/CD
  
  Este proyecto usa GitHub Actions para CI/CD automático.
  
  - **CI**: Ejecuta en cada PR y push a master/develop
  - **CD**: Deploy automático a staging (master) y production (tags)
  - **Security**: CodeQL scanning y Dependabot
  
  Ver [.github/README.md](.github/README.md) para más detalles.
  ```

### Documentar para el Equipo

- [ ] Compartir guías con el equipo
  - [ ] `.github/SETUP_GUIDE.md` - Setup completo
  - [ ] `.github/RULESET_MASTER.md` - Configuración de rulesets
  - [ ] `.github/QUICK_COMMANDS.md` - Comandos útiles
  - [ ] `CICD_SETUP_SUMMARY.md` - Resumen ejecutivo

- [ ] Realizar sesión de onboarding
  - [ ] Explicar workflow de desarrollo
  - [ ] Demostrar creación de PR
  - [ ] Mostrar cómo revisar status checks
  - [ ] Explicar proceso de deploy

## 🎉 Completado

Una vez que todos los items estén marcados:

✅ **Tu repositorio está completamente configurado con CI/CD profesional**

### Próximos Pasos

1. Comenzar desarrollo normal
2. Crear PRs siguiendo el workflow
3. Monitorear Actions y Security tabs
4. Actualizar documentación según sea necesario
5. Revisar y ajustar rulesets según experiencia del equipo

---

## 📞 Soporte

Si tienes problemas:

1. Revisa [SETUP_GUIDE.md](./SETUP_GUIDE.md#troubleshooting)
2. Revisa logs en Actions tab
3. Contacta a @tradingapp/devops

---

**Última actualización**: 2024-01-03
