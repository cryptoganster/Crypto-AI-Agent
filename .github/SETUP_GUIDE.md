# Guía de Configuración del Repositorio

Esta guía te ayudará a configurar completamente el repositorio con CI/CD, rulesets, y protecciones de branch.

## Tabla de Contenidos

1. [Configuración Inicial](#configuración-inicial)
2. [Configurar Secrets](#configurar-secrets)
3. [Configurar Rulesets](#configurar-rulesets)
4. [Configurar Environments](#configurar-environments)
5. [Configurar Code Scanning](#configurar-code-scanning)
6. [Configurar Teams](#configurar-teams)
7. [Verificación](#verificación)

---

## Configuración Inicial

### 1. Habilitar GitHub Actions

1. Ve a **Settings** → **Actions** → **General**
2. En "Actions permissions", selecciona: **Allow all actions and reusable workflows**
3. En "Workflow permissions", selecciona: **Read and write permissions**
4. Marca: **Allow GitHub Actions to create and approve pull requests**
5. Click **Save**

### 2. Habilitar Dependabot

1. Ve a **Settings** → **Code security and analysis**
2. Habilita:
   - ✅ **Dependency graph**
   - ✅ **Dependabot alerts**
   - ✅ **Dependabot security updates**
3. Click en **Enable** para cada opción

---

## Configurar Secrets

### Repository Secrets

Ve a **Settings** → **Secrets and variables** → **Actions** → **New repository secret**

Agrega los siguientes secrets:

#### Para CI/CD
```
CODECOV_TOKEN=<tu-token-de-codecov>
```

#### Para Staging
```
STAGING_DATABASE_URL=postgresql://user:pass@host:5432/staging_db
STAGING_REDIS_URL=redis://host:6379/0
```

#### Para Production
```
PRODUCTION_DATABASE_URL=postgresql://user:pass@host:5432/prod_db
PRODUCTION_REDIS_URL=redis://host:6379/0
```

### Environment Variables (no secretas)

Ve a **Settings** → **Secrets and variables** → **Actions** → **Variables** → **New repository variable**

```
PYTHON_VERSION=3.11
ENVIRONMENT=production
```

---

## Configurar Rulesets

### Crear Ruleset para Master

1. Ve a **Settings** → **Rules** → **Rulesets**
2. Click **New ruleset** → **New branch ruleset**

#### Configuración Básica
```
Name: master-protection
Enforcement status: Active
Bypass list: Repository administrators (solo emergencias)
```

#### Target Branches
```
Target: Include by pattern
Pattern: master
```

#### Reglas a Activar

**Branch Protection Rules**:
- ✅ Restrict deletions
- ✅ Require linear history
- ✅ Block force pushes

**Pull Request Rules**:
- ✅ Require a pull request before merging
  - Required approvals: **1**
  - ✅ Dismiss stale pull request approvals
  - ✅ Require review from Code Owners
  - ✅ Require approval of most recent push
  - ✅ Require conversation resolution

**Status Check Rules**:
- ✅ Require status checks to pass before merging
  - ✅ Require branches to be up to date
  - Status checks requeridos:
    - `code-quality`
    - `unit-tests`
    - `integration-tests`
    - `property-tests`
    - `security`
    - `build`
    - `pr-title`
    - `dependency-review`

**Commit Rules**:
- ✅ Require signed commits (recomendado)

**Deployment Rules** (opcional):
- ✅ Require deployments to succeed
  - Required environments: `staging`

3. Click **Create**

### Crear Ruleset para Develop (opcional)

Repite el proceso con configuración más relajada:
```
Name: develop-protection
Pattern: develop
Required approvals: 0 (o 1 si prefieres)
Status checks: Solo los críticos
```

---

## Configurar Environments

### Crear Environment: Staging

1. Ve a **Settings** → **Environments**
2. Click **New environment**
3. Name: `staging`
4. Click **Configure environment**

**Configuración**:
- ✅ **Required reviewers**: Agrega reviewers (opcional)
- ✅ **Wait timer**: 0 minutes
- **Deployment branches**: Selected branches → `master`

**Environment secrets**:
```
DATABASE_URL=<staging-db-url>
REDIS_URL=<staging-redis-url>
API_KEY=<staging-api-key>
```

### Crear Environment: Production

1. Click **New environment**
2. Name: `production`
3. Click **Configure environment**

**Configuración**:
- ✅ **Required reviewers**: Agrega 1-2 reviewers (IMPORTANTE)
- ✅ **Wait timer**: 5 minutes (opcional)
- **Deployment branches**: Selected branches → `master` y tags `v*.*.*`

**Environment secrets**:
```
DATABASE_URL=<production-db-url>
REDIS_URL=<production-redis-url>
API_KEY=<production-api-key>
```

---

## Configurar Code Scanning

### Habilitar CodeQL

1. Ve a **Settings** → **Code security and analysis**
2. En "Code scanning", click **Set up** → **Advanced**
3. Esto creará `.github/workflows/codeql.yml` (ya lo tenemos)
4. Si ya existe, solo habilita: **CodeQL analysis**

### Configurar Alertas

1. En **Settings** → **Code security and analysis**
2. Habilita:
   - ✅ **Code scanning**
   - ✅ **Secret scanning**
   - ✅ **Push protection** (previene commits con secrets)

---

## Configurar Teams

### Crear Teams en GitHub

1. Ve a tu organización → **Teams**
2. Crea los siguientes teams:

```
@tradingapp/backend-team
@tradingapp/architects
@tradingapp/devops
@tradingapp/dba
@tradingapp/api-team
@tradingapp/tech-writers
```

### Asignar Permisos

1. Ve a **Settings** → **Collaborators and teams**
2. Agrega cada team con permisos apropiados:

```
@tradingapp/backend-team → Write
@tradingapp/architects → Maintain
@tradingapp/devops → Admin
@tradingapp/dba → Write
@tradingapp/api-team → Write
@tradingapp/tech-writers → Write
```

### Actualizar CODEOWNERS

El archivo `.github/CODEOWNERS` ya está configurado con estos teams.

---

## Configurar Branch Protection (Legacy - si no usas Rulesets)

Si prefieres usar Branch Protection Rules en lugar de Rulesets:

1. Ve a **Settings** → **Branches**
2. Click **Add branch protection rule**
3. Branch name pattern: `master`
4. Configura las mismas reglas que en Rulesets

---

## Configurar Signed Commits

### Para Desarrolladores

Cada desarrollador debe configurar GPG:

```bash
# 1. Generar GPG key
gpg --full-generate-key
# Selecciona: RSA and RSA, 4096 bits, no expira

# 2. Listar keys
gpg --list-secret-keys --keyid-format=long

# 3. Exportar public key
gpg --armor --export YOUR_KEY_ID

# 4. Agregar a GitHub
# Settings → SSH and GPG keys → New GPG key → Pegar key

# 5. Configurar Git
git config --global user.signingkey YOUR_KEY_ID
git config --global commit.gpgsign true

# 6. Configurar GPG_TTY (agregar a ~/.bashrc o ~/.zshrc)
export GPG_TTY=$(tty)
```

---

## Verificación

### Checklist de Verificación

Verifica que todo esté configurado correctamente:

#### GitHub Actions
- [ ] Actions están habilitadas
- [ ] Workflows tienen permisos de escritura
- [ ] Secrets están configurados
- [ ] Variables de entorno están configuradas

#### Rulesets
- [ ] Ruleset `master-protection` está activo
- [ ] Status checks están configurados
- [ ] Pull requests requieren approval
- [ ] Force push está bloqueado
- [ ] Deletion está bloqueada

#### Environments
- [ ] Environment `staging` existe
- [ ] Environment `production` existe
- [ ] Production requiere reviewers
- [ ] Secrets de environment están configurados

#### Code Security
- [ ] Dependabot está habilitado
- [ ] CodeQL está habilitado
- [ ] Secret scanning está habilitado
- [ ] Push protection está habilitado

#### Teams
- [ ] Teams están creados
- [ ] Permisos están asignados
- [ ] CODEOWNERS está configurado

### Test del Setup

#### Test 1: Crear PR de Prueba

```bash
git checkout -b test/setup-verification
echo "# Test" >> TEST.md
git add TEST.md
git commit -m "test: Verificar setup de CI/CD"
git push origin test/setup-verification
```

Crea PR en GitHub y verifica:
- ✅ Workflows se ejecutan automáticamente
- ✅ Status checks aparecen
- ✅ PR title check funciona
- ✅ Merge está bloqueado hasta que checks pasen

#### Test 2: Verificar Protecciones

```bash
# Intentar push directo a master (debe fallar)
git checkout master
echo "test" >> README.md
git commit -am "test: Direct push"
git push origin master
# ❌ Debe fallar

# Intentar force push (debe fallar)
git push --force origin master
# ❌ Debe fallar

# Intentar eliminar branch (debe fallar)
git push origin --delete master
# ❌ Debe fallar
```

#### Test 3: Verificar Workflows

Ve a **Actions** y verifica que los workflows existen:
- ✅ CI
- ✅ CD - Continuous Deployment
- ✅ CodeQL Security Analysis
- ✅ Dependency Review
- ✅ PR Checks

---

## Troubleshooting

### Problema: Workflows no se ejecutan

**Solución**:
1. Verifica que Actions estén habilitadas
2. Verifica permisos de workflows
3. Revisa logs en Actions tab

### Problema: Status checks no aparecen en PR

**Solución**:
1. Los status checks solo aparecen después de ejecutarse al menos una vez
2. Crea un PR de prueba para que se ejecuten
3. Luego agrégalos a los required status checks

### Problema: No puedo hacer merge aunque todo está verde

**Solución**:
1. Verifica que todos los required status checks pasaron
2. Verifica que tienes approval requerido
3. Verifica que la branch está actualizada
4. Verifica que todas las conversaciones están resueltas

### Problema: CodeQL falla

**Solución**:
1. CodeQL puede tardar en la primera ejecución
2. Verifica que el código compila correctamente
3. Revisa logs de CodeQL en Actions

---

## Mantenimiento

### Actualizar Status Checks

Cuando agregues nuevos workflows:

1. **Settings** → **Rules** → **Rulesets** → **master-protection**
2. Edit → **Require status checks to pass**
3. Agregar nuevo status check
4. **Save changes**

### Revisar Dependabot Alerts

Semanalmente:
1. Ve a **Security** → **Dependabot alerts**
2. Revisa y actualiza dependencias vulnerables
3. Crea PRs para actualizaciones

### Revisar Code Scanning Alerts

Semanalmente:
1. Ve a **Security** → **Code scanning**
2. Revisa alertas de CodeQL
3. Corrige vulnerabilidades encontradas

---

## Referencias

- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [GitHub Rulesets](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-rulesets)
- [CodeQL](https://codeql.github.com/)
- [Dependabot](https://docs.github.com/en/code-security/dependabot)
- [CODEOWNERS](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/about-code-owners)

---

## Soporte

Si tienes problemas con la configuración:

1. Revisa la sección de Troubleshooting
2. Consulta la documentación de GitHub
3. Contacta al equipo de DevOps: @tradingapp/devops
