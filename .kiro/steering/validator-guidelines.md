# Guía de Validators en Application Layer

## Introducción

Esta guía documenta el patrón de validators en Application Layer, cómo crear nuevos validators, y la diferencia entre Application Layer validators y Domain Layer specifications.

## Filosofía de Validators

Los validators en Application Layer tienen una responsabilidad única: **validar comandos antes de que sean ejecutados por los handlers**.

### Principios Fundamentales

1. **Validación de Entrada**: Validators validan datos de entrada (comandos) antes de que lleguen a la lógica de negocio
2. **Excepciones Específicas**: Validators lanzan excepciones específicas cuando la validación falla
3. **Sin Lógica de Negocio**: Validators NO contienen lógica de negocio, solo validación de formato y estructura
4. **Independientes**: Cada validator es independiente y no hereda de clases base

## Patrón de Validators

### Estructura Básica

```python
"""Validator para [CommandName]."""

from typing import List
from .command import MyCommand
from .exception import MyValidationException


class MyCommandValidator:
    """
    Validator para MyCommand.
    
    Responsabilidad única: Validar comandos MyCommand antes de ejecución.
    """
    
    def __init__(self, logger: ILogger):
        """
        Inicializa validator.
        
        Args:
            logger: Logger para registrar validaciones
        """
        self._logger = logger
    
    def validate(self, command: MyCommand) -> None:
        """
        Valida comando.
        
        Args:
            command: Comando a validar
            
        Raises:
            MyValidationException: Si la validación falla
        """
        errors = []
        
        # Validar campos requeridos
        if not command.field:
            errors.append("field es requerido")
        
        # Validar formato
        if command.field and len(command.field) > 255:
            errors.append("field no puede exceder 255 caracteres")
        
        # Lanzar excepción si hay errores
        if errors:
            raise MyValidationException("; ".join(errors))
```

### Ubicación

Los validators viven junto al comando que validan:

```
src/app/commands/<feature>/<use-case>/
├── __init__.py
├── command.py          # Comando
├── handler.py          # Handler
├── validator.py        # ← Validator
├── exception.py        # Excepciones específicas
└── result.py           # Result Object
```

## Tipos de Validaciones

### 1. Validaciones de Formato

Validar que los datos tengan el formato correcto:

```python
def validate(self, command: CreateArticleCommand) -> None:
    errors = []
    
    # Validar que sea string no vacío
    if not command.title or not isinstance(command.title, str):
        errors.append("title es requerido y debe ser string")
    
    # Validar longitud
    if command.title and len(command.title) > 500:
        errors.append("title no puede exceder 500 caracteres")
    
    # Validar formato de URL
    if not command.url.startswith(('http://', 'https://')):
        errors.append("url debe comenzar con http:// o https://")
    
    if errors:
        raise CreateArticleValidationException("; ".join(errors))
```

### 2. Validaciones de Rango

Validar que los valores estén en rangos válidos:

```python
def validate(self, command: UpdateSourceCommand) -> None:
    errors = []
    
    # Validar rango numérico
    if command.priority is not None:
        if not isinstance(command.priority, int) or not (1 <= command.priority <= 10):
            errors.append("priority debe ser entero entre 1 y 10")
    
    # Validar rango de score
    if command.quality_threshold is not None:
        if not (0.0 <= command.quality_threshold <= 1.0):
            errors.append("quality_threshold debe estar entre 0.0 y 1.0")
    
    if errors:
        raise InvalidSourceUpdateError("; ".join(errors))
```

### 3. Validaciones de Estructura

Validar que estructuras complejas sean correctas:

```python
def _validate_source_config(self, config: dict) -> list[str]:
    """Valida configuración de source."""
    errors = []
    
    if not isinstance(config, dict):
        errors.append("source_config debe ser un diccionario")
        return errors
    
    # Validar campos conocidos
    valid_fields = {"fetch_enabled", "priority", "quality_threshold"}
    invalid_fields = set(config.keys()) - valid_fields
    
    if invalid_fields:
        errors.append(f"Campos no válidos: {', '.join(invalid_fields)}")
    
    # Validar tipos de campos
    if "fetch_enabled" in config:
        if not isinstance(config["fetch_enabled"], bool):
            errors.append("fetch_enabled debe ser boolean")
    
    return errors
```

### 4. Validaciones con Dependencias Externas

Validar contra repositorios o queries:

```python
class CreateSourceValidator:
    """Validator con dependencias externas."""
    
    def __init__(
        self,
        duplicate_sources_query: IFindDuplicateSources,
        logger: ILogger,
    ):
        self._duplicate_sources_query = duplicate_sources_query
        self._logger = logger
    
    async def validate_command(self, command: CreateSourceCommand) -> None:
        """Valida comando con verificación de duplicados."""
        errors = []
        
        # Validaciones básicas
        if not command.name:
            errors.append("name es requerido")
        
        if errors:
            raise CreateSourceValidationException("; ".join(errors))
        
        # Validación con dependencia externa
        await self._check_source_duplicates(command.source_url)
    
    async def _check_source_duplicates(self, source_url: str) -> None:
        """Verifica duplicados en repositorio."""
        duplicates = await self._duplicate_sources_query.find_by_url(source_url)
        
        if duplicates:
            existing = duplicates[0]
            raise DuplicateSourceException(
                source_url=source_url,
                existing_id=str(existing.get("id"))
            )
```

## Excepciones de Validators

### Estructura de Excepciones

Cada validator debe tener sus propias excepciones específicas:

```python
"""Excepciones para MyCommand."""


class MyCommandError(Exception):
    """Excepción base para errores de MyCommand."""
    pass


class MyValidationException(MyCommandError):
    """Excepción cuando la validación falla."""
    pass


class DuplicateResourceException(MyCommandError):
    """Excepción cuando se detecta recurso duplicado."""
    
    def __init__(self, resource_id: str, existing_id: str):
        self.resource_id = resource_id
        self.existing_id = existing_id
        super().__init__(
            f"Ya existe recurso con ID {resource_id} (existente: {existing_id})"
        )
```

### Jerarquía de Excepciones

```
Exception
└── MyCommandError (base)
    ├── MyValidationException (validación general)
    ├── DuplicateResourceException (duplicados)
    ├── InvalidConfigurationException (configuración)
    └── ResourceNotFoundException (no encontrado)
```

### Mensajes de Error

Los mensajes de error deben ser:

1. **Descriptivos**: Explicar qué está mal
2. **Accionables**: Indicar cómo corregir el error
3. **En Español**: Seguir convenciones del proyecto
4. **Concatenados**: Múltiples errores separados por "; "

```python
# ✅ CORRECTO - Descriptivo y accionable
errors.append("title no puede exceder 500 caracteres")
errors.append("url debe comenzar con http:// o https://")
errors.append("priority debe ser entero entre 1 y 10")

# ❌ INCORRECTO - Vago y no accionable
errors.append("invalid title")
errors.append("bad url")
errors.append("wrong priority")
```

## Uso en Handlers

Los handlers usan validators en el patrón try/except:

```python
class MyCommandHandler:
    """Handler para MyCommand."""
    
    def __init__(
        self,
        validator: MyCommandValidator,
        repository: IRepository,
        logger: ILogger,
    ):
        self._validator = validator
        self._repository = repository
        self._logger = logger
    
    async def handle(self, command: MyCommand) -> MyCommandResult:
        """Ejecuta comando."""
        
        # 1. Validar comando
        try:
            await self._validator.validate(command)
        except MyValidationException as e:
            self._logger.error("Validación fallida", error=str(e))
            return MyCommandResult.failure(str(e))
        
        # 2. Ejecutar lógica de negocio
        try:
            # ... lógica del handler
            return MyCommandResult.success(result)
        except Exception as e:
            self._logger.error("Error ejecutando comando", error=str(e))
            return MyCommandResult.failure(str(e))
```

## Validators vs Domain Specifications

### Application Layer Validators

**Ubicación**: `src/app/commands/*/validator.py`

**Propósito**: Validar comandos antes de ejecución

**Características**:
- Validan formato y estructura de comandos
- Lanzan excepciones específicas
- Pueden tener dependencias (repositories, queries)
- Validaciones técnicas y de entrada
- NO contienen lógica de negocio

**Ejemplo**:
```python
class CreateArticleValidator:
    """Valida CreateArticleCommand."""
    
    def validate(self, command: CreateArticleCommand) -> None:
        """Valida formato de comando."""
        errors = []
        
        if not command.title or len(command.title) > 500:
            errors.append("title inválido")
        
        if not command.url.startswith('http'):
            errors.append("url debe ser HTTP/HTTPS")
        
        if errors:
            raise CreateArticleValidationException("; ".join(errors))
```

### Domain Layer Specifications

**Ubicación**: `src/domain/specifications/`

**Propósito**: Validar reglas de negocio del dominio

**Características**:
- Validan invariantes de dominio
- Retornan ValidationResult (no lanzan excepciones)
- Sin dependencias externas (puras)
- Reutilizables en múltiples contextos
- Contienen lógica de negocio

**Ejemplo**:
```python
class ScoreRangeSpecification(Specification[float]):
    """Valida que score esté en rango [0.0, 1.0]."""
    
    def is_satisfied_by(self, score: float) -> ValidationResult:
        """Verifica que score esté en rango válido."""
        if not isinstance(score, (int, float)):
            return ValidationResult.failure(
                f"score debe ser numérico",
                "INVALID_TYPE"
            )
        
        if not (0.0 <= score <= 1.0):
            return ValidationResult.failure(
                f"score debe estar entre 0.0 y 1.0",
                "OUT_OF_RANGE"
            )
        
        return ValidationResult.success()
```

### Comparación

| Aspecto | Application Validator | Domain Specification |
|---------|----------------------|---------------------|
| **Ubicación** | `src/app/commands/*/validator.py` | `src/domain/specifications/` |
| **Propósito** | Validar comandos | Validar reglas de negocio |
| **Retorno** | Lanza excepciones | Retorna ValidationResult |
| **Dependencias** | Puede tener (repos, queries) | Sin dependencias (puro) |
| **Reutilización** | Específico del comando | Reutilizable en dominio |
| **Lógica** | Validación técnica | Lógica de negocio |
| **Testing** | Tests unitarios simples | Tests de propiedades |

### Cuándo Usar Cada Uno

**Usar Application Validator cuando**:
- ✅ Validar formato de entrada de comandos
- ✅ Verificar longitudes, rangos, tipos
- ✅ Validar contra repositorios (duplicados)
- ✅ Validación técnica de API/comandos

**Usar Domain Specification cuando**:
- ✅ Validar invariantes de dominio
- ✅ Reglas de negocio reutilizables
- ✅ Validaciones en Value Objects
- ✅ Validaciones en Aggregates

## Ejemplos Completos

### Ejemplo 1: Validator Simple

```python
"""Validator para DetectArticleLanguageCommand."""

from typing import List
from .command import DetectArticleLanguageCommand
from .exception import DetectArticleLanguageValidationException


class DetectArticleLanguageValidator:
    """
    Validator para DetectArticleLanguageCommand.
    
    Valida que los parámetros del comando sean correctos.
    """
    
    def validate(self, command: DetectArticleLanguageCommand) -> None:
        """
        Valida el comando.
        
        Args:
            command: Comando a validar
            
        Raises:
            DetectArticleLanguageValidationException: Si la validación falla
        """
        errors: List[str] = []
        
        # Validar article_id
        if not command.article_id:
            errors.append("article_id es requerido")
        
        # Validar correlation_id si se proporciona
        if command.correlation_id and len(command.correlation_id) > 100:
            errors.append("correlation_id demasiado largo (max 100 caracteres)")
        
        # Validar triggered_by
        if command.triggered_by and len(command.triggered_by) > 50:
            errors.append("triggered_by demasiado largo (max 50 caracteres)")
        
        if errors:
            raise DetectArticleLanguageValidationException("; ".join(errors))
```

### Ejemplo 2: Validator con Configuración Compleja

```python
"""Validator para UpdateSourceCommand."""

from typing import List
from .command import UpdateSourceCommand
from .exception import InvalidSourceUpdateError


class UpdateSourceValidator:
    """Validator para UpdateSourceCommand."""
    
    def validate(self, command: UpdateSourceCommand) -> None:
        """
        Valida comando UpdateSource.
        
        Args:
            command: Comando a validar
            
        Raises:
            InvalidSourceUpdateError: Si la validación falla
        """
        errors = []
        
        # Validar source_id
        if not command.source_id or not isinstance(command.source_id, str):
            errors.append("source_id es requerido y debe ser string válido")
        
        # Validar que al menos una actualización está especificada
        has_update = any([
            command.name,
            command.description,
            command.source_config,
        ])
        
        if not has_update:
            errors.append(
                "Debe especificar al menos un campo para actualizar"
            )
        
        # Validar name si se proporciona
        if command.name is not None:
            if not isinstance(command.name, str) or not command.name.strip():
                errors.append("name debe ser string no vacío")
            elif len(command.name.strip()) > 255:
                errors.append("name no puede exceder 255 caracteres")
        
        # Validar source_config si se proporciona
        if command.source_config is not None:
            config_errors = self._validate_source_config(command.source_config)
            errors.extend(config_errors)
        
        # Lanzar excepción si hay errores
        if errors:
            raise InvalidSourceUpdateError("; ".join(errors))
    
    def _validate_source_config(self, config: dict) -> list[str]:
        """
        Valida configuración de source.
        
        Args:
            config: Diccionario de configuración
            
        Returns:
            Lista de errores de validación
        """
        errors = []
        
        if not isinstance(config, dict):
            errors.append("source_config debe ser un diccionario")
            return errors
        
        # Validar campos conocidos
        valid_fields = {
            "fetch_enabled",
            "priority",
            "quality_threshold",
            "max_fetch_retries",
        }
        
        invalid_fields = set(config.keys()) - valid_fields
        if invalid_fields:
            errors.append(
                f"Campos no válidos: {', '.join(invalid_fields)}"
            )
        
        # Validar tipos y rangos
        if "fetch_enabled" in config:
            if not isinstance(config["fetch_enabled"], bool):
                errors.append("fetch_enabled debe ser boolean")
        
        if "priority" in config:
            if not isinstance(config["priority"], int) or not (
                1 <= config["priority"] <= 10
            ):
                errors.append("priority debe ser entero entre 1 y 10")
        
        if "quality_threshold" in config:
            if not isinstance(config["quality_threshold"], (int, float)) or not (
                0.0 <= config["quality_threshold"] <= 1.0
            ):
                errors.append("quality_threshold debe estar entre 0.0 y 1.0")
        
        return errors
```

### Ejemplo 3: Validator con Dependencias Externas

```python
"""Validator para CreateSourceCommand."""

from typing import List
from .command import CreateSourceCommand
from .exception import (
    CreateSourceValidationException,
    DuplicateSourceException,
)
from src.shared.kernel.logger import ILogger
from src.domain.interfaces.queries.sources.find_duplicate_sources import (
    IFindDuplicateSources,
)


class CreateSourceValidator:
    """
    Validator para CreateSourceCommand.
    
    Valida comandos CreateSource incluyendo verificación de duplicados.
    """
    
    def __init__(
        self,
        duplicate_sources_query: IFindDuplicateSources,
        logger: ILogger,
    ):
        self._duplicate_sources_query = duplicate_sources_query
        self._logger = logger
    
    async def validate_command(self, command: CreateSourceCommand) -> None:
        """
        Valida completamente un CreateSourceCommand.
        
        Args:
            command: Comando a validar
            
        Raises:
            CreateSourceValidationException: Si las validaciones fallan
            DuplicateSourceException: Si se detecta fuente duplicada
        """
        self._logger.info(
            "Iniciando validaciones para CreateSourceCommand",
            name=command.name,
            url=command.source_url,
        )
        
        # 1. Validaciones básicas
        validation_errors = []
        
        if not command.name or not command.name.strip():
            validation_errors.append("name es requerido")
        elif len(command.name) > 255:
            validation_errors.append("name no puede exceder 255 caracteres")
        
        if not command.source_url:
            validation_errors.append("source_url es requerido")
        elif not command.source_url.startswith(('http://', 'https://')):
            validation_errors.append("source_url debe comenzar con http:// o https://")
        
        # Validar parámetros de configuración
        try:
            self._validate_configuration_parameters(command)
        except ValueError as e:
            validation_errors.append(str(e))
        
        if validation_errors:
            self._logger.error(
                "Errores de validación",
                errors=validation_errors,
            )
            raise CreateSourceValidationException(
                f"Errores de validación: {'; '.join(validation_errors)}"
            )
        
        # 2. Verificar duplicados en repositorio
        await self._check_source_duplicates(command.source_url)
        
        self._logger.info("Validaciones completadas exitosamente")
    
    def _validate_configuration_parameters(
        self, 
        command: CreateSourceCommand
    ) -> None:
        """Valida parámetros de configuración."""
        if command.fetch_interval_minutes is not None:
            if command.fetch_interval_minutes <= 0:
                raise ValueError("fetch_interval_minutes debe ser mayor a 0")
            if command.fetch_interval_minutes > 1440:
                raise ValueError(
                    "fetch_interval_minutes no puede exceder 1440 (24 horas)"
                )
        
        if command.max_articles_per_fetch is not None:
            if command.max_articles_per_fetch <= 0:
                raise ValueError("max_articles_per_fetch debe ser mayor a 0")
            if command.max_articles_per_fetch > 1000:
                raise ValueError("max_articles_per_fetch no puede exceder 1000")
    
    async def _check_source_duplicates(self, source_url: str) -> None:
        """Verifica duplicados usando query interface."""
        duplicates = await self._duplicate_sources_query.find_by_url(source_url)
        
        if duplicates:
            existing_source = duplicates[0]
            self._logger.error(
                "Source duplicado detectado",
                url=source_url,
                existing_id=str(existing_source.get("id")),
            )
            raise DuplicateSourceException(
                source_url=source_url,
                existing_id=str(existing_source.get("id")),
            )
```

## Testing de Validators

### Tests Unitarios

```python
"""Tests para MyCommandValidator."""

import pytest
from src.app.commands.my_feature.my_command.validator import MyCommandValidator
from src.app.commands.my_feature.my_command.command import MyCommand
from src.app.commands.my_feature.my_command.exception import (
    MyValidationException,
)


class TestMyCommandValidator:
    """Tests para MyCommandValidator."""
    
    def test_validate_with_valid_command_succeeds(self):
        """Debería validar comando válido sin lanzar excepción."""
        # Arrange
        validator = MyCommandValidator()
        command = MyCommand(
            field="valid value",
            other_field=123,
        )
        
        # Act & Assert - No debe lanzar excepción
        validator.validate(command)
    
    def test_validate_with_missing_required_field_raises_exception(self):
        """Debería lanzar excepción cuando falta campo requerido."""
        # Arrange
        validator = MyCommandValidator()
        command = MyCommand(field=None)
        
        # Act & Assert
        with pytest.raises(MyValidationException) as exc_info:
            validator.validate(command)
        
        assert "field es requerido" in str(exc_info.value)
    
    def test_validate_with_field_too_long_raises_exception(self):
        """Debería lanzar excepción cuando campo excede longitud."""
        # Arrange
        validator = MyCommandValidator()
        command = MyCommand(field="x" * 256)
        
        # Act & Assert
        with pytest.raises(MyValidationException) as exc_info:
            validator.validate(command)
        
        assert "no puede exceder 255 caracteres" in str(exc_info.value)
    
    def test_validate_with_multiple_errors_concatenates_messages(self):
        """Debería concatenar múltiples errores en mensaje."""
        # Arrange
        validator = MyCommandValidator()
        command = MyCommand(field=None, other_field=-1)
        
        # Act & Assert
        with pytest.raises(MyValidationException) as exc_info:
            validator.validate(command)
        
        error_message = str(exc_info.value)
        assert "field es requerido" in error_message
        assert "other_field debe ser positivo" in error_message
        assert ";" in error_message  # Separador
```

### Tests con Dependencias

```python
"""Tests para CreateSourceValidator."""

import pytest
from unittest.mock import AsyncMock, Mock
from src.app.commands.sources.create_source.validator import (
    CreateSourceValidator,
)
from src.app.commands.sources.create_source.command import (
    CreateSourceCommand,
)
from src.app.commands.sources.create_source.exception import (
    DuplicateSourceException,
)


class TestCreateSourceValidator:
    """Tests para CreateSourceValidator."""
    
    @pytest.fixture
    def mock_duplicate_query(self):
        """Mock para query de duplicados."""
        return AsyncMock()
    
    @pytest.fixture
    def mock_logger(self):
        """Mock para logger."""
        return Mock()
    
    @pytest.fixture
    def validator(self, mock_duplicate_query, mock_logger):
        """Validator con dependencias mockeadas."""
        return CreateSourceValidator(
            duplicate_sources_query=mock_duplicate_query,
            logger=mock_logger,
        )
    
    async def test_validate_with_duplicate_url_raises_exception(
        self,
        validator,
        mock_duplicate_query,
    ):
        """Debería lanzar excepción cuando URL está duplicada."""
        # Arrange
        command = CreateSourceCommand(
            name="Test Source",
            source_url="https://example.com/feed",
        )
        
        # Mock retorna duplicado
        mock_duplicate_query.find_by_url.return_value = [
            {"id": "existing-123", "name": "Existing Source"}
        ]
        
        # Act & Assert
        with pytest.raises(DuplicateSourceException) as exc_info:
            await validator.validate_command(command)
        
        assert "existing-123" in str(exc_info.value)
        mock_duplicate_query.find_by_url.assert_called_once_with(
            "https://example.com/feed"
        )
```

## Checklist para Crear Nuevo Validator

- [ ] 1. Crear archivo `validator.py` en directorio del comando
- [ ] 2. Crear clase `[CommandName]Validator`
- [ ] 3. Implementar método `validate(command)` que lanza excepciones
- [ ] 4. Crear archivo `exception.py` con excepciones específicas
- [ ] 5. Validar campos requeridos
- [ ] 6. Validar formatos y rangos
- [ ] 7. Validar estructuras complejas (si aplica)
- [ ] 8. Agregar validaciones con dependencias externas (si aplica)
- [ ] 9. Agregar logging apropiado
- [ ] 10. Crear tests unitarios del validator
- [ ] 11. Verificar que handler usa validator correctamente
- [ ] 12. Documentar excepciones en docstrings

## Anti-Patrones a Evitar

### ❌ Anti-Patrón 1: Heredar de BaseValidator

```python
# ❌ INCORRECTO - No heredar de clase base
class MyValidator(BaseValidator):
    def validate(self, command):
        result = ValidationResult()
        # ...
        return result
```

**Problema**: Crea acoplamiento innecesario y viola YAGNI.

**Solución**: Validators independientes sin herencia.

### ❌ Anti-Patrón 2: Retornar ValidationResult

```python
# ❌ INCORRECTO - No retornar ValidationResult
def validate(self, command) -> ValidationResult:
    if not command.field:
        return ValidationResult.failure("field requerido")
    return ValidationResult.success()
```

**Problema**: Inconsistente con el patrón de excepciones del proyecto.

**Solución**: Lanzar excepciones específicas.

### ❌ Anti-Patrón 3: Lógica de Negocio en Validator

```python
# ❌ INCORRECTO - No incluir lógica de negocio
def validate(self, command):
    # Calcular quality score (lógica de negocio)
    quality = self._calculate_quality(command.content)
    if quality < 0.5:
        raise ValidationException("quality too low")
```

**Problema**: Validators solo validan formato, no ejecutan lógica de negocio.

**Solución**: Mover lógica de negocio al handler o domain service.

### ❌ Anti-Patrón 4: Validators Genéricos

```python
# ❌ INCORRECTO - No crear validators genéricos
class GenericValidator:
    def validate(self, command: Any) -> None:
        # Validación genérica
        pass
```

**Problema**: Validators deben ser específicos para cada comando.

**Solución**: Un validator por comando.

## Resumen

- 🎯 Validators validan comandos antes de ejecución
- 🚫 NO heredan de BaseValidator
- ⚡ Lanzan excepciones específicas cuando fallan
- 📝 Mensajes de error descriptivos y accionables
- 🔍 Validaciones de formato, rango y estructura
- 🏗️ Pueden tener dependencias (repos, queries)
- ✅ Tests unitarios simples con pytest.raises
- 🔄 Diferentes de Domain Specifications (reglas de negocio)

## Referencias

- **Requirements**: `.kiro/specs/remove-base-validator/requirements.md`
- **Design**: `.kiro/specs/remove-base-validator/design.md`
- **Architecture**: `.kiro/steering/architecture.md`
- **Domain Patterns**: `.kiro/steering/domain-patterns.md`
- **Testing Guidelines**: `.kiro/steering/testing-guidelines.md`
