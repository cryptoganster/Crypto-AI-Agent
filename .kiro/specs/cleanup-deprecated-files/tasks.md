# Implementation Plan: Limpieza de Archivos Deprecated

## Archivos Deprecated Identificados

### Domain Services (9 archivos)
1. `src/domain/services/articles/article_content_extraction_service.py`
2. `src/domain/services/articles/article_language_detection_service.py`
3. `src/domain/services/articles/article_metrics_calculation_service.py`
4. `src/domain/services/articles/article_plaintext_extraction_service.py`
5. `src/domain/services/articles/sentence_relevance_scorer.py`

### Interfaces (4 archivos)
6. `src/domain/interfaces/services/articles/article_content_extraction_service.py`
7. `src/domain/interfaces/services/articles/article_language_detection_service.py`
8. `src/domain/interfaces/services/articles/article_metrics_calculation_service.py`
9. `src/domain/interfaces/services/articles/article_scraping_service.py`

**Total: 9 archivos deprecated**

---

## Tasks

- [x] 1. PASO 1: Investigar causa y dependencias
  - Identificar todos los archivos deprecated en `src/domain/`
  - Buscar imports de archivos deprecated en `src/` y `tests/`
  - Generar reporte de dependencias con archivos y líneas
  - Verificar que nuevas ubicaciones existen
  - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 2.1, 2.2, 2.3, 2.4, 2.5_

- [x] 2. PASO 2: Resolver dependencias
  - Actualizar imports en `src/` para usar nuevas ubicaciones
  - Actualizar imports en `tests/` para usar nuevas ubicaciones
  - Actualizar imports en `src/bootstrap/containers/` si existen
  - Verificar que no quedan imports deprecated con grep
  - Ejecutar verificación final de imports
  - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5_

- [x] 3. PASO 3: Marcar archivos con extensión .bak
  - Renombrar `article_content_extraction_service.py` a `.bak`
  - Renombrar `article_language_detection_service.py` a `.bak`
  - Renombrar `article_metrics_calculation_service.py` a `.bak`
  - Renombrar `article_plaintext_extraction_service.py` a `.bak`
  - Renombrar `sentence_relevance_scorer.py` a `.bak`
  - Renombrar interfaces a `.bak` (4 archivos)
  - Verificar que todos los archivos .bak existen
  - Registrar operación en log
  - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5_

- [x] 4. PASO 4: Ejecutar pruebas y eliminar o revertir
  - Ejecutar `pytest tests/unit/` completo
  - Ejecutar `pytest tests/integration/` si aplica
  - Si tests pasan: Eliminar todos los archivos .bak
  - Si tests fallan: Revertir todos los .bak a .py
  - Generar reporte final de limpieza
  - Documentar archivos eliminados y estadísticas
  - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5, 6.1, 6.2, 6.3, 6.4, 6.5, 7.1, 7.2, 7.3, 7.4, 7.5_

---

## Mapeo de Migraciones

### Services
```
src/domain/services/articles/article_content_extraction_service.py
  → src/article/domain/services/content_extraction.py

src/domain/services/articles/article_language_detection_service.py
  → src/article/domain/services/language_detection.py

src/domain/services/articles/article_metrics_calculation_service.py
  → src/article/domain/services/metrics_calculation.py

src/domain/services/articles/article_plaintext_extraction_service.py
  → src/article/domain/services/plaintext_extraction.py

src/domain/services/articles/sentence_relevance_scorer.py
  → src/article/domain/services/sentence_relevance_scorer.py
```

### Interfaces
```
src/domain/interfaces/services/articles/article_content_extraction_service.py
  → src/article/domain/interfaces/services/content_extraction.py

src/domain/interfaces/services/articles/article_language_detection_service.py
  → src/article/domain/interfaces/services/language_detection.py

src/domain/interfaces/services/articles/article_metrics_calculation_service.py
  → src/article/domain/interfaces/services/metrics_calculation.py

src/domain/interfaces/services/articles/article_scraping_service.py
  → src/article/domain/interfaces/external/scraping_service.py
```

---

## Comandos Útiles

### Buscar imports deprecated
```bash
# Buscar en src/
grep -r "from src.domain.services.articles" src/ --include="*.py"
grep -r "from src.domain.interfaces.services.articles" src/ --include="*.py"

# Buscar en tests/
grep -r "from src.domain.services.articles" tests/ --include="*.py"
grep -r "from src.domain.interfaces.services.articles" tests/ --include="*.py"
```

### Renombrar a .bak
```bash
# Services
mv src/domain/services/articles/article_content_extraction_service.py src/domain/services/articles/article_content_extraction_service.py.bak
mv src/domain/services/articles/article_language_detection_service.py src/domain/services/articles/article_language_detection_service.py.bak
mv src/domain/services/articles/article_metrics_calculation_service.py src/domain/services/articles/article_metrics_calculation_service.py.bak
mv src/domain/services/articles/article_plaintext_extraction_service.py src/domain/services/articles/article_plaintext_extraction_service.py.bak
mv src/domain/services/articles/sentence_relevance_scorer.py src/domain/services/articles/sentence_relevance_scorer.py.bak

# Interfaces
mv src/domain/interfaces/services/articles/article_content_extraction_service.py src/domain/interfaces/services/articles/article_content_extraction_service.py.bak
mv src/domain/interfaces/services/articles/article_language_detection_service.py src/domain/interfaces/services/articles/article_language_detection_service.py.bak
mv src/domain/interfaces/services/articles/article_metrics_calculation_service.py src/domain/interfaces/services/articles/article_metrics_calculation_service.py.bak
mv src/domain/interfaces/services/articles/article_scraping_service.py src/domain/interfaces/services/articles/article_scraping_service.py.bak
```

### Ejecutar tests
```bash
# Tests completos
pytest tests/ -v

# Solo unit tests
pytest tests/unit/ -v

# Con coverage
pytest tests/ --cov=src --cov-report=term
```

### Eliminar .bak (si tests pasan)
```bash
# Eliminar todos los .bak
find src/domain/services/articles/ -name "*.bak" -delete
find src/domain/interfaces/services/articles/ -name "*.bak" -delete
```

### Revertir .bak (si tests fallan)
```bash
# Revertir todos los .bak
for file in $(find src/domain/ -name "*.bak"); do
    mv "$file" "${file%.bak}"
done
```

---

## Notas Importantes

1. **Orden de Ejecución**: Los pasos deben ejecutarse en orden secuencial (1 → 2 → 3 → 4)
2. **Reversibilidad**: Hasta el paso 4, todo es reversible renombrando .bak a .py
3. **Tests Críticos**: Si los tests fallan en paso 4, REVERTIR inmediatamente
4. **Documentación**: Generar reporte final después de paso 4
5. **Verificación**: Después de cada paso, verificar que todo está correcto antes de continuar

## Criterios de Éxito

- ✅ Todos los imports deprecated actualizados
- ✅ Todos los archivos deprecated renombrados a .bak
- ✅ Todos los tests pasan con archivos .bak
- ✅ Todos los archivos .bak eliminados
- ✅ Reporte final generado
- ✅ No quedan archivos deprecated en `src/domain/`
