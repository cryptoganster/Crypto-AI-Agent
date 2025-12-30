# Capacidades Existentes de Procesamiento de Contenido

## Introducción

Este documento registra las capacidades de procesamiento de contenido que ya están implementadas en el sistema, para evitar duplicación y facilitar la integración de nuevas funcionalidades de AI/ML.

## Pipeline de Extracción de Contenido (Implementado)

**Ubicación**: `src/article/app/process_managers/content_extraction_pipeline.py`

### Flujo Actual

```
ArticleContentScraped
    ↓
ExtractArticlePlaintextCommand
    ↓
ArticlePlaintextExtracted
    ↓
ConvertArticleToMarkdownCommand
    ↓
ArticleMarkdownConverted
```

### Componentes

1. **ArticleContentExtractionPipeline** (Process Manager)
   - Coordina el flujo de extracción
   - Mantiene estado del pipeline por artículo
   - Emite comandos basados en eventos

2. **ExtractArticlePlaintextCommand/Handler**
   - Ubicación: `src/article/app/commands/extract_article_plaintext/`
   - Extrae texto plano del HTML
   - Usa servicios externos de limpieza

3. **ConvertArticleToMarkdownCommand/Handler**
   - Ubicación: `src/article/app/commands/convert_article_to_markdown/`
   - Convierte HTML a formato markdown
   - Preserva estructura (headers, párrafos)

## Pipeline de Análisis de Contenido (Implementado)

**Ubicación**: `src/article/app/process_managers/content_analysis_pipeline.py`

### Flujo Actual

```
ArticleMarkdownConverted
    ↓
CalculateArticleMetricsCommand
    ↓
ArticleMetricsCalculated
    ↓
DetectArticleLanguageCommand
    ↓
ArticleLanguageDetected
    ↓
GenerateArticleSummaryCommand
    ↓
ArticleSummaryGenerated
    ↓
ExtractArticleKeywordsCommand
    ↓
ArticleKeywordsExtracted
    ↓
CalculateArticleQualityCommand
    ↓
ArticleQualityCalculated (FIN)
```

### Componentes

1. **ArticleContentAnalysisPipeline** (Process Manager)
   - Coordina análisis NLP completo
   - Pasa datos entre pasos vía eventos
   - Trackea estado del análisis

2. **CalculateArticleMetricsCommand/Handler**
   - Ubicación: `src/article/app/commands/calculate_article_metrics/`
   - Calcula: word_count, reading_time_minutes
   - Usa tiktoken para conteo de tokens

3. **DetectArticleLanguageCommand/Handler**
   - Ubicación: `src/article/app/commands/detect_article_language/`
   - Detecta idioma del contenido
   - Usa fasttext o langdetect

4. **GenerateArticleSummaryCommand/Handler**
   - Ubicación: `src/article/app/commands/generate_article_summary/`
   - Genera resumen del artículo
   - Usa extractive summarization

5. **ExtractArticleKeywordsCommand/Handler**
   - Ubicación: `src/article/app/commands/extract_article_keywords/`
   - Extrae keywords relevantes
   - Usa TF-IDF o RAKE

6. **CalculateArticleQualityCommand/Handler**
   - Ubicación: `src/article/app/commands/calculate_article_quality/`
   - Calcula score de calidad (0.0-1.0)
   - Considera múltiples factores

## Servicios de Limpieza y Normalización (Implementado)

**Ubicación**: `src/article/infra/external/`

### Servicios Disponibles

1. **HTML to Plaintext Converter**
   - Archivo: `html_to_plaintext_converter.py`
   - Remueve tags HTML
   - Normaliza espacios
   - Preserva estructura de párrafos

2. **HTML to Markdown Converter**
   - Archivo: `html_to_markdown_converter.py`
   - Convierte headers (h1 → #, h2 → ##)
   - Mantiene formato de listas
   - Preserva links y énfasis

3. **Language Detector**
   - Archivo: `language_detector.py`
   - Detecta idioma del texto
   - Usa fasttext o langdetect
   - Retorna código ISO (es, en, etc.)

4. **Playwright Scraper Service**
   - Archivo: `playwright_scraper_service.py`
   - Scraping con JavaScript rendering
   - Maneja contenido dinámico
   - Retorna HTML completo

5. **Trafilatura Scraper Service**
   - Archivo: `trafilatura_scraper_service.py`
   - Extracción de contenido principal
   - Remueve ads, banners, scripts
   - Optimizado para artículos de noticias

## Comandos de Scraping (Implementado)

**Ubicación**: `src/article/app/commands/scrape_article_content/`

### ScrapeArticleContentCommand/Handler

- Scraping de contenido HTML
- Usa Playwright o Trafilatura según configuración
- Emite ArticleContentScraped event
- Maneja errores y timeouts

## Capacidades de Summarización (Implementado)

**Ubicación**: `src/article/domain/services/summary_extraction.py`

### ArticleSummaryExtractionService

- Extractive summarization
- Selección de oraciones más relevantes
- Scoring basado en:
  - Posición en el texto
  - Frecuencia de términos
  - Longitud de oración
  - Presencia de entidades nombradas

## Lo que FALTA Implementar (Para AI/ML Bounded Context)

### 1. Chunking Inteligente
- División en chunks de 1200-1500 tokens
- Overlap de 150 tokens
- Separadores jerárquicos
- Preservación de contexto semántico

### 2. Vector Embeddings
- Generación con nomic-embed-text
- Dimensión 768
- Normalización de vectores
- Batch processing

### 3. Vector Storage (pgvector)
- Almacenamiento de embeddings
- Índices HNSW para búsqueda
- Metadata asociada
- Queries de similitud

### 4. Semantic Search
- Búsqueda por similitud vectorial
- Filtros por fecha, source, topics
- Top-k retrieval
- Score de relevancia

### 5. Semantic Clustering
- Agrupación de artículos similares
- K-means o DBSCAN
- Labels descriptivos
- Detección de outliers

### 6. RAG Context Assembly
- Construcción de context packs
- Ordenamiento por relevancia
- Límite de tokens
- Formateo para LLM

### 7. Content Generation with RAG
- Generación basada en contexto recuperado
- Prompts estructurados
- Citación de fuentes
- Validación de factualidad

### 8. Hierarchical Summarization
- Chunk summaries (3-5 frases)
- Global summary (artículo completo)
- TLDR fusion (3-5 bullets)
- Preservación de información crítica

### 9. Duplicate Detection (Semántica)
- Detección usando embeddings
- Threshold de similitud (0.85)
- Comparación multi-dimensional
- Prevención de procesamiento redundante

## Integración Recomendada

### Event-Driven Integration

El nuevo bounded context de AI/ML debe integrarse vía eventos:

```
ArticleQualityCalculated (último paso del pipeline actual)
    ↓
OnArticleQualityCalculated (nuevo event handler)
    ↓
ProcessArticleForAICommand (nuevo comando en AI BC)
    ↓
AI Processing Pipeline:
    - Chunking
    - Embeddings
    - Vector Storage
    - Clustering
    ↓
ArticleAIProcessedEvent (nuevo evento)
```

### Reutilización de Datos

El AI BC puede reutilizar:
- ✅ `plaintext` (ya limpio y normalizado)
- ✅ `markdown_content` (ya estructurado)
- ✅ `summary` (extractive summary existente)
- ✅ `keywords` (ya extraídos)
- ✅ `language_code` (ya detectado)
- ✅ `word_count` (ya calculado)

### Nuevos Datos a Generar

El AI BC generará:
- ❌ `chunks` (lista de ContentChunk)
- ❌ `embeddings` (vectores 768-dim)
- ❌ `chunk_summaries` (summaries por chunk)
- ❌ `global_summary` (LLM-based)
- ❌ `tldr` (fusion de summaries)
- ❌ `cluster_id` (agrupación semántica)
- ❌ `similar_articles` (basado en embeddings)

## Comandos y Queries Existentes

### Comandos Disponibles

1. `ScrapeArticleContentCommand` - Scraping de HTML
2. `ExtractArticlePlaintextCommand` - Extracción de texto plano
3. `ConvertArticleToMarkdownCommand` - Conversión a markdown
4. `CalculateArticleMetricsCommand` - Métricas básicas
5. `DetectArticleLanguageCommand` - Detección de idioma
6. `GenerateArticleSummaryCommand` - Generación de resumen
7. `ExtractArticleKeywordsCommand` - Extracción de keywords
8. `CalculateArticleQualityCommand` - Cálculo de calidad

### Queries Disponibles

- `GetArticleByIdQuery` - Obtener artículo por ID
- `GetArticlesListQuery` - Listar artículos con filtros
- `GetArticlesByQualityQuery` - Filtrar por calidad
- `GetArticlesBySourceQuery` - Filtrar por fuente

## Recomendaciones para Nuevo Bounded Context

### 1. No Duplicar Funcionalidad

- ✅ Reutilizar pipelines existentes
- ✅ Consumir datos ya procesados
- ✅ Integrarse vía eventos
- ❌ NO reimplementar limpieza de HTML
- ❌ NO reimplementar detección de idioma
- ❌ NO reimplementar extractive summarization

### 2. Enfocarse en Valor Agregado

- ✅ Chunking inteligente
- ✅ Embeddings vectoriales
- ✅ Búsqueda semántica
- ✅ RAG capabilities
- ✅ Generación de contenido
- ✅ Clustering semántico

### 3. Mantener Separación de Concerns

- **Article BC**: Gestión de artículos, scraping, análisis básico
- **AI BC**: Procesamiento avanzado con ML, embeddings, RAG
- **Integración**: Event-driven, desacoplada

### 4. Usar Interfaces Compartidas

- `ILogger` - Logging consistente
- `IMediator` - Command/Query bus
- `IEventBus` - Publicación de eventos
- `IUnitOfWork` - Transacciones

## Referencias

- **Architecture**: `.kiro/steering/architecture.md`
- **Event-Driven Architecture**: `.kiro/steering/event-driven-architecture.md`
- **Domain Patterns**: `.kiro/steering/domain-patterns.md`
- **Process Managers**: Ver ejemplos en `src/article/app/process_managers/`

---

**Última actualización**: 2024-12-09
**Autor**: Sistema de documentación automática

