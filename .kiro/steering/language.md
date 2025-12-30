---
inclusion: always
---

# Convenciones de Idioma

Este proyecto utiliza una combinación estratégica de español e inglés para mantener consistencia con estándares internacionales de desarrollo mientras preserva la comunicación efectiva en español para el equipo.

## Reglas de Idioma por Contexto

### Código Fuente
**Idioma: Inglés**

- Nombres de variables, funciones, clases, métodos
- Nombres de archivos y carpetas
- Nombres de tipos, interfaces, protocolos
- Constantes y enums

```python
# ✅ CORRECTO
class ArticleRepository:
    def find_by_id(self, article_id: str) -> Optional[Article]:
        pass

# ❌ INCORRECTO
class RepositorioArticulo:
    def buscar_por_id(self, id_articulo: str) -> Optional[Article]:
        pass
```

### Comentarios y Docstrings
**Idioma: Español**

- Docstrings de funciones, clases y módulos
- Comentarios inline
- TODOs, FIXMEs, NOTEs

```python
# ✅ CORRECTO
def calculate_quality_score(article: Article) -> float:
    """Calcula el puntaje de calidad de un artículo.
    
    Args:
        article: El artículo a evaluar
        
    Returns:
        Puntaje de calidad entre 0.0 y 1.0
        
    Raises:
        ValueError: Si el artículo no tiene contenido
    """
    # Validar que el artículo tenga contenido
    if not article.content:
        raise ValueError("El artículo debe tener contenido")
    
    # TODO: Agregar análisis de sentimiento
    return self._analyze_content(article.content)
```

### Mensajes de Error y Logs
**Idioma: Español**

- Mensajes de excepciones
- Logs (info, warning, error, debug)
- Mensajes de validación

```python
# ✅ CORRECTO
logger.info("Iniciando scraping de fuente RSS", source_id=source.id)
logger.error("Error al conectar con la base de datos", error=str(e))

raise ValidationError("La URL del feed RSS es inválida")
raise ArticleNotFoundException(f"Artículo {article_id} no encontrado")
```

### Nombres de Excepciones
**Idioma: Inglés** (siguiendo convenciones estándar)

```python
# ✅ CORRECTO
class ValidationError(DomainException):
    """Excepción para errores de validación."""
    pass

class ArticleNotFoundException(DomainException):
    """Excepción cuando no se encuentra un artículo."""
    pass
```

### Documentación
**Idioma: Español**

- README.md
- Archivos en `/docs`
- Archivos de steering (`.kiro/steering/`)
- Especificaciones (`.kiro/specs/`)
- Guías de arquitectura

### Commits
**Idioma: Español**

Usar Conventional Commits en español:

```bash
# Tipos permitidos
feat(articles): agregar filtro por calidad
fix(rss): corregir parsing de fechas en feeds
docs(readme): actualizar instrucciones de instalación
refactor(domain): simplificar lógica de deduplicación
test(repositories): agregar tests para ArticleRepository
chore(deps): actualizar dependencias de SQLAlchemy
```

### Tests
**Idioma: Español** (descripciones)

```python
# ✅ CORRECTO
class TestArticleRepository:
    """Tests para el repositorio de artículos."""
    
    async def test_save_article_success(self):
        """Debería guardar un artículo correctamente."""
        pass
    
    async def test_find_by_id_returns_none_when_not_found(self):
        """Debería retornar None cuando el artículo no existe."""
        pass
```

### Variables de Entorno
**Idioma: Inglés** (UPPER_SNAKE_CASE)

```bash
# ✅ CORRECTO
DATABASE_URL=postgresql://localhost:5432/rss_scraper
RSS_FETCH_TIMEOUT=30
MAX_ARTICLES_PER_SOURCE=100
```

### Respuestas de API
**Idioma: Español** (mensajes para usuarios)

```python
# ✅ CORRECTO
return ErrorResponse(
    error="validation_error",
    message="Los datos proporcionados son inválidos",
    details={"url": "La URL del feed RSS no es válida"}
)
```

## Resumen Rápido

| Contexto | Idioma | Ejemplo |
|----------|--------|---------|
| Nombres en código | 🇬🇧 Inglés | `ArticleRepository`, `fetch_articles()` |
| Comentarios/Docstrings | 🇪🇸 Español | `"""Calcula la calidad del artículo"""` |
| Logs y errores | 🇪🇸 Español | `logger.info("Artículo procesado")` |
| Clases de excepción | 🇬🇧 Inglés | `ValidationError`, `NotFoundException` |
| Mensajes de excepción | 🇪🇸 Español | `"El artículo no fue encontrado"` |
| Documentación | 🇪🇸 Español | `README.md`, archivos en `/docs` |
| Commits | 🇪🇸 Español | `feat(rss): agregar soporte para Atom` |
| Tests (descripciones) | 🇪🇸 Español | `"debería crear un artículo válido"` |
| Variables de entorno | 🇬🇧 Inglés | `DATABASE_URL`, `API_KEY` |

## Justificación

Esta convención permite:

1. **Compatibilidad internacional**: Código en inglés facilita colaboración global
2. **Comunicación clara**: Documentación y mensajes en español para el equipo
3. **Estándares de la industria**: Seguir convenciones establecidas
4. **Mantenibilidad**: Consistencia en todo el proyecto
5. **Onboarding eficiente**: Reglas claras para nuevos desarrolladores
