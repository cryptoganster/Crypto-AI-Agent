"""Handler para GenerateContentWithRAG command."""

from datetime import datetime, timezone
from typing import Any, Dict

from src.chunking.domain.interfaces.services import IEmbeddingService
from src.rag.app.commands.generate_content_with_rag.command import (
    GenerateContentWithRAGCommand,
)
from src.rag.app.commands.generate_content_with_rag.result import (
    GenerateContentWithRAGResult,
    GeneratedContent,
)
from src.rag.domain.interfaces.llm_service import ILLMService
from src.rag.domain.services.context_assembly import RAGContextAssemblyService
from src.shared.kernel.logger import ILogger


class GenerateContentWithRAGHandler:
    """
    Handler para generar contenido usando RAG.

    Flujo:
    1. Generar embedding del query
    2. Ensamblar context pack con chunks relevantes
    3. Formatear prompt con contexto
    4. Generar contenido usando LLM
    5. Incluir citaciones de fuentes

    Responsabilidades:
    - Orquestar el flujo de generación RAG
    - Manejar errores en cada paso
    - Logging detallado del proceso
    - Retornar resultado con metadata completa

    Examples:
        >>> handler = GenerateContentWithRAGHandler(
        ...     embedding_service=embedding_service,
        ...     context_assembly_service=context_service,
        ...     llm_service=llm_service,
        ...     logger=logger,
        ... )
        >>> command = GenerateContentWithRAGCommand(
        ...     query="Bitcoin ETF regulation",
        ...     top_k=15,
        ...     content_type="analysis"
        ... )
        >>> result = await handler.handle(command)
        >>> result.success
        True
    """

    def __init__(
        self,
        embedding_service: IEmbeddingService,
        context_assembly_service: RAGContextAssemblyService,
        llm_service: ILLMService,
        logger: ILogger,
    ):
        """
        Inicializa GenerateContentWithRAGHandler.

        Args:
            embedding_service: Servicio para generar embeddings
            context_assembly_service: Servicio para ensamblar context packs
            llm_service: Servicio LLM para generación de texto
            logger: Logger para registrar operaciones
        """
        self._embedding_service = embedding_service
        self._context_assembly = context_assembly_service
        self._llm_service = llm_service
        self._logger = logger.bind(
            layer="application",
            component="GenerateContentWithRAGHandler",
        )

    async def handle(
        self,
        command: GenerateContentWithRAGCommand,
    ) -> GenerateContentWithRAGResult:
        """
        Ejecuta generación de contenido con RAG.

        Args:
            command: Comando con parámetros de generación

        Returns:
            GenerateContentWithRAGResult con contenido generado o error

        Examples:
            >>> command = GenerateContentWithRAGCommand(
            ...     query="Bitcoin regulation impact",
            ...     top_k=10,
            ...     content_type="article"
            ... )
            >>> result = await handler.handle(command)
            >>> if result.success:
            ...     print(result.generated_content.content)
        """
        self._logger.info(
            "Iniciando generación de contenido con RAG",
            query=command.query,
            top_k=command.top_k,
            content_type=command.content_type,
            filters=command.filters,
        )

        try:
            # 1. Generar embedding del query
            self._logger.debug("Generando embedding del query")
            query_embedding = await self._embedding_service.embed_text(command.query)

            # 2. Ensamblar context pack
            self._logger.debug(
                "Ensamblando context pack",
                top_k=command.top_k,
                filters=command.filters,
            )
            context_pack = await self._context_assembly.assemble_context_pack(
                query=command.query,
                query_embedding=query_embedding,
                top_k=command.top_k,
                filters=command.filters,
            )

            self._logger.info(
                "Context pack ensamblado",
                context_pack_id=str(context_pack.id),
                chunk_count=context_pack.get_chunk_count(),
                total_tokens=context_pack.total_tokens,
                source_count=context_pack.get_source_count(),
            )

            # 3. Formatear prompt con contexto
            prompt = self._format_rag_prompt(
                query=command.query,
                context_pack_metadata=await self._context_assembly.get_context_pack_summary(
                    context_pack
                ),
                content_type=command.content_type,
            )

            # 4. Generar contenido usando LLM
            self._logger.debug(
                "Generando contenido con LLM",
                max_tokens=command.max_tokens,
                temperature=command.temperature,
            )

            system_prompt = self._get_system_prompt(command.content_type)

            generated_text = await self._llm_service.generate(
                prompt=prompt,
                max_tokens=command.max_tokens,
                temperature=command.temperature,
                system_prompt=system_prompt,
            )

            # 5. Crear resultado con metadata
            generated_content = GeneratedContent(
                content=generated_text,
                sources=context_pack.sources,
                chunk_ids=[str(cid) for cid in context_pack.chunk_ids],
                relevance_scores=context_pack.relevance_scores,
                tokens_used=command.max_tokens,  # Aproximación
                model="gpt-4",  # TODO: Obtener del LLM service
                generated_at=datetime.now(timezone.utc),
            )

            self._logger.info(
                "Contenido generado exitosamente",
                query=command.query,
                content_length=len(generated_text),
                sources_count=len(context_pack.sources),
                chunks_used=context_pack.get_chunk_count(),
            )

            return GenerateContentWithRAGResult.success_result(
                generated_content=generated_content,
                context_pack_id=str(context_pack.id),
                query=command.query,
            )

        except ValueError as e:
            self._logger.error(
                "Error de validación en generación RAG",
                error=str(e),
                query=command.query,
            )
            return GenerateContentWithRAGResult.failure(
                error=f"Error de validación: {str(e)}",
                query=command.query,
            )

        except Exception as e:
            self._logger.error(
                "Error inesperado en generación RAG",
                error=str(e),
                error_type=type(e).__name__,
                query=command.query,
            )
            return GenerateContentWithRAGResult.failure(
                error=f"Error generando contenido: {str(e)}",
                query=command.query,
            )

    def _format_rag_prompt(
        self,
        query: str,
        context_pack_metadata: Dict[str, Any],
        content_type: str,
    ) -> str:
        """
        Formatea prompt RAG con contexto recuperado.

        Args:
            query: Query original
            context_pack_metadata: Metadata del context pack
            content_type: Tipo de contenido a generar

        Returns:
            Prompt formateado para el LLM
        """
        # Obtener instrucciones específicas por tipo de contenido
        content_instructions = self._get_content_type_instructions(content_type)

        prompt = f"""Usa el siguiente contexto recuperado para responder la consulta.

        CONSULTA: {query}

        CONTEXTO RECUPERADO:
        - Chunks relevantes: {context_pack_metadata['chunk_count']}
        - Fuentes: {context_pack_metadata['source_count']}
        - Relevancia promedio: {context_pack_metadata['average_relevance']:.2f}

        INSTRUCCIONES:
        {content_instructions}

        REGLAS IMPORTANTES:
        1. Basa tu respuesta EXCLUSIVAMENTE en la información del contexto
        2. NO inventes información que no esté en el contexto
        3. Si el contexto no tiene suficiente información, indícalo claramente
        4. Cita las fuentes cuando uses información específica
        5. Mantén un tono profesional y objetivo

        FUENTES DISPONIBLES:
        {self._format_sources(context_pack_metadata['sources'])}

        Genera el contenido ahora:"""

        return prompt

    def _get_system_prompt(self, content_type: str) -> str:
        """
        Obtiene system prompt según tipo de contenido.

        Args:
            content_type: Tipo de contenido

        Returns:
            System prompt apropiado
        """
        system_prompts = {
            "article": "Eres un periodista experto en criptomonedas que escribe artículos informativos basados en fuentes verificadas.",
            "analysis": "Eres un analista financiero experto en criptomonedas que genera análisis profundos basados en datos.",
            "newsletter": "Eres un editor de newsletter que crea resúmenes concisos y atractivos de noticias cripto.",
            "summary": "Eres un experto en resumir información compleja de forma clara y concisa.",
            "report": "Eres un analista que genera reportes técnicos detallados basados en investigación.",
        }

        return system_prompts.get(
            content_type,
            "Eres un experto en criptomonedas que genera contenido basado en fuentes verificadas.",
        )

    def _get_content_type_instructions(self, content_type: str) -> str:
        """
        Obtiene instrucciones específicas por tipo de contenido.

        Args:
            content_type: Tipo de contenido

        Returns:
            Instrucciones específicas
        """
        instructions = {
            "article": """Genera un artículo completo con:
            - Título atractivo
            - Introducción que contextualice el tema
            - Desarrollo con información del contexto
            - Conclusión con implicaciones
            - Citas de fuentes específicas""",
            "analysis": """Genera un análisis profundo con:
            - Resumen ejecutivo
            - Análisis de tendencias y patrones
            - Impacto en el mercado
            - Riesgos y oportunidades
            - Conclusiones basadas en datos""",
            "newsletter": """Genera un newsletter con:
            - Título llamativo
            - 3-5 puntos clave (bullets)
            - Contexto breve de cada punto
            - Llamado a la acción o conclusión
            - Tono conversacional pero profesional""",
            "summary": """Genera un resumen con:
            - Puntos principales del contexto
            - Información crítica preservada
            - Formato claro y escaneable
            - Máximo 5 párrafos""",
            "report": """Genera un reporte técnico con:
            - Executive summary
            - Metodología (fuentes usadas)
            - Hallazgos principales
            - Análisis detallado
            - Recomendaciones""",
        }

        return instructions.get(
            content_type,
            "Genera contenido informativo y bien estructurado basado en el contexto.",
        )

    def _format_sources(self, sources: list[str]) -> str:
        """
        Formatea lista de fuentes para el prompt.

        Args:
            sources: Lista de URLs de fuentes

        Returns:
            Fuentes formateadas
        """
        if not sources:
            return "No hay fuentes disponibles"

        formatted = []
        for i, source in enumerate(sources[:10], 1):  # Limitar a 10 fuentes
            formatted.append(f"{i}. {source}")

        if len(sources) > 10:
            formatted.append(f"... y {len(sources) - 10} fuentes más")

        return "\n".join(formatted)
