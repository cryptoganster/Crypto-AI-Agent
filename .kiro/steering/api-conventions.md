# Convenciones de API

## FastAPI y REST

Este proyecto usa **FastAPI** para exponer una API REST.

## Estructura de Endpoints

### Organización

**Ubicación**: `src/presentation/routers/`

```
routers/
├── articles.py      # /api/v1/articles
├── sources.py       # /api/v1/sources
├── fetch.py         # /api/v1/fetch-sessions
└── health.py        # /health, /metrics
```

### Versionado

Usar prefijo `/api/v1/` para todos los endpoints:

```python
from fastapi import APIRouter

router = APIRouter(prefix="/api/v1/articles", tags=["articles"])
```

## Schemas (Request/Response)

**Ubicación**: `src/presentation/schemas/`

### Request Schemas

```python
from pydantic import BaseModel, Field, HttpUrl
from typing import Optional

class CreateArticleRequest(BaseModel):
    """Request schema for creating an article."""
    
    source_id: str = Field(..., description="Source ID")
    title: str = Field(..., min_length=1, max_length=500)
    url: HttpUrl = Field(..., description="Article URL")
    content: str = Field(..., min_length=1)
    
    class Config:
        json_schema_extra = {
            "example": {
                "source_id": "src-123",
                "title": "Example Article",
                "url": "https://example.com/article",
                "content": "Article content here..."
            }
        }

class UpdateArticleRequest(BaseModel):
    """Request schema for updating an article."""
    
    title: Optional[str] = Field(None, min_length=1, max_length=500)
    content: Optional[str] = Field(None, min_length=1)
    quality_score: Optional[float] = Field(None, ge=0.0, le=1.0)
```

### Response Schemas

```python
from datetime import datetime
from pydantic import BaseModel

class ArticleResponse(BaseModel):
    """Response schema for article."""
    
    id: str
    source_id: str
    title: str
    url: str
    content: str
    published_at: datetime
    quality_score: Optional[float]
    status: str
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True  # Para convertir desde ORM models

class PaginatedArticlesResponse(BaseModel):
    """Paginated response for articles."""
    
    items: list[ArticleResponse]
    total: int
    page: int
    page_size: int
    total_pages: int
```

### Error Schemas

```python
class ErrorResponse(BaseModel):
    """Standard error response."""
    
    error: str
    message: str
    details: Optional[dict] = None

class ValidationErrorResponse(BaseModel):
    """Validation error response."""
    
    error: str = "validation_error"
    message: str
    errors: list[dict]
```

## Endpoints

### Naming Conventions

- **Recursos en plural**: `/articles`, `/sources`
- **Kebab-case para multi-palabra**: `/fetch-sessions`
- **IDs en path**: `/articles/{article_id}`
- **Query params para filtros**: `/articles?source_id=123&status=published`

### CRUD Operations

```python
from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import Optional

router = APIRouter(prefix="/api/v1/articles", tags=["articles"])

@router.post(
    "",
    response_model=ArticleResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new article",
    description="Create a new article from provided data"
)
async def create_article(
    request: CreateArticleRequest,
    mediator: IMediator = Depends(get_mediator)
) -> ArticleResponse:
    """Create a new article."""
    command = CreateArticleCommand(
        source_id=request.source_id,
        title=request.title,
        url=str(request.url),
        content=request.content
    )
    
    result = await mediator.send(command)
    
    if not result.success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result.error
        )
    
    return ArticleResponse.from_orm(result.article)

@router.get(
    "",
    response_model=PaginatedArticlesResponse,
    summary="List articles",
    description="Get a paginated list of articles with optional filters"
)
async def list_articles(
    source_id: Optional[str] = Query(None, description="Filter by source ID"),
    status: Optional[str] = Query(None, description="Filter by status"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    query_adapter: IListArticlesQuery = Depends(get_list_articles_query)
) -> PaginatedArticlesResponse:
    """List articles with pagination."""
    offset = (page - 1) * page_size
    
    articles, total = await query_adapter.execute(
        source_id=source_id,
        status=status,
        limit=page_size,
        offset=offset
    )
    
    total_pages = (total + page_size - 1) // page_size
    
    return PaginatedArticlesResponse(
        items=articles,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages
    )

@router.get(
    "/{article_id}",
    response_model=ArticleResponse,
    summary="Get article by ID",
    description="Retrieve a specific article by its ID"
)
async def get_article(
    article_id: str,
    query_adapter: IGetArticleQuery = Depends(get_article_query)
) -> ArticleResponse:
    """Get article by ID."""
    article = await query_adapter.execute(article_id)
    
    if article is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Article {article_id} not found"
        )
    
    return article

@router.put(
    "/{article_id}",
    response_model=ArticleResponse,
    summary="Update article",
    description="Update an existing article"
)
async def update_article(
    article_id: str,
    request: UpdateArticleRequest,
    mediator: IMediator = Depends(get_mediator)
) -> ArticleResponse:
    """Update an article."""
    command = UpdateArticleCommand(
        article_id=article_id,
        title=request.title,
        content=request.content,
        quality_score=request.quality_score
    )
    
    result = await mediator.send(command)
    
    if not result.success:
        if result.error == "not_found":
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Article {article_id} not found"
            )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result.error
        )
    
    return ArticleResponse.from_orm(result.article)

@router.delete(
    "/{article_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete article",
    description="Delete an article by ID"
)
async def delete_article(
    article_id: str,
    mediator: IMediator = Depends(get_mediator)
) -> None:
    """Delete an article."""
    command = DeleteArticleCommand(article_id=article_id)
    result = await mediator.send(command)
    
    if not result.success:
        if result.error == "not_found":
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Article {article_id} not found"
            )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result.error
        )
```

## Status Codes

### Usar códigos apropiados

- **200 OK**: GET exitoso, PUT exitoso
- **201 Created**: POST exitoso (recurso creado)
- **204 No Content**: DELETE exitoso
- **400 Bad Request**: Validación fallida, error de negocio
- **404 Not Found**: Recurso no encontrado
- **409 Conflict**: Conflicto (ej: duplicado)
- **422 Unprocessable Entity**: Error de validación de Pydantic
- **500 Internal Server Error**: Error del servidor

## Error Handling

### Exception Handlers

```python
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from src.domain.shared.exceptions.base import DomainException

app = FastAPI()

@app.exception_handler(DomainException)
async def domain_exception_handler(
    request: Request,
    exc: DomainException
) -> JSONResponse:
    """Handle domain exceptions."""
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={
            "error": exc.__class__.__name__,
            "message": str(exc)
        }
    )

@app.exception_handler(ValueError)
async def value_error_handler(
    request: Request,
    exc: ValueError
) -> JSONResponse:
    """Handle value errors."""
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": "validation_error",
            "message": str(exc)
        }
    )
```

## Dependency Injection

### Usar FastAPI Dependencies

```python
from fastapi import Depends
from dependency_injector.wiring import inject, Provide

from src.bootstrap.containers.application.main import ApplicationContainer
from src.app.interfaces.common.mediator import IMediator

@inject
def get_mediator(
    mediator: IMediator = Depends(Provide[ApplicationContainer.mediator])
) -> IMediator:
    """Get mediator dependency."""
    return mediator

@inject
def get_article_query(
    query: IGetArticleQuery = Depends(
        Provide[ApplicationContainer.get_article_query]
    )
) -> IGetArticleQuery:
    """Get article query dependency."""
    return query

# Uso en endpoint
@router.get("/{article_id}")
async def get_article(
    article_id: str,
    query: IGetArticleQuery = Depends(get_article_query)
):
    return await query.execute(article_id)
```

## Documentación

### OpenAPI/Swagger

FastAPI genera automáticamente documentación OpenAPI.

**Acceso**:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`
- OpenAPI JSON: `http://localhost:8000/openapi.json`

### Mejorar Documentación

```python
from fastapi import FastAPI

app = FastAPI(
    title="Scraping Service API",
    description="API for RSS scraping and content aggregation",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# Tags para agrupar endpoints
tags_metadata = [
    {
        "name": "articles",
        "description": "Operations with articles",
    },
    {
        "name": "sources",
        "description": "Manage RSS sources",
    },
    {
        "name": "fetch",
        "description": "Fetch operations and sessions",
    },
]

app = FastAPI(openapi_tags=tags_metadata)
```

## Middleware

### Logging Middleware

```python
import time
from fastapi import Request
from loguru import logger

@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all HTTP requests."""
    start_time = time.time()
    
    logger.info(
        "Request started",
        method=request.method,
        path=request.url.path,
        client=request.client.host
    )
    
    response = await call_next(request)
    
    duration = time.time() - start_time
    
    logger.info(
        "Request completed",
        method=request.method,
        path=request.url.path,
        status_code=response.status_code,
        duration=f"{duration:.3f}s"
    )
    
    return response
```

### CORS Middleware

```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # En producción: lista específica
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

## Health Checks

```python
from fastapi import APIRouter, status
from pydantic import BaseModel

router = APIRouter(tags=["health"])

class HealthResponse(BaseModel):
    status: str
    version: str
    database: str

@router.get(
    "/health",
    response_model=HealthResponse,
    status_code=status.HTTP_200_OK
)
async def health_check(
    db_session = Depends(get_db_session)
) -> HealthResponse:
    """Health check endpoint."""
    # Check database
    try:
        await db_session.execute("SELECT 1")
        db_status = "healthy"
    except Exception:
        db_status = "unhealthy"
    
    return HealthResponse(
        status="healthy" if db_status == "healthy" else "degraded",
        version="1.0.0",
        database=db_status
    )
```

## Best Practices

1. **Validación en Pydantic**: Usar Field() con constraints
2. **Documentación**: Agregar summary, description, examples
3. **Status Codes**: Usar códigos HTTP apropiados
4. **Error Handling**: Manejar excepciones consistentemente
5. **Dependency Injection**: Usar FastAPI Depends
6. **Async/Await**: Todos los endpoints async
7. **Type Hints**: Siempre usar type hints
8. **Response Models**: Definir response_model en decoradores
