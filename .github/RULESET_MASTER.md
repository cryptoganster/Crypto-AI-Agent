# Configuración de Ruleset para Branch Master

Este documento describe cómo configurar el ruleset para la branch `master` en GitHub.

## Acceso a Configuración

1. Ve a tu repositorio en GitHub
2. Click en **Settings** → **Rules** → **Rulesets**
3. Click en **New ruleset** → **New branch ruleset**

## Configuración del Ruleset

### Información Básica

- **Ruleset Name**: `master-protection`
- **Enforcement status**: Active
- **Bypass list**: 
  - Repository admins (solo para emergencias)
  - CI/CD service accounts (si es necesario)

### Target Branches

- **Target**: Include by pattern
- **Pattern**: `master`

## Reglas a Configurar

### ✅ 1. Restrict creations
**Estado**: ❌ NO ACTIVAR

**Razón**: No es necesario para master, esta regla es más útil para patterns de branches.

---

### ✅ 2. Restrict updates
**Estado**: ❌ NO ACTIVAR

**Razón**: Las otras reglas ya protegen adecuadamente.

---

### ✅ 3. Restrict deletions
**Estado**: ✅ ACTIVAR

**Configuración**:
- Prevent deletion of matching refs

**Razón**: Previene eliminación accidental de la branch principal.

---

### ✅ 4. Require linear history
**Estado**: ✅ ACTIVAR

**Configuración**:
- Require linear history

**Razón**: Mantiene un historial limpio y fácil de seguir. Usa `rebase` o `squash merge`.

---

### ✅ 5. Require deployments to succeed
**Estado**: ✅ ACTIVAR (si tienes CI/CD)

**Configuración**:
- Required deployment environments: `staging`

**Razón**: Asegura que el código funciona en staging antes de merge a master.

---

### ✅ 6. Require signed commits
**Estado**: ✅ ACTIVAR (recomendado)

**Configuración**:
- Require signed commits

**Razón**: Añade capa de seguridad verificando identidad de commits.

**Setup para desarrolladores**:
```bash
# Configurar GPG key
git config --global user.signingkey YOUR_GPG_KEY_ID
git config --global commit.gpgsign true
```

---

### ✅ 7. Require a pull request before merging
**Estado**: ✅ ACTIVAR

**Configuración**:
- **Required approvals**: 1
- **Dismiss stale pull request approvals when new commits are pushed**: ✅
- **Require review from Code Owners**: ✅ (si tienes CODEOWNERS)
- **Require approval of the most recent reviewable push**: ✅
- **Require conversation resolution before merging**: ✅

**Razón**: Asegura revisión de código antes de merge.

---

### ✅ 8. Require status checks to pass
**Estado**: ✅ ACTIVAR

**Configuración**:
- **Require branches to be up to date before merging**: ✅

**Status checks requeridos**:
- ✅ `code-quality` - Code Quality checks (black, isort, flake8, mypy)
- ✅ `unit-tests` - Unit Tests
- ✅ `integration-tests` - Integration Tests
- ✅ `property-tests` - Property-Based Tests
- ✅ `security` - Security Scan
- ✅ `build` - Build Check
- ✅ `pr-title` - PR Title Check
- ✅ `dependency-review` - Dependency Review

**Razón**: Garantiza que el código pasa todos los tests y validaciones.

---

### ✅ 9. Block force pushes
**Estado**: ✅ ACTIVAR

**Configuración**:
- Block force pushes

**Razón**: Protege el historial de master de ser reescrito.

---

### ✅ 10. Require code scanning results
**Estado**: ✅ ACTIVAR (si usas GitHub Advanced Security)

**Configuración**:
- **Tools**: CodeQL
- **Security alerts**: High or higher
- **Required**: ✅

**Razón**: Detecta vulnerabilidades de seguridad automáticamente.

---

### ⚠️ 11. Require code quality results
**Estado**: ⚠️ OPCIONAL

**Configuración**:
- Depende de herramientas externas (SonarCloud, CodeClimate)

**Razón**: Útil si usas herramientas de análisis de calidad.

---

### ⚠️ 12. Automatically request Copilot code review
**Estado**: ⚠️ OPCIONAL

**Razón**: Útil para revisiones adicionales automáticas, pero no crítico.

---

## Configuración Paso a Paso en GitHub UI

### Paso 1: Crear Ruleset

```
Settings → Rules → Rulesets → New ruleset → New branch ruleset
```

### Paso 2: Configuración Básica

```
Name: master-protection
Enforcement status: Active
Target branches: Include by pattern → master
```

### Paso 3: Agregar Reglas

Marca las siguientes opciones:

#### Branch Protection Rules
- [x] Restrict deletions
- [x] Require linear history
- [x] Block force pushes

#### Pull Request Rules
- [x] Require a pull request before merging
  - Required approvals: 1
  - [x] Dismiss stale pull request approvals
  - [x] Require review from Code Owners
  - [x] Require approval of most recent push
  - [x] Require conversation resolution

#### Status Check Rules
- [x] Require status checks to pass before merging
  - [x] Require branches to be up to date
  - Add status checks:
    - code-quality
    - unit-tests
    - integration-tests
    - property-tests
    - security
    - build
    - pr-title
    - dependency-review

#### Commit Rules
- [x] Require signed commits

#### Deployment Rules (opcional)
- [x] Require deployments to succeed
  - Required environments: staging

#### Code Scanning Rules (si tienes GitHub Advanced Security)
- [x] Require code scanning results
  - Tool: CodeQL
  - Severity: High or higher

### Paso 4: Bypass List

Agregar bypass permissions para:
- Repository administrators (solo emergencias)

### Paso 5: Guardar

Click en **Create** para activar el ruleset.

---

## Verificación

Después de configurar, verifica que:

1. ✅ No puedes hacer push directo a master
2. ✅ Debes crear PR para hacer cambios
3. ✅ PR requiere 1 approval
4. ✅ Todos los status checks deben pasar
5. ✅ No puedes hacer force push
6. ✅ No puedes eliminar la branch

## Testing del Ruleset

### Test 1: Push Directo (debe fallar)
```bash
git checkout master
echo "test" >> README.md
git commit -am "test: Direct push"
git push origin master
# ❌ Debe fallar con: "required status checks"
```

### Test 2: PR sin Approval (debe fallar)
```bash
git checkout -b test/ruleset
echo "test" >> README.md
git commit -am "test: PR without approval"
git push origin test/ruleset
# Crear PR en GitHub
# ❌ Merge debe estar bloqueado hasta tener approval
```

### Test 3: PR con Tests Fallando (debe fallar)
```bash
# Crear PR con código que falla tests
# ❌ Merge debe estar bloqueado hasta que tests pasen
```

### Test 4: Force Push (debe fallar)
```bash
git checkout master
git reset --hard HEAD~1
git push --force origin master
# ❌ Debe fallar con: "force push blocked"
```

---

## Troubleshooting

### Problema: Status checks no aparecen

**Solución**: Los status checks solo aparecen después de que el workflow se ejecuta al menos una vez. Crea un PR de prueba para que se ejecuten.

### Problema: No puedo hacer merge aunque todo está verde

**Solución**: Verifica que:
1. Todos los status checks requeridos pasaron
2. Tienes al menos 1 approval
3. La branch está actualizada con master
4. Todas las conversaciones están resueltas

### Problema: Necesito hacer push de emergencia

**Solución**: 
1. Pide a un admin que temporalmente te agregue al bypass list
2. Haz el push necesario
3. Pide que te remuevan del bypass list
4. Crea un PR para documentar el cambio

---

## Mantenimiento

### Actualizar Status Checks

Cuando agregues nuevos workflows, actualiza la lista de status checks requeridos:

1. Settings → Rules → Rulesets → master-protection
2. Edit → Require status checks to pass
3. Agregar nuevo status check
4. Save changes

### Revisar Bypass List

Revisa periódicamente quién tiene bypass permissions:

1. Settings → Rules → Rulesets → master-protection
2. Revisar "Bypass list"
3. Remover usuarios que ya no necesitan bypass

---

## Referencias

- [GitHub Branch Protection Rules](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-protected-branches/about-protected-branches)
- [GitHub Rulesets](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-rulesets/about-rulesets)
- [Status Checks](https://docs.github.com/en/pull-requests/collaborating-with-pull-requests/collaborating-on-repositories-with-code-quality-features/about-status-checks)
