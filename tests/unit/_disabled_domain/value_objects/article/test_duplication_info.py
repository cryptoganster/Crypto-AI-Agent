"""Unit tests para ArticleDuplicate Value Object."""

import pytest

from src.rss.article.domain.value_objects import RssArticleId
from src.rss.article.domain.value_objects.analysis import (
    RssArticleDuplicate as RssArticleDuplicate,
)


class TestDuplicationInfo:
    """Unit tests para ArticleDuplicate VO."""

    def test_not_duplicate_creates_valid_instance(self):
        """Debería crear instancia para artículo no duplicado."""
        info = RssArticleDuplicate.not_duplicate()

        assert not info.is_duplicate
        assert info.duplicate_of_article_id is None
        assert not info.has_original_reference

    def test_duplicate_of_creates_valid_instance(self):
        """Debería crear instancia para artículo duplicado."""
        article_id = ArticleId.generate()
        info = RssArticleDuplicate.duplicate_of(article_id)

        assert info.is_duplicate
        assert info.duplicate_of_article_id == article_id
        assert info.has_original_reference

    def test_duplicate_of_rejects_none_article_id(self):
        """Debería rechazar article_id None."""
        with pytest.raises(ValueError) as exc_info:
            ArticleDuplicate.duplicate_of(None)  # type: ignore

        assert "article_id no puede ser None" in str(exc_info.value)

    def test_rejects_duplicate_without_article_id(self):
        """Debería rechazar is_duplicate=True sin article_id."""
        with pytest.raises(ValueError) as exc_info:
            RssArticleDuplicate(is_duplicate=True, duplicate_of_article_id=None)

        assert "duplicate_of_article_id es requerido" in str(exc_info.value)

    def test_accepts_not_duplicate_without_article_id(self):
        """Debería aceptar is_duplicate=False sin article_id."""
        info = RssArticleDuplicate(is_duplicate=False, duplicate_of_article_id=None)

        assert not info.is_duplicate
        assert info.duplicate_of_article_id is None

    def test_mark_as_not_duplicate_returns_new_instance(self):
        """Debería retornar nueva instancia marcando como no duplicado."""
        article_id = ArticleId.generate()
        original = RssArticleDuplicate.duplicate_of(article_id)

        reverted = original.mark_as_not_duplicate()

        # Verificar que son instancias diferentes
        assert original is not reverted

        # Verificar que el original no cambió
        assert original.is_duplicate
        assert original.duplicate_of_article_id == article_id

        # Verificar que el nuevo está marcado como no duplicado
        assert not reverted.is_duplicate
        assert reverted.duplicate_of_article_id is None

    def test_mark_as_duplicate_of_returns_new_instance(self):
        """Debería retornar nueva instancia marcando como duplicado."""
        original = RssArticleDuplicate.not_duplicate()
        article_id = ArticleId.generate()

        marked = original.mark_as_duplicate_of(article_id)

        # Verificar que son instancias diferentes
        assert original is not marked

        # Verificar que el original no cambió
        assert not original.is_duplicate

        # Verificar que el nuevo está marcado como duplicado
        assert marked.is_duplicate
        assert marked.duplicate_of_article_id == article_id

    def test_immutability(self):
        """Debería ser inmutable (frozen dataclass)."""
        info = RssArticleDuplicate.not_duplicate()

        with pytest.raises(AttributeError):
            info.is_duplicate = True  # type: ignore

    def test_has_original_reference_true_with_article_id(self):
        """Debería retornar True cuando tiene article_id."""
        article_id = ArticleId.generate()
        info = RssArticleDuplicate.duplicate_of(article_id)

        assert info.has_original_reference

    def test_has_original_reference_false_without_article_id(self):
        """Debería retornar False sin article_id."""
        info = RssArticleDuplicate.not_duplicate()

        assert not info.has_original_reference

    def test_default_values(self):
        """Debería tener valores por defecto correctos."""
        info = RssArticleDuplicate()

        assert not info.is_duplicate
        assert info.duplicate_of_article_id is None
