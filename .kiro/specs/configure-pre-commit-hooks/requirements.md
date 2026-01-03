# Requirements Document: Configure Pre-Commit Hooks

## Introduction

Este documento define los requisitos para configurar pre-commit hooks en el proyecto, asegurando calidad de código consistente antes de cada commit.

## Glossary

- **Pre-commit**: Framework para gestionar y mantener hooks de git multi-lenguaje
- **Hook**: Script que se ejecuta automáticamente en eventos específicos de git
- **Linter**: Herramienta que analiza código para detectar errores y problemas de estilo
- **Formatter**: Herramienta que formatea código automáticamente según reglas definidas
- **Type Checker**: Herramienta que verifica tipos estáticos en Python

## Requirements

### Requirement 1: Configuración Base de Pre-commit

**User Story:** Como desarrollador, quiero que pre-commit esté configurado correctamente, para que los hooks se ejecuten automáticamente antes de cada commit.

#### Acceptance Criteria

1. THE System SHALL tener un archivo `.pre-commit-config.yaml` en la raíz del proyecto
2. WHEN un desarrollador instala pre-commit THEN el sistema SHALL configurar los hooks automáticamente
3. THE System SHALL incluir pre-commit en las dependencias de desarrollo
4. THE System SHALL documentar el proceso de instalación en README.md

### Requirement 2: Formateo de Código con Black

**User Story:** Como desarrollador, quiero que el código Python se formatee automáticamente con Black, para mantener un estilo consistente.

#### Acceptance Criteria

1. THE System SHALL ejecutar Black antes de cada commit
2. THE System SHALL usar la configuración de Black definida en `pyproject.toml`
3. WHEN Black detecta código sin formatear THEN el sistema SHALL formatear automáticamente y fallar el commit
4. THE System SHALL aplicar Black a todos los archivos Python (*.py)

### Requirement 3: Ordenamiento de Imports con isort

**User Story:** Como desarrollador, quiero que los imports se ordenen automáticamente, para mantener consistencia en el código.

#### Acceptance Criteria

1. THE System SHALL ejecutar isort antes de cada commit
2. THE System SHALL usar el perfil "black" para compatibilidad
3. WHEN isort detecta imports desordenados THEN el sistema SHALL ordenarlos automáticamente
4. THE System SHALL aplicar isort a todos los archivos Python

### Requirement 4: Linting con Flake8

**User Story:** Como desarrollador, quiero que se detecten problemas de código automáticamente, para mantener calidad del código.

#### Acceptance Criteria

1. THE System SHALL ejecutar Flake8 antes de cada commit
2. THE System SHALL usar configuración compatible con Black (line-length=88)
3. WHEN Flake8 detecta errores THEN el sistema SHALL fallar el commit con mensaje descriptivo
4. THE System SHALL ignorar errores específicos compatibles con Black (E203, W503)

### Requirement 5: Type Checking con MyPy

**User Story:** Como desarrollador, quiero que se verifiquen los tipos estáticos, para detectar errores de tipos antes del commit.

#### Acceptance Criteria

1. THE System SHALL ejecutar MyPy antes de cada commit
2. THE System SHALL usar la configuración de MyPy definida en `pyproject.toml`
3. WHEN MyPy detecta errores de tipos THEN el sistema SHALL fallar el commit
4. THE System SHALL aplicar MyPy solo a archivos modificados para velocidad

### Requirement 6: Validaciones Generales de Git

**User Story:** Como desarrollador, quiero validaciones básicas de git, para evitar commits problemáticos.

#### Acceptance Criteria

1. THE System SHALL verificar que no haya archivos grandes (>500KB) en el commit
2. THE System SHALL verificar que no haya conflictos de merge sin resolver
3. THE System SHALL verificar que los archivos YAML sean válidos
4. THE System SHALL verificar que los archivos JSON sean válidos
5. THE System SHALL remover espacios en blanco al final de líneas

### Requirement 7: Validaciones de Seguridad

**User Story:** Como desarrollador, quiero detectar secretos y credenciales accidentales, para evitar fugas de seguridad.

#### Acceptance Criteria

1. THE System SHALL detectar claves privadas en el código
2. THE System SHALL detectar tokens y credenciales hardcodeadas
3. WHEN se detectan secretos THEN el sistema SHALL fallar el commit con advertencia
4. THE System SHALL permitir excepciones mediante comentarios especiales

### Requirement 8: Performance y Usabilidad

**User Story:** Como desarrollador, quiero que los hooks sean rápidos, para no interrumpir mi flujo de trabajo.

#### Acceptance Criteria

1. THE System SHALL ejecutar hooks solo en archivos modificados (staged)
2. THE System SHALL cachear dependencias de hooks para velocidad
3. WHEN todos los hooks pasan THEN el commit SHALL completarse en menos de 10 segundos
4. THE System SHALL mostrar progreso claro durante ejecución de hooks

### Requirement 9: Bypass de Hooks

**User Story:** Como desarrollador, quiero poder saltarme hooks en casos especiales, para commits urgentes o WIP.

#### Acceptance Criteria

1. THE System SHALL permitir bypass con flag `--no-verify`
2. THE System SHALL documentar cuándo es apropiado usar bypass
3. THE System SHALL loggear cuando se usa bypass
4. THE System SHALL recomendar ejecutar hooks manualmente después de bypass

### Requirement 10: Integración con CI/CD

**User Story:** Como equipo, queremos que los mismos checks se ejecuten en CI, para consistencia entre local y remoto.

#### Acceptance Criteria

1. THE System SHALL tener un comando para ejecutar todos los hooks manualmente
2. THE System SHALL documentar cómo ejecutar hooks en CI/CD
3. THE System SHALL usar las mismas versiones de herramientas en local y CI
4. THE System SHALL fallar el build de CI si los hooks fallan

### Requirement 11: Documentación

**User Story:** Como nuevo desarrollador, quiero documentación clara sobre pre-commit, para configurar mi entorno rápidamente.

#### Acceptance Criteria

1. THE System SHALL documentar instalación de pre-commit en README.md
2. THE System SHALL documentar qué hace cada hook
3. THE System SHALL documentar cómo resolver errores comunes
4. THE System SHALL documentar cómo agregar nuevos hooks
5. THE System SHALL incluir ejemplos de uso

### Requirement 12: Hooks Específicos de Python

**User Story:** Como desarrollador Python, quiero validaciones específicas del lenguaje, para mantener mejores prácticas.

#### Acceptance Criteria

1. THE System SHALL verificar que los archivos Python tengan encoding UTF-8
2. THE System SHALL verificar que no haya imports de `__future__` obsoletos
3. THE System SHALL verificar que los docstrings sigan formato Google
4. THE System SHALL verificar que no haya `print()` statements en código de producción

## Out of Scope

- Hooks para otros lenguajes (JavaScript, TypeScript, etc.)
- Hooks de post-commit o post-merge
- Integración con IDEs específicos
- Configuración de git hooks del lado del servidor
- Análisis de complejidad ciclomática
- Cobertura de tests en pre-commit (demasiado lento)

## Success Criteria

1. ✅ Archivo `.pre-commit-config.yaml` creado y funcional
2. ✅ Todos los hooks configurados ejecutan correctamente
3. ✅ Documentación completa en README.md
4. ✅ Pre-commit instalado en dependencias de desarrollo
5. ✅ Tiempo de ejecución de hooks < 10 segundos para commits típicos
6. ✅ Cero falsos positivos en hooks
7. ✅ Equipo puede instalar y usar pre-commit sin problemas

## Dependencies

- Python 3.11+
- Git 2.x
- Herramientas ya configuradas en pyproject.toml:
  - black>=23.11.0
  - isort>=5.12.0
  - flake8>=6.1.0
  - mypy>=1.7.1

## Notes

- Pre-commit ya está parcialmente instalado pero falta el archivo de configuración
- Las herramientas de linting/formatting ya están configuradas en `pyproject.toml`
- El proyecto sigue Clean Architecture y DDD, los hooks deben respetar esta estructura
- Los hooks deben ser rápidos para no interrumpir el flujo de desarrollo
