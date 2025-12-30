# Patrón de Mappers por Caso de Uso

## Filosofía

En este proyecto, seguimos el principio de **"Mapper por Caso de Uso"** en lugar de mappers centralizados. Cada comando o query que necesite serializar agregados de dominio tiene su propio mapper local.

## ¿Por qué Mappers Locales?

### Problemas de Mappers Centralizados

❌ **Baja cohesión**: Mapper separado del caso de uso que lo usa
❌ **Alto acoplamiento**: Múltiples casos de uso dependen del mismo mapper
❌ **Violación de SRP**: Un mapper con múltiples responsabilidades
❌ **Difícil de mantener**: Cambios afectan múltiples casos de uso
❌ **Violación de Clean Architecture**: Application Layer haciendo serialización

### Ventajas de Mappers Locales

✅ **Alta cohesión**: Mapper vive junto al caso de uso
✅ **Bajo acoplamiento**: Cada caso de uso es independiente
✅ **Single Responsibility**: Un mapper, una responsabilidad
✅ **Fácil de testear**: Tests aislados y enfocados
✅ **Fácil de mantener**: Cambios localizados
✅ **Clean Architecture**: Separación clara de responsabilidades

## Estructura de Directorios

```
src/app/commands/<feature>/<use-case>/
├── __init__.py
├── command.py          # Comando (input)
├── handler.py          # Handler (lógica del caso de uso)
├── mapper.py           # ← Mapper específico del caso de uso
├── result.py           # Result Object (output)
├── validator.py        # Validador (opcional)
└── exception.py        # Excepciones (opcional)

tests/unit/app/commands/<feature>/<use-case>/
├── test_handler.py
├── test_mapper.py      # ← Tests del mapper
└── test_validator.py
```

## Plantilla de Mapper

```python
"""Mapper para [UseCase] command."""

from typing import Dict, Any, List
from src.domain.aggregates.[aggregate] import [Aggregate]


class [UseCase]Mapper:
    """
    Mapper específico para [UseCase] command.
    
    Serializa [Aggregate] aggregates a DTOs para [UseCase]Result.
    
    Responsabilidades:
    - Serializar [Aggregate] a DTO
    - Convertir Value Objects a primitivos
    - NO contiene lógica de negocio
    """
    
    @staticmethod
    def [aggregate]_to_dto(aggregate: [Aggregate]) -> Dict[str, Any]:
        """
        Serializa [Aggregate] a DTO.
        
        Usado para [descripción del uso].
        
        Args:
            aggregate: [Aggregate] aggregate del dominio
            
        Returns:
            Dict con datos del [aggregate]
            
        Example:
            >>> aggregate = [Aggregate](id="123", ...)
            >>> dto = [UseCase]Mapper.[aggregate]_to_dto(aggregate)
            >>> dto["id"]
            '123'
        """
        return {
            "id": str(aggregate.id),
            "field": aggregate.field,
            # Convertir Value Objects a primitivos
            "status": str(aggregate.status),
            "created_at": aggregate.created_at.isoformat(),
        }
    
    @staticmethod
    def [aggregates]_to_dto_list(aggregates: List[[Aggregate]]) -> List[Dict[str, Any]]:
        """
        Serializa lista de [Aggregate] a lista de DTOs.
        
        Args:
            aggregates: Lista de [Aggregate] aggregates
            
        Returns:
            Lista de DTOs
        """
        return [
            [UseCase]Mapper.[aggregate]_to_dto(aggregate)
            for aggregate in aggregates
        ]
```

## Plantilla de Tests

```python
"""Tests para [UseCase]Mapper."""

import pytest
from datetime import datetime, timezone
from unittest.mock import Mock

from src.app.commands.[feature].[use_case].mapper import [UseCase]Mapper
from src.domain.aggregates.[aggregate] import [Aggregate]


class Test[UseCase]Mapper:
    """Tests para [UseCase]Mapper."""
    
    def test_[aggregate]_to_dto_serializes_correctly(self):
        """Debería serializar [Aggregate] a DTO correctamente."""
        # Arrange
        aggregate = [Aggregate](
            id="test-123",
            field="value",
            created_at=datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        )
        
        # Act
        dto = [UseCase]Mapper.[aggregate]_to_dto(aggregate)
        
        # Assert
        assert dto["id"] == "test-123"
        assert dto["field"] == "value"
        assert dto["created_at"] == "2024-01-01T12:00:00+00:00"
    
    def test_[aggregate]_to_dto_handles_none_values(self):
        """Debería manejar valores None correctamente."""
        # Arrange
        aggregate = [Aggregate](
            id="test-456",
            optional_field=None
        )
        
        # Act
        dto = [UseCase]Mapper.[aggregate]_to_dto(aggregate)
        
        # Assert
        assert dto["optional_field"] is None
    
    def test_[aggregate]_to_dto_converts_value_objects_to_primitives(self):
        """Debería convertir Value Objects a primitivos."""
        # Arrange
        aggregate = [Aggregate](
            id="test-789",
            status=Status.ACTIVE  # Value Object
        )
        
        # Act
        dto = [UseCase]Mapper.[aggregate]_to_dto(aggregate)
        
        # Assert
        assert isinstance(dto["status"], str)
        assert dto["status"] == "active"
    
    def test_[aggregate]_to_dto_includes_all_required_fields(self):
        """Debería incluir todos los campos requeridos."""
        # Arrange
        aggregate = [Aggregate](id="test-complete")
        
        # Act
        dto = [UseCase]Mapper.[aggregate]_to_dto(aggregate)
        
        # Assert
        required_fields = ["id", "field", "status", "created_at"]
        for field in required_fields:
            assert field in dto, f"Campo requerido '{field}' faltante"
    
    def test_[aggregate]_to_dto_is_static_method(self):
        """Debería ser un método estático (no requiere instancia)."""
        # Arrange
        aggregate = [Aggregate](id="test-static")
        
        # Act - Llamar sin instanciar la clase
        dto = [UseCase]Mapper.[aggregate]_to_dto(aggregate)
        
        # Assert
        assert dto is not None
        assert dto["id"] == "test-static"
    
    def test_[aggregates]_to_dto_list_serializes_multiple(self):
        """Debería serializar múltiples [Aggregate] correctamente."""
        # Arrange
        aggregates = [
            [Aggregate](id="test-1"),
            [Aggregate](id="test-2"),
            [Aggregate](id="test-3"),
        ]
        
        # Act
        dtos = [UseCase]Mapper.[aggregates]_to_dto_list(aggregates)
        
        # Assert
        assert len(dtos) == 3
        assert dtos[0]["id"] == "test-1"
        assert dtos[1]["id"] == "test-2"
        assert dtos[2]["id"] == "test-3"
    
    def test_[aggregates]_to_dto_list_handles_empty_list(self):
        """Debería manejar lista vacía correctamente."""
        # Arrange
        aggregates = []
        
        # Act
        dtos = [UseCase]Mapper.[aggregates]_to_dto_list(aggregates)
        
        # Assert
        assert dtos == []
        assert isinstance(dtos, list)
```

## Checklist de Implementación

### 1. Crear Mapper

- [ ] Crear archivo `mapper.py` en el directorio del caso de uso
- [ ] Implementar clase `[UseCase]Mapper`
- [ ] Implementar métodos de serialización necesarios
- [ ] Agregar docstrings completos
- [ ] Agregar type hints completos
- [ ] Agregar ejemplos en docstrings

### 2. Actualizar Handler

- [ ] Importar mapper local: `from .mapper import [UseCase]Mapper`
- [ ] Remover imports de mappers centralizados
- [ ] Actualizar llamadas a mapper: `[UseCase]Mapper.method()`
- [ ] Verificar que no quedan referencias a mappers antiguos

### 3. Crear Tests

- [ ] Crear archivo `test_[use_case]_mapper.py`
- [ ] Implementar test de serialización correcta
- [ ] Implementar test de manejo de None
- [ ] Implementar test de conversión a primitivos
- [ ] Implementar test de campos requeridos
- [ ] Implementar test de método estático
- [ ] Implementar tests de listas (si aplica)
- [ ] Ejecutar tests: `pytest tests/unit/app/commands/.../test_mapper.py -v`

### 4. Verificar

- [ ] Todos los tests pasan
- [ ] Cobertura del mapper > 90%
- [ ] No hay imports de mappers centralizados
- [ ] Handler usa mapper local correctamente
- [ ] Documentación completa

## Ejemplos Reales del Proyecto

### UpdateSourceMapper

```python
class UpdateSourceMapper:
    """Mapper específico para UpdateSource command."""
    
    @staticmethod
    def source_to_summary(source: Source) -> Dict[str, Any]:
        """Serializa Source a DTO resumido."""
        return {
            "id": str(source.id),
            "name": str(source.name),
            "url": str(source.url),
            "description": str(source.description) if source.description else None,
            "status": str(source.status),
            "is_active": source.is_active,
            "success_rate": source.metrics.success_rate if source.metrics else 0.0,
            "updated_at": source.updated_at.isoformat(),
        }
```

### FetchFromSourcesMapper

```python
class FetchFromSourcesMapper:
    """Mapper específico para FetchFromSources command."""
    
    @staticmethod
    def source_to_dto(source: Source) -> Dict[str, Any]:
        """Serializa Source a DTO."""
        return {
            "id": str(source.id),
            "name": str(source.name),
            "url": str(source.url),
            "status": str(source.status),
        }
    
    @staticmethod
    def sources_to_dto_list(sources: List[Source]) -> List[Dict[str, Any]]:
        """Serializa lista de Sources a lista de DTOs."""
        return [
            FetchFromSourcesMapper.source_to_dto(source)
            for source in sources
        ]
    
    @staticmethod
    def fetch_session_to_dto(session: FetchSession) -> Dict[str, Any]:
        """Serializa FetchSession a DTO."""
        return {
            "session_id": str(session.id),
            "source_id": str(session.source_id),
            "status": session.fetch_state.phase.value,
            "started_at": session.started_at.isoformat(),
        }
```

## Preguntas Frecuentes

### ¿Cuándo NO crear un mapper?

No crear mapper cuando:
- El caso de uso no serializa agregados
- Solo se pasan agregados sin transformar
- La conversión es trivial (un solo campo)
- El caso de uso no retorna datos

### ¿Puedo compartir un mapper entre casos de uso?

**No**. Cada caso de uso debe tener su propio mapper, incluso si la serialización es similar. Esto mantiene la independencia y facilita cambios futuros.

### ¿Dónde va la lógica de negocio?

La lógica de negocio va en:
- **Aggregates**: Lógica de dominio
- **Domain Services**: Lógica que involucra múltiples aggregates
- **Handlers**: Orquestación del caso de uso

Los mappers **NO** deben contener lógica de negocio, solo transformación de datos.

### ¿Qué pasa con los mappers de Infrastructure?

Los mappers de Infrastructure (entre ORM y Domain) son diferentes:
- **Ubicación**: `src/infra/persistence/mappers/`
- **Propósito**: Convertir entre modelos ORM y agregados de dominio
- **Patrón**: Pueden ser compartidos porque son técnicos, no de negocio

### ¿Cómo manejo mappers complejos?

Si un mapper se vuelve complejo:
1. Dividir en múltiples métodos privados
2. Considerar si hay lógica de negocio que debería estar en el dominio
3. Usar métodos helper para conversiones comunes
4. Mantener cada método enfocado en una sola transformación

## Referencias

- **Clean Architecture**: Robert C. Martin
- **Domain-Driven Design**: Eric Evans
- **Single Responsibility Principle**: SOLID principles
- **High Cohesion, Low Coupling**: Principios de diseño de software
