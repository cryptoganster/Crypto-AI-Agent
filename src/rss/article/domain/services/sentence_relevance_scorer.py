"""Domain Service para scoring de relevancia de oraciones."""

import re
from dataclasses import dataclass
from typing import List, Tuple


@dataclass
class ScoredSentence:
    """Representa una oración con su score de relevancia."""

    text: str
    score: float
    position: int  # Posición original en el texto


class SentenceRelevanceScorer:
    """
    Domain Service para calcular relevancia de oraciones.

    Responsabilidades:
    - Calcular score de relevancia para cada oración
    - Aplicar heurísticas de extractive summarization
    - Identificar oraciones más importantes del contenido

    PURE DOMAIN SERVICE: Sin dependencias externas, solo lógica de scoring.

    Algoritmo de Scoring:
    - Posición: Oraciones al inicio tienen mayor peso
    - Longitud: Oraciones de longitud media son preferidas
    - Palabras clave: Presencia de términos importantes
    - Puntuación: Oraciones con puntuación fuerte (. ! ?) son preferidas
    """

    # Pesos para diferentes factores de scoring
    POSITION_WEIGHT = 0.3
    LENGTH_WEIGHT = 0.2
    KEYWORD_WEIGHT = 0.3
    PUNCTUATION_WEIGHT = 0.2

    # Longitud óptima de oración (en palabras)
    OPTIMAL_SENTENCE_LENGTH = 15
    MIN_SENTENCE_LENGTH = 5
    MAX_SENTENCE_LENGTH = 40

    def __init__(self, keywords: List[str] = None):
        """
        Inicializa el scorer.

        Args:
            keywords: Lista opcional de palabras clave para aumentar relevancia
        """
        self.keywords = [k.lower() for k in (keywords or [])]

    def score_sentences(self, sentences: List[str]) -> List[ScoredSentence]:
        """
        Calcula score de relevancia para cada oración.

        Args:
            sentences: Lista de oraciones a evaluar

        Returns:
            Lista de ScoredSentence ordenadas por score (mayor a menor)
        """
        if not sentences:
            return []

        scored = []
        total_sentences = len(sentences)

        for position, sentence in enumerate(sentences):
            # Calcular componentes del score
            position_score = self._calculate_position_score(position, total_sentences)
            length_score = self._calculate_length_score(sentence)
            keyword_score = self._calculate_keyword_score(sentence)
            punctuation_score = self._calculate_punctuation_score(sentence)

            # Score final ponderado
            final_score = (
                position_score * self.POSITION_WEIGHT
                + length_score * self.LENGTH_WEIGHT
                + keyword_score * self.KEYWORD_WEIGHT
                + punctuation_score * self.PUNCTUATION_WEIGHT
            )

            scored.append(
                ScoredSentence(text=sentence, score=final_score, position=position)
            )

        # Ordenar por score descendente
        scored.sort(key=lambda x: x.score, reverse=True)

        return scored

    def select_top_sentences(
        self, scored_sentences: List[ScoredSentence], max_length: int
    ) -> List[str]:
        """
        Selecciona las mejores oraciones hasta llenar max_length.

        Mantiene el orden original de las oraciones en el texto.

        Args:
            scored_sentences: Oraciones con scores
            max_length: Longitud máxima del resumen en caracteres

        Returns:
            Lista de oraciones seleccionadas en orden original
        """
        if not scored_sentences:
            return []

        # Seleccionar oraciones hasta llenar max_length
        selected = []
        current_length = 0

        for scored in scored_sentences:
            sentence_length = len(scored.text)

            # Calcular longitud con espacio si no es la primera
            space_length = 1 if selected else 0
            total_needed = sentence_length + space_length

            # Verificar si cabe
            if current_length + total_needed <= max_length:
                selected.append(scored)
                current_length += total_needed
            elif not selected:
                # Si ninguna oración cabe, no agregar nada (respetar max_length)
                break

        # Ordenar por posición original para mantener coherencia
        selected.sort(key=lambda x: x.position)

        return [s.text for s in selected]

    def _calculate_position_score(self, position: int, total: int) -> float:
        """
        Calcula score basado en posición.

        Oraciones al inicio tienen mayor relevancia (pirámide invertida).
        """
        if total == 1:
            return 1.0

        # Score decreciente: primera oración = 1.0, última = 0.0
        return 1.0 - (position / (total - 1))

    def _calculate_length_score(self, sentence: str) -> float:
        """
        Calcula score basado en longitud.

        Oraciones de longitud media son preferidas.
        Muy cortas o muy largas tienen menor score.
        """
        words = sentence.split()
        word_count = len(words)

        if word_count < self.MIN_SENTENCE_LENGTH:
            # Penalizar oraciones muy cortas
            return word_count / self.MIN_SENTENCE_LENGTH * 0.5

        if word_count > self.MAX_SENTENCE_LENGTH:
            # Penalizar oraciones muy largas
            return 1.0 - (
                (word_count - self.MAX_SENTENCE_LENGTH) / self.MAX_SENTENCE_LENGTH
            )

        # Score óptimo para longitud media
        distance_from_optimal = abs(word_count - self.OPTIMAL_SENTENCE_LENGTH)
        max_distance = self.OPTIMAL_SENTENCE_LENGTH

        return 1.0 - (distance_from_optimal / max_distance)

    def _calculate_keyword_score(self, sentence: str) -> float:
        """
        Calcula score basado en presencia de palabras clave.

        Más keywords = mayor relevancia.
        """
        if not self.keywords:
            # Sin keywords configuradas, score neutral
            return 0.5

        sentence_lower = sentence.lower()

        # Contar keywords presentes
        keyword_count = sum(1 for keyword in self.keywords if keyword in sentence_lower)

        if keyword_count == 0:
            return 0.0

        # Normalizar por número total de keywords
        return min(1.0, keyword_count / len(self.keywords))

    def _calculate_punctuation_score(self, sentence: str) -> float:
        """
        Calcula score basado en puntuación.

        Oraciones con puntuación fuerte (. ! ?) son preferidas.
        """
        sentence = sentence.strip()

        if not sentence:
            return 0.0

        # Puntuación fuerte al final
        if sentence.endswith((".", "!", "?")):
            return 1.0

        # Puntuación débil o sin puntuación
        if sentence.endswith((",", ";", ":")):
            return 0.5

        return 0.3
