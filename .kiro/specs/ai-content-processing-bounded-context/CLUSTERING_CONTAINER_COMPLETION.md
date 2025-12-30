# Clustering Container - Tarea 10.3 Completada

## Resumen

Se ha completado exitosamente la implementación del **ClusteringContainer** para el bounded context de Clustering, siguiendo los patrones establecidos en ChunkingContainer y EmbeddingContainer.

## Archivos Creados

### 1. Container Principal
- **`src/clustering/container.py`**
  - ClusteringContainer con lazy initialization
  - Factories para todos los servicios, repositories y handlers
  - Registro de command, query y event handlers
  - Integración con SharedContainer

### 2. Configuración
- **`src/shared/config/clustering_config.py`**
  - ClusteringConfig dataclass
  - Carga desde variables de entorno
  - Validación de configuración
  - Defaults apropiados

### 3. Event Handler
- **`src/clustering/app/event_handlers/__init__.py`**
- **`src/clustering/app/event_handlers/on_article_embedding_generated.py`**
  - OnArticleEmbeddingGeneratedHandler
  - Escucha ArticleEmbeddingGenerated del Embedding BC
  - Por ahora solo loggea (clustering manual/programado)

### 4. Factory
- **`src/clustering/domain/factories/__init__.py`**
- **`src/clustering/domain/factories/semantic_cluster_factory.py`**
  - SemanticClusterFactory
  - Validación de datos de entrada
  - Limpieza de label y top_terms
  - Creación de SemanticCluster

### 5. Tests de Integración
- **`tests/integration/clustering/__init__.py`**
- **`tests/integration/clustering/test_clustering_container.py`**
  - Tests de resolución de servicios
  - Tests de resolución de repositories
  - Tests de resolución de handlers
  - Tests de registro de handlers
  - Tests de configuración desde env
  - Tests de validación de configuración

### 6. Configuración de Entorno
- **`.env.example`** (actualizado)
  - Variables de clustering agregadas
  - Variables de chunking agregadas
  - Variables de embedding agregadas

## Componentes Registrados

### Command Handlers
- ✅ **ClusterArticlesHandler**
  - Agrupa artículos en clusters semánticos
  - Usa ClusteringService (KMeans o DBSCAN)
  - Asigna labels descriptivos con TF-IDF

### Query Handlers
- ✅ **GetArticleClustersHandler**
  - Obtiene clusters de artículos
  - Aplica filtros (min_size)
  - Ordenamiento configurable

### Event Handlers
- ✅ **OnArticleEmbeddingGeneratedHandler**
  - Escucha ArticleEmbeddingGenerated
  - Por ahora solo loggea
  - Clustering debe ejecutarse manualmente o programado

### Domain Services
- ✅ **ClusteringService**
  - Algoritmos: KMeans, DBSCAN
  - Asignación de labels con TF-IDF
  - Cálculo de métricas de calidad

### Repositories
- ✅ **SemanticClusterReadRepository**
  - Lectura de clusters
  - Filtrado por tamaño
  - Ordenamiento

- ✅ **SemanticClusterWriteRepository**
  - Persistencia de clusters
  - Actualización de clusters

### Factories
- ✅ **SemanticClusterFactory**
  - Validación de datos
  - Limpieza de label
  - Normalización de top_terms

## Configuración

### Variables de Entorno

```bash
# Clustering Configuration
CLUSTERING_ALGORITHM=kmeans          # "kmeans" o "dbscan"
CLUSTERING_N_CLUSTERS=10             # Número de clusters (KMeans)
CLUSTERING_DBSCAN_EPS=0.3            # Epsilon para DBSCAN
CLUSTERING_DBSCAN_MIN_SAMPLES=2     # Min samples para DBSCAN
CLUSTERING_MIN_CLUSTER_SIZE=3       # Tamaño mínimo de cluster
CLUSTERING_RANDOM_STATE=42          # Seed para reproducibilidad
```

### Defaults
- **Algorithm**: kmeans
- **N Clusters**: 10
- **DBSCAN Eps**: 0.3
- **DBSCAN Min Samples**: 2
- **Min Cluster Size**: 3
- **Random State**: 42

## Arquitectura Event-Driven

### Flujo de Eventos

```
ArticleEmbeddingGenerated (Embedding BC)
    ↓ (Event Bus)
OnArticleEmbeddingGeneratedHandler (Clustering BC)
    ↓ (solo loggea por ahora)
[Clustering manual o programado]
    ↓
ClusterArticlesCommand
    ↓
ClusterArticlesHandler
    ↓
ClusteringService (KMeans/DBSCAN)
    ↓
SemanticCluster aggregates
    ↓
SemanticClusterWriteRepository
```

### Nota sobre Clustering Automático

El clustering NO se ejecuta automáticamente cuando se generan embeddings porque:
1. Es una operación costosa (O(n²) para DBSCAN)
2. Requiere todos los embeddings del corpus
3. Mejor ejecutar en batch programado o manualmente

**Opciones futuras**:
- Acumular artículos y re-clusterizar cada N artículos
- Re-clusterizar en horarios de baja carga
- Usar clustering incremental

## Tests

### Cobertura de Tests

- ✅ Resolución de servicios
- ✅ Resolución de repositories
- ✅ Resolución de handlers
- ✅ Registro de command handlers
- ✅ Registro de query handlers
- ✅ Registro de event handlers
- ✅ Configuración desde environment
- ✅ Validación de configuración
- ✅ Manejo de errores

### Ejecutar Tests

```bash
# Tests de integración del container
pytest tests/integration/clustering/test_clustering_container.py -v

# Todos los tests de clustering
pytest tests/integration/clustering/ -v

# Con coverage
pytest tests/integration/clustering/ --cov=src/clustering/container --cov-report=term
```

## Integración con SharedContainer

El ClusteringContainer se integra con SharedContainer para:
- ✅ Logger compartido
- ✅ Mediator para command/query bus
- ✅ EventHandlerRegistry para event bus
- ✅ SessionFactory para repositories
- ✅ EventPublisher para domain events

## Patrones Implementados

### 1. Dependency Injection
- Lazy initialization de dependencias
- Factory methods para cada componente
- Inyección vía constructor

### 2. Clean Architecture
- Domain services sin dependencias de infra
- Repositories implementan interfaces del dominio
- Handlers orquestan casos de uso

### 3. CQRS
- Command handlers para escritura
- Query handlers para lectura
- Separación clara de responsabilidades

### 4. Event-Driven Architecture
- Event handlers escuchan eventos de otros BCs
- Desacoplamiento entre bounded contexts
- Comunicación asíncrona vía event bus

### 5. Factory Pattern
- SemanticClusterFactory para creación compleja
- Validación y limpieza de datos
- Separación de creación y lógica de negocio

## Próximos Pasos

### Implementaciones Pendientes

1. **Vector Store Integration**
   - Implementar IVectorStore para recuperar embeddings
   - Integrar con pgvector
   - Query para obtener embeddings de artículos

2. **Clustering Automático**
   - Implementar lógica de re-clustering incremental
   - Scheduled job para clustering batch
   - Threshold de artículos para re-clustering

3. **Métricas de Calidad**
   - Silhouette score
   - Davies-Bouldin index
   - Calinski-Harabasz index

4. **API Endpoints**
   - POST /api/v1/clustering/cluster-articles
   - GET /api/v1/clustering/clusters
   - GET /api/v1/clustering/clusters/{cluster_id}

5. **CLI Commands**
   - cluster-articles
   - list-clusters
   - cluster-quality-metrics

## Validación de Requirements

### 10.3.1 Create ClusteringContainer ✅
- [x] Container creado con lazy initialization
- [x] Registro de ClusteringService
- [x] Registro de SemanticClusterReadRepository
- [x] Registro de SemanticClusterWriteRepository
- [x] Registro de SemanticClusterFactory

### 10.3.2 Register Clustering command handlers ✅
- [x] ClusterArticlesHandler registrado
- [x] Usa `register_pipeline_handlers()` method
- [x] Logging de handlers registrados

### 10.3.3 Register Clustering query handlers ✅
- [x] GetArticleClustersHandler registrado
- [x] Usa `register_pipeline_handlers()` method
- [x] Logging de handlers registrados

### 10.3.4 Register Clustering event handlers ✅
- [x] OnArticleEmbeddingGeneratedHandler registrado
- [x] Usa `register_event_handlers()` method
- [x] Logging de handlers registrados

### 10.3.5 Add Clustering configuration ✅
- [x] ClusteringConfig class creada
- [x] Carga CLUSTERING_ALGORITHM, MIN_CLUSTER_SIZE desde env
- [x] Validación de configuración
- [x] Defaults apropiados

### 10.3.6 Write integration tests for ClusteringContainer ✅
- [x] Test service resolution
- [x] Test handler registration
- [x] Test event handler registration
- [x] Test configuration loading
- [x] Test validation

## Conclusión

El ClusteringContainer está completamente implementado y sigue los mismos patrones que ChunkingContainer y EmbeddingContainer. Todos los handlers están registrados correctamente y los tests de integración validan la funcionalidad.

**Status**: ✅ COMPLETADO

**Requirements**: 10.3.1, 10.3.2, 10.3.3, 10.3.4, 10.3.5, 10.3.6

**Fecha**: 2024-12-11
