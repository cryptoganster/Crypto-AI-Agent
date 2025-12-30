# Requirements Document

## Introduction

El sistema necesita capacidades avanzadas de procesamiento de contenido usando AI/ML para transformar artículos scrapeados en contenido estructurado, semánticamente indexado y listo para generación de contenido mediante RAG (Retrieval-Augmented Generation). Este bounded context manejará chunking inteligente, embeddings vectoriales, summarización jerárquica, clustering semántico y generación de contenido nuevo basado en recuperación de información relevante.

## Glossary

- **Chunking**: Proceso de dividir texto largo en segmentos manejables manteniendo coherencia semántica
- **Embedding**: Representación vectorial densa de texto que captura significado semántico
- **RAG (Retrieval-Augmented Generation)**: Patrón que combina recuperación de información con generación de contenido
- **TLDR (Too Long; Didn't Read)**: Resumen ejecutivo ultra-conciso de un artículo
- **Chunk Summary**: Resumen individual de un chunk específico
- **Global Summary**: Resumen del artículo completo considerando todo el contenido
- **Context Pack**: Conjunto de chunks, summaries y metadata recuperados para generación
- **Vector Search**: Búsqueda por similitud semántica usando embeddings
- **pgvector**: Extensión de PostgreSQL para almacenar y buscar vectores
- **Semantic Clustering**: Agrupación de contenido similar usando embeddings
- **Token**: Unidad básica de texto para modelos de lenguaje (medido con tiktoken)
- **Content Processor**: Servicio que orquesta el pipeline completo de procesamiento
- **Nomic Embed**: Modelo de embeddings de alta calidad para texto
- **Sentence Transformers**: Biblioteca para crear embeddings de oraciones

## Requirements

### Nota: Capacidades Existentes

El sistema ya tiene implementado:
- ✅ **Text Cleaning**: HTML → plaintext (Trafilatura, BeautifulSoup)
- ✅ **Markdown Conversion**: HTML → markdown con headers estructurados
- ✅ **Basic Summarization**: Extractive summarization
- ✅ **Language Detection**: fasttext/langdetect
- ✅ **Keyword Extraction**: TF-IDF/RAKE
- ✅ **Metrics Calculation**: word_count, reading_time
- ✅ **Pipeline Orchestration**: Process Managers para extracción y análisis

Ver: `.kiro/steering/existing-content-processing-capabilities.md`

Este bounded context se enfoca en capacidades avanzadas de AI/ML que NO existen:
- Chunking inteligente con overlap
- Vector embeddings (nomic-embed-text)
- Vector storage (pgvector)
- Semantic search
- Semantic clustering
- RAG context assembly
- Content generation with RAG
- Hierarchical summarization (LLM-based)

### Requirement 1: Intelligent Text Chunking

**User Story:** Como sistema de procesamiento, quiero dividir artículos largos en chunks semánticamente coherentes, para que cada chunk sea procesable independientemente manteniendo contexto.

#### Acceptance Criteria

1. WHEN el sistema recibe texto limpio THEN el sistema SHALL dividir en chunks de 1200-1500 tokens usando tiktoken
2. WHEN el sistema crea chunks THEN el sistema SHALL mantener overlap de 150 tokens entre chunks consecutivos
3. WHEN el sistema divide texto THEN el sistema SHALL usar separadores jerárquicos (\n\n, \n, ., espacio)
4. WHEN el sistema chunking encuentra párrafo largo THEN el sistema SHALL dividir en límites de oración
5. WHEN el sistema completa chunking THEN el sistema SHALL retornar lista ordenada de chunks con metadata
6. WHEN un chunk excede tamaño máximo THEN el sistema SHALL forzar división en límite de token más cercano
7. WHEN el sistema crea chunks THEN el sistema SHALL preservar información de posición original en el artículo

### Requirement 2: Vector Embeddings Generation

**User Story:** Como sistema de procesamiento, quiero generar embeddings vectoriales de alta calidad para cada chunk, para habilitar búsqueda semántica y clustering.

#### Acceptance Criteria

1. WHEN el sistema recibe chunks THEN el sistema SHALL generar embeddings usando nomic-embed-text
2. WHEN el sistema genera embeddings THEN el sistema SHALL producir vectores de dimensión 768
3. WHEN el sistema procesa batch de chunks THEN el sistema SHALL generar embeddings en paralelo para eficiencia
4. WHEN el sistema completa embeddings THEN el sistema SHALL retornar lista alineada con chunks originales
5. WHEN el embedding falla para un chunk THEN el sistema SHALL loggear error y continuar con otros chunks
6. WHEN el sistema genera embeddings THEN el sistema SHALL normalizar vectores a magnitud unitaria
7. WHEN el sistema procesa texto vacío THEN el sistema SHALL retornar vector cero o manejar gracefully

### Requirement 3: Hierarchical Summarization (LLM-based)

**User Story:** Como sistema de procesamiento, quiero generar summaries jerárquicos (por chunk y global), para crear TLDRs de alta calidad que capturen información crítica.

#### Acceptance Criteria

1. WHEN el sistema recibe chunk THEN el sistema SHALL generar summary de 3-5 frases manteniendo hechos importantes
2. WHEN el sistema genera chunk summary THEN el sistema SHALL preservar números, fechas, actores y eventos clave
3. WHEN el sistema completa chunk summaries THEN el sistema SHALL generar summary global del artículo completo
4. WHEN el sistema genera global summary THEN el sistema SHALL considerar todo el contenido limpio original
5. WHEN el sistema fusiona summaries THEN el sistema SHALL crear TLDR final de 3-5 bullets
6. WHEN el sistema crea TLDR THEN el sistema SHALL incluir: qué pasó, impacto, tokens afectados, actores, riesgos
7. WHEN el sistema genera summaries THEN el sistema SHALL NO agregar información no presente en el texto original
8. WHEN el summary falla THEN el sistema SHALL retornar error descriptivo sin detener pipeline completo

### Requirement 4: Vector Storage and Indexing

**User Story:** Como sistema de almacenamiento, quiero persistir chunks, embeddings y summaries en PostgreSQL con pgvector, para habilitar búsquedas semánticas eficientes.

#### Acceptance Criteria

1. WHEN el sistema persiste chunks THEN el sistema SHALL almacenar en tabla con columnas: article_id, chunk_id, content, summary, embedding, position
2. WHEN el sistema almacena embeddings THEN el sistema SHALL usar tipo VECTOR(768) de pgvector
3. WHEN el sistema guarda chunks THEN el sistema SHALL crear índice HNSW para búsqueda vectorial eficiente
4. WHEN el sistema persiste THEN el sistema SHALL almacenar metadata: published_at, source, topics, tokens_mentioned
5. WHEN el sistema completa persistencia THEN el sistema SHALL retornar IDs de chunks creados
6. WHEN el almacenamiento falla THEN el sistema SHALL hacer rollback y retornar error descriptivo
7. WHEN el sistema actualiza artículo THEN el sistema SHALL eliminar chunks antiguos antes de insertar nuevos

### Requirement 5: Semantic Search and Retrieval

**User Story:** Como sistema de recuperación, quiero buscar chunks relevantes usando similitud vectorial, para construir context packs para generación de contenido.

#### Acceptance Criteria

1. WHEN el sistema recibe query de búsqueda THEN el sistema SHALL generar embedding del query
2. WHEN el sistema busca chunks THEN el sistema SHALL usar operador de distancia coseno (<->) de pgvector
3. WHEN el sistema ejecuta búsqueda THEN el sistema SHALL retornar top-k chunks más similares (k configurable)
4. WHEN el sistema recupera chunks THEN el sistema SHALL incluir: content, summary, TLDR, metadata
5. WHEN el sistema completa búsqueda THEN el sistema SHALL ordenar resultados por score de similitud descendente
6. WHEN el sistema busca THEN el sistema SHALL permitir filtros adicionales: fecha, source, topics
7. WHEN no hay resultados THEN el sistema SHALL retornar lista vacía con mensaje descriptivo

### Requirement 6: Semantic Clustering

**User Story:** Como sistema de análisis, quiero agrupar artículos similares en clusters semánticos, para identificar temas trending y relacionar contenido.

#### Acceptance Criteria

1. WHEN el sistema ejecuta clustering THEN el sistema SHALL usar algoritmo K-means o DBSCAN sobre embeddings
2. WHEN el sistema agrupa artículos THEN el sistema SHALL considerar embeddings de chunks y global summaries
3. WHEN el sistema crea clusters THEN el sistema SHALL asignar label descriptivo basado en términos frecuentes
4. WHEN el sistema completa clustering THEN el sistema SHALL retornar: cluster_id, articles, centroid, label
5. WHEN el sistema detecta outliers THEN el sistema SHALL marcarlos como cluster especial
6. WHEN el clustering falla THEN el sistema SHALL retornar error sin afectar datos existentes
7. WHEN el sistema actualiza clusters THEN el sistema SHALL recalcular periódicamente con nuevos artículos

### Requirement 7: RAG Context Pack Assembly

**User Story:** Como sistema de generación, quiero ensamblar context packs con chunks relevantes y summaries, para proveer contexto rico al LLM generador.

#### Acceptance Criteria

1. WHEN el sistema recibe topic para generación THEN el sistema SHALL recuperar top-k chunks relevantes
2. WHEN el sistema ensambla context pack THEN el sistema SHALL incluir: chunks, chunk summaries, TLDRs, metadata
3. WHEN el sistema construye contexto THEN el sistema SHALL ordenar chunks por relevancia y fecha
4. WHEN el sistema prepara pack THEN el sistema SHALL limitar tokens totales a presupuesto configurable
5. WHEN el sistema completa ensamblaje THEN el sistema SHALL formatear contexto para prompt del LLM
6. WHEN el contexto excede límite THEN el sistema SHALL priorizar chunks más relevantes y recientes
7. WHEN el sistema ensambla THEN el sistema SHALL incluir instrucciones de uso del contexto

### Requirement 8: Content Generation with RAG

**User Story:** Como sistema de generación, quiero crear contenido nuevo basado en context packs recuperados, para producir artículos, análisis y newsletters de alta calidad.

#### Acceptance Criteria

1. WHEN el sistema recibe request de generación THEN el sistema SHALL ensamblar context pack relevante
2. WHEN el sistema genera contenido THEN el sistema SHALL usar prompt RAG con instrucciones claras
3. WHEN el sistema crea contenido THEN el sistema SHALL basar EXCLUSIVAMENTE en información del contexto
4. WHEN el sistema genera THEN el sistema SHALL incluir: resumen ejecutivo, narrativa, impacto, riesgos, oportunidades
5. WHEN el sistema completa generación THEN el sistema SHALL retornar contenido estructurado con metadata
6. WHEN el sistema genera THEN el sistema SHALL citar fuentes originales de chunks usados
7. WHEN la generación falla THEN el sistema SHALL retornar error descriptivo con contexto usado
8. WHEN el sistema genera contenido factual THEN el sistema SHALL NO inventar eventos no presentes en contexto

### Requirement 9: Duplicate Detection (Semantic)

**User Story:** Como sistema de calidad, quiero detectar artículos duplicados o muy similares usando embeddings, para evitar procesamiento redundante.

#### Acceptance Criteria

1. WHEN el sistema recibe nuevo artículo THEN el sistema SHALL generar embedding del contenido completo
2. WHEN el sistema verifica duplicados THEN el sistema SHALL buscar artículos con similitud > threshold (0.85)
3. WHEN el sistema encuentra similar THEN el sistema SHALL comparar: título, URL, contenido, fecha
4. WHEN el sistema detecta duplicado THEN el sistema SHALL marcar artículo y NO procesar completamente
5. WHEN el sistema completa verificación THEN el sistema SHALL retornar: is_duplicate, similar_articles, similarity_scores
6. WHEN no hay duplicados THEN el sistema SHALL continuar con pipeline normal
7. WHEN la verificación falla THEN el sistema SHALL asumir no-duplicado y continuar

### Requirement 10: AI Pipeline Integration

**User Story:** Como sistema de integración, quiero conectar el nuevo pipeline de AI con el pipeline existente de análisis, para que el procesamiento sea automático y event-driven.

#### Acceptance Criteria

1. WHEN ArticleQualityCalculated event ocurre THEN el sistema SHALL iniciar ProcessArticleForAICommand
2. WHEN el sistema procesa artículo THEN el sistema SHALL reutilizar datos existentes: plaintext, markdown, summary, keywords
3. WHEN el sistema ejecuta AI pipeline THEN el sistema SHALL ejecutar: chunk → embed → summarize → persist
4. WHEN el sistema completa AI processing THEN el sistema SHALL emitir ArticleAIProcessedEvent
5. WHEN el sistema detecta duplicado semántico THEN el sistema SHALL saltar procesamiento y marcar como duplicado
6. WHEN un paso falla THEN el sistema SHALL loggear error y continuar con siguiente artículo
7. WHEN el pipeline completa THEN el sistema SHALL retornar resultado con: chunks_created, embeddings_generated, tldr_generated

### Requirement 11: Performance and Scalability

**User Story:** Como sistema de alto rendimiento, quiero procesar artículos eficientemente usando batching y paralelización, para manejar volumen alto de contenido.

#### Acceptance Criteria

1. WHEN el sistema procesa múltiples artículos THEN el sistema SHALL usar batching para embeddings (batch size: 32)
2. WHEN el sistema genera summaries THEN el sistema SHALL procesar chunks en paralelo con límite de concurrencia
3. WHEN el sistema persiste THEN el sistema SHALL usar bulk inserts para chunks y embeddings
4. WHEN el sistema ejecuta búsqueda THEN el sistema SHALL usar índice HNSW para latencia < 100ms
5. WHEN el sistema procesa batch grande THEN el sistema SHALL dividir en sub-batches para evitar timeouts
6. WHEN el sistema completa procesamiento THEN el sistema SHALL reportar métricas: throughput, latencia, tokens/segundo
7. WHEN el sistema detecta carga alta THEN el sistema SHALL aplicar backpressure y rate limiting

