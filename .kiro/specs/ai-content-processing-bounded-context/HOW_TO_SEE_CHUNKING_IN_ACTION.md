# Cómo Ver el Chunking en Acción

## Estado Actual ✅

El bounded context de **Chunking** está **completamente integrado** al flujo principal del sistema. Aquí está cómo funciona:

## Flujo Completo (Event-Driven)

```
1. Article BC: Content Analysis Pipeline
   ├─ ScrapeArticleContent
   ├─ ExtractPlaintext
   ├─ ConvertToMarkdown
   ├─ CalculateMetrics
   ├─ DetectLanguage
   ├─ GenerateSummary
   ├─ ExtractKeywords
   └─ CalculateQuality ✅ (último paso)
       ↓
       Emite: ArticleQualityCalculated
       
2. Event Bus
   ↓
   
3. Chunking BC: OnArticleQualityCalculatedHandler ✅
   ├─ Escucha: ArticleQualityCalculated
   ├─ Query: GetArticleByIdQuery (obtiene plaintext, markdown, etc.)
   └─ Emite: ProcessArticleForAICommand
       ↓
       
4. Chunking BC: ProcessArticleForAIHandler ✅
   ├─ Step 1: Chunking (divide texto en chunks)
   ├─ Step 2: Embeddings (genera vectores)
   ├─ Step 3: Summaries (resume cada chunk)
   ├─ Step 4: Mark as completed
   ├─ Step 5: Persist to vector store
   ├─ Step 6: Global summary (opcional)
   ├─ Step 7: TLDR (opcional)
   └─ Emite: ArticleAIProcessedEvent
       ↓
       
5. Embedding BC: OnArticleAIProcessedHandler
   └─ Procesa embeddings adicionales (si necesario)
```

## Cómo Activar el Flujo

### Opción 1: Via API (Recomendado)

```bash
# 1. Crear una source RSS
curl -X POST http://localhost:8000/api/v1/sources \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Test Source",
    "url": "https://example.com/feed.xml",
    "fetch_interval": 3600
  }'

# 2. Iniciar fetch session (esto dispara todo el pipeline)
curl -X POST http://localhost:8000/api/v1/fetch-sessions \
  -H "Content-Type: application/json" \
  -d '{
    "source_ids": ["<source_id>"]
  }'

# 3. El flujo completo se ejecuta automáticamente:
#    - Scraping → Extraction → Analysis → Quality → AI Processing
```

### Opción 2: Via Command Line

```bash
# Ejecutar el pipeline completo
python -m src.main fetch --source-id <source_id>
```

### Opción 3: Trigger Manual (Para Testing)

```python
# En un script de prueba o notebook
import asyncio
from src.bootstrap.containers.main import MainContainer
from src.article.domain.events import ArticleQualityCalculated

async def trigger_ai_processing():
    # Inicializar container
    container = MainContainer()
    await container.init_resources()
    
    # Crear evento manualmente
    event = ArticleQualityCalculated(
        article_id="<article_id>",
        quality_score=0.85,
        success=True,
    )
    
    # Publicar evento (dispara el handler)
    await container.shared.event_bus.publish(event)
    
    print("✅ Evento publicado - revisa logs para ver el procesamiento")

# Ejecutar
asyncio.run(trigger_ai_processing())
```

## Cómo Verificar que Está Funcionando

### 1. Logs en Tiempo Real

```bash
# Ver logs del sistema
tail -f logs/app.log | grep -E "(ArticleQualityCalculated|ProcessArticleForAI|Chunking)"

# Buscar específicamente el handler de chunking
tail -f logs/app.log | grep "OnArticleQualityCalculatedHandler"

# Ver el pipeline completo
tail -f logs/app.log | grep "🚀\|📝\|🔢\|📋\|💾\|✅\|🎉"
```

### 2. Verificar en Base de Datos

```sql
-- Ver artículos procesados
SELECT 
    id,
    title,
    quality_score,
    content_plaintext IS NOT NULL as has_plaintext,
    content_markdown IS NOT NULL as has_markdown,
    summary IS NOT NULL as has_summary
FROM articles
WHERE quality_score IS NOT NULL
ORDER BY created_at DESC
LIMIT 10;

-- Ver chunks generados (si tienes tabla de chunks)
SELECT 
    article_id,
    COUNT(*) as chunk_count,
    SUM(token_count) as total_tokens
FROM content_chunks
GROUP BY article_id
ORDER BY created_at DESC;
```

### 3. Verificar Eventos Publicados

```python
# En un test o script
from src.bootstrap.containers.main import MainContainer

async def check_events():
    container = MainContainer()
    await container.init_resources()
    
    # Ver handlers registrados
    event_registry = container.shared.event_handler_registry
    
    # Verificar que OnArticleQualityCalculatedHandler está registrado
    from src.article.domain.events import ArticleQualityCalculated
    
    handlers = event_registry.get_handlers(ArticleQualityCalculated)
    print(f"Handlers para ArticleQualityCalculated: {len(handlers)}")
    
    for handler in handlers:
        print(f"  - {handler.__class__.__name__}")
```

## Logs Esperados

Cuando el flujo se ejecuta correctamente, verás logs como estos:

```
[INFO] ArticleQualityCalculated exitoso - iniciando procesamiento AI
       article_id=abc-123 quality_score=0.85

[INFO] ProcessArticleForAICommand emitido exitosamente
       article_id=abc-123 plaintext_length=5000 has_markdown=True

[INFO] 🚀 Iniciando procesamiento AI de artículo
       article_id=abc-123 plaintext_length=5000

[INFO] 📝 Step 1/7: Chunking texto
       article_id=abc-123

[INFO] ✅ Chunks creados
       article_id=abc-123 chunks_count=4 total_tokens=1200

[INFO] 🔢 Step 2/7: Generando embeddings
       article_id=abc-123 chunks_count=4

[INFO] ✅ Embeddings generados
       article_id=abc-123 embeddings_count=4

[INFO] 📋 Step 3/7: Generando summaries
       article_id=abc-123 chunks_count=4

[INFO] ✅ Summaries generados
       article_id=abc-123 summaries_count=4

[INFO] 💾 Step 5/7: Persistiendo chunks en vector store
       article_id=abc-123 chunks_count=4

[INFO] ✅ Chunks persistidos
       article_id=abc-123 chunk_ids_count=4

[INFO] 🎉 Procesamiento AI completado exitosamente
       article_id=abc-123 chunks_created=4 total_tokens=1200
```

## Troubleshooting

### Si no ves logs de chunking:

1. **Verificar que el handler está registrado**:
   ```python
   # En src/chunking/container.py
   # Buscar: _register_event_handlers()
   # Debe registrar OnArticleQualityCalculatedHandler
   ```

2. **Verificar que el evento se publica**:
   ```python
   # En src/article/app/commands/calculate_article_quality/handler.py
   # Debe emitir ArticleQualityCalculated al final
   ```

3. **Verificar configuración**:
   ```bash
   # En .env
   CHUNKING_ENABLED=true
   CHUNKING_CHUNK_SIZE=1200
   CHUNKING_OVERLAP=150
   ```

4. **Verificar que el artículo tiene plaintext**:
   ```sql
   SELECT id, content_plaintext IS NOT NULL 
   FROM articles 
   WHERE id = '<article_id>';
   ```

### Si el handler se ejecuta pero falla:

1. **Revisar logs de error**:
   ```bash
   tail -f logs/app.log | grep "ERROR\|Exception"
   ```

2. **Verificar dependencias**:
   - ChunkingService está inicializado
   - EmbeddingService está disponible
   - VectorStore está configurado

3. **Verificar configuración de servicios externos**:
   ```bash
   # En .env
   EMBEDDING_MODEL=nomic-embed-text
   EMBEDDING_DIMENSION=768
   VECTOR_STORE_TYPE=pgvector
   ```

## Testing Manual

### Script de Prueba Completo

```python
# test_chunking_flow.py
import asyncio
from src.bootstrap.containers.main import MainContainer
from src.article.app.commands.create_article.command import CreateArticleCommand

async def test_full_flow():
    """Test completo del flujo de chunking."""
    
    # 1. Inicializar container
    container = MainContainer()
    await container.init_resources()
    
    # 2. Crear artículo de prueba
    command = CreateArticleCommand(
        title="Test Article for Chunking",
        url="https://example.com/test",
        source_id="test-source-123",
        content="Este es un artículo de prueba con suficiente contenido " * 100,
    )
    
    result = await container.shared.mediator.send(command)
    
    if not result.success:
        print(f"❌ Error creando artículo: {result.error}")
        return
    
    article_id = result.article.id
    print(f"✅ Artículo creado: {article_id}")
    
    # 3. Esperar a que el pipeline complete
    print("⏳ Esperando pipeline de análisis...")
    await asyncio.sleep(10)  # Ajustar según velocidad del sistema
    
    # 4. Verificar que se procesó con AI
    print("🔍 Verificando procesamiento AI...")
    
    # Aquí podrías verificar en DB o logs
    print("✅ Revisa los logs para ver el procesamiento completo")

if __name__ == "__main__":
    asyncio.run(test_full_flow())
```

## Próximos Pasos

Una vez que veas el chunking funcionando:

1. **Verificar embeddings**: Los chunks deben tener vectores de 768 dimensiones
2. **Verificar summaries**: Cada chunk debe tener un summary de 3-5 frases
3. **Verificar persistencia**: Los chunks deben estar en el vector store
4. **Probar búsqueda semántica**: Usar los embeddings para buscar chunks similares
5. **Probar RAG**: Usar los chunks para generar contenido con contexto

## Resumen

✅ **El chunking ESTÁ conectado al flujo**
✅ **Se activa automáticamente** después de ArticleQualityCalculated
✅ **Procesa artículos completos** con chunking → embeddings → summaries
✅ **Persiste en vector store** para búsqueda semántica
✅ **Emite eventos** para coordinación con otros bounded contexts

**Para verlo en acción**: Simplemente crea un artículo o inicia un fetch session, y el pipeline completo se ejecutará automáticamente. Revisa los logs para ver cada paso del procesamiento.
