# File and Class Mapping: source/ + article/ → rss/

## Overview

Este documento proporciona el mapeo completo de archivos y clases desde los bounded contexts `source/` y `article/` hacia la nueva estructura `src/rss/feed/` y `src/rss/article/`.

## Quick Reference

### Path Changes
```
src/source/          → src/rss/feed/
src/article/         → src/rss/article/
```

### Class Name Patterns
```
Source*              → RssFeed*
Article*             → RssArticle*
ISource*             → IRssFeed*
IArticle*            → IRssArticle*
*Source*             → *RssFeed*
*Article*            → *RssArticle*
```

## Part 1: Source → RssFeed Migration

### 1.1 Aggregates

| Old Path | New Path | Old Class | New Class |
|----------|----------|-----------|-----------|
| `src/source/domain/aggregates/source.py` | `src/rss/feed/domain/aggregates/rss_feed.py` | `Source` | `RssFeed` |

### 1.2 Value Objects

| Old Path | New Path | Old Class | New Class |
|----------|----------|-----------|-----------|
| `src/source/domain/value_objects/id.py` | `src/rss/feed/domain/value_objects/rss_feed_id.py` | `SourceId` | `RssFeedId` |
| `src/source/domain/value_objects/url.py` | `src/rss/feed/domain/value_objects/rss_feed_url.py` | `SourceUrl` | `RssFeedUrl` |
| `src/source/domain/value_objects/name.py` | `src/rss/feed/domain/value_objects/rss_feed_name.py` | `SourceName` | `RssFeedName` |
| `src/source/domain/value_objects/description.py` | `src/rss/feed/domain/value_objects/rss_feed_description.py` | `SourceDescription` | `RssFeedDescription` |
| `src/source/domain/value_objects/status.py` | `src/rss/feed/domain/value_objects/rss_feed_status.py` | `SourceStatus` | `RssFeedStatus` |
| `src/source/domain/value_objects/configuration.py` | `src/rss/feed/domain/value_objects/rss_feed_configuration.py` | `SourceConfiguration` | `RssFeedConfiguration` |
| `src/source/domain/value_objects/metrics.py` | `src/rss/feed/domain/value_objects/rss_feed_metrics.py` | `SourceMetrics` | `RssFeedMetrics` |
| `src/source/domain/value_objects/source_health.py` | `src/rss/feed/domain/value_objects/rss_feed_health.py` | `SourceHealth` | `RssFeedHealth` |
| `src/source/domain/value_objects/source_identity.py` | `src/rss/feed/domain/value_objects/rss_feed_identity.py` | `SourceIdentity` | `RssFeedIdentity` |
| `src/source/domain/value_objects/source_metadata.py` | `src/rss/feed/domain/value_objects/rss_feed_metadata.py` | `SourceMetadata` | `RssFeedMetadata` |

### 1.3 Domain Events

| Old Path | New Path | Old Class | New Class |
|----------|----------|-----------|-----------|
| `src/source/domain/events/created.py` | `src/rss/feed/domain/events/rss_feed_created.py` | `SourceCreated` | `RssFeedCreated` |
| `src/source/domain/events/activated.py` | `src/rss/feed/domain/events/rss_feed_activated.py` | `SourceActivated` | `RssFeedActivated` |
| `src/source/domain/events/deactivated.py` | `src/rss/feed/domain/events/rss_feed_deactivated.py` | `SourceDeactivated` | `RssFeedDeactivated` |
| `src/source/domain/events/added.py` | `src/rss/feed/domain/events/rss_feed_added.py` | `SourceAdded` | `RssFeedAdded` |
| `src/source/domain/events/removed.py` | `src/rss/feed/domain/events/rss_feed_removed.py` | `SourceRemoved` | `RssFeedRemoved` |
| `src/source/domain/events/configuration_updated.py` | `src/rss/feed/domain/events/rss_feed_configuration_updated.py` | `SourceConfigurationUpdated` | `RssFeedConfigurationUpdated` |
| `src/source/domain/events/fetch_started.py` | `src/rss/feed/domain/events/rss_feed_fetch_started.py` | `SourceFetchStarted` | `RssFeedFetchStarted` |
| `src/source/domain/events/fetch_stopped.py` | `src/rss/feed/domain/events/rss_feed_fetch_stopped.py` | `SourceFetchStopped` | `RssFeedFetchStopped` |
| `src/source/domain/events/fetched.py` | `src/rss/feed/domain/events/rss_feed_fetched.py` | `SourceFetched` | `RssFeedFetched` |
| `src/source/domain/events/health_degraded.py` | `src/rss/feed/domain/events/rss_feed_health_degraded.py` | `SourceHealthDegraded` | `RssFeedHealthDegraded` |
| `src/source/domain/events/health_recovered.py` | `src/rss/feed/domain/events/rss_feed_health_recovered.py` | `SourceHealthRecovered` | `RssFeedHealthRecovered` |
| `src/source/domain/events/metrics_updated.py` | `src/rss/feed/domain/events/rss_feed_metrics_updated.py` | `SourceMetricsUpdated` | `RssFeedMetricsUpdated` |
| `src/source/domain/events/status_changed.py` | `src/rss/feed/domain/events/rss_feed_status_changed.py` | `SourceStatusChanged` | `RssFeedStatusChanged` |

### 1.4 Commands

| Old Path | New Path | Old Command | New Command |
|----------|----------|-------------|-------------|
| `src/source/app/commands/create_source/` | `src/rss/feed/app/commands/create_rss_feed/` | `CreateSourceCommand` | `CreateRssFeedCommand` |
| `src/source/app/commands/update_source/` | `src/rss/feed/app/commands/update_rss_feed/` | `UpdateSourceCommand` | `UpdateRssFeedCommand` |
| `src/source/app/commands/activate_source/` | `src/rss/feed/app/commands/activate_rss_feed/` | `ActivateSourceCommand` | `ActivateRssFeedCommand` |
| `src/source/app/commands/remove_source/` | `src/rss/feed/app/commands/remove_rss_feed/` | `RemoveSourceCommand` | `RemoveRssFeedCommand` |

### 1.5 Repositories

| Old Path | New Path | Old Interface | New Interface |
|----------|----------|---------------|---------------|
| `src/source/domain/interfaces/repositories/source_read_repository.py` | `src/rss/feed/domain/interfaces/repositories/rss_feed_read_repository.py` | `ISourceReadRepository` | `IRssFeedReadRepository` |
| `src/source/domain/interfaces/repositories/source_write_repository.py` | `src/rss/feed/domain/interfaces/repositories/rss_feed_write_repository.py` | `ISourceWriteRepository` | `IRssFeedWriteRepository` |
| `src/source/infra/persistence/repositories/source_read_repository.py` | `src/rss/feed/infra/persistence/repositories/rss_feed_read_repository.py` | `SqlAlchemySourceReadRepository` | `SqlAlchemyRssFeedReadRepository` |
| `src/source/infra/persistence/repositories/source_write_repository.py` | `src/rss/feed/infra/persistence/repositories/rss_feed_write_repository.py` | `SqlAlchemySourceWriteRepository` | `SqlAlchemyRssFeedWriteRepository` |

### 1.6 Factories

| Old Path | New Path | Old Class | New Class |
|----------|----------|-----------|-----------|
| `src/source/domain/factories/source_factory.py` | `src/rss/feed/domain/factories/rss_feed_factory.py` | `SourceFactory` | `RssFeedFactory` |

### 1.7 Services

| Old Path | New Path | Old Class | New Class |
|----------|----------|-----------|-----------|
| `src/source/domain/services/health.py` | `src/rss/feed/domain/services/rss_feed_health.py` | `SourceHealthService` | `RssFeedHealthService` |
| `src/source/domain/services/validation.py` | `src/rss/feed/domain/services/rss_feed_validation.py` | `SourceValidationService` | `RssFeedValidationService` |
| `src/source/domain/services/similarity.py` | `src/rss/feed/domain/services/rss_feed_similarity.py` | `SourceSimilarityService` | `RssFeedSimilarityService` |
| `src/source/domain/services/metrics_calculation.py` | `src/rss/feed/domain/services/rss_feed_metrics_calculation.py` | `SourceMetricsCalculationService` | `RssFeedMetricsCalculationService` |

### 1.8 ORM Models

| Old Path | New Path | Old Model | New Model | Old Table | New Table |
|----------|----------|-----------|-----------|-----------|-----------|
| `src/source/infra/persistence/models/source_model.py` | `src/rss/feed/infra/persistence/models/rss_feed_model.py` | `SourceModel` | `RssFeedModel` | `sources` | `rss_feeds` |

### 1.9 Mappers

| Old Path | New Path | Old Class | New Class |
|----------|----------|-----------|-----------|
| `src/source/infra/persistence/mappers/source_mapper.py` | `src/rss/feed/infra/persistence/mappers/rss_feed_mapper.py` | `SourceMapper` | `RssFeedMapper` |

### 1.10 Container

| Old Path | New Path | Old Class | New Class |
|----------|----------|-----------|-----------|
| `src/source/container.py` | `src/rss/feed/container.py` | `SourceContainer` | `RssFeedContainer` |

## Part 2: Article → RssArticle Migration

### 2.1 Aggregates

| Old Path | New Path | Old Class | New Class |
|----------|----------|-----------|-----------|
| `src/article/domain/aggregates/article.py` | `src/rss/article/domain/aggregates/rss_article.py` | `Article` | `RssArticle` |

### 2.2 Value Objects (Core)

| Old Path | New Path | Old Class | New Class |
|----------|----------|-----------|-----------|
| `src/article/domain/value_objects/metadata/article_id.py` | `src/rss/article/domain/value_objects/metadata/rss_article_id.py` | `ArticleId` | `RssArticleId` |
| `src/article/domain/value_objects/metadata/article_url.py` | `src/rss/article/domain/value_objects/metadata/rss_article_url.py` | `ArticleUrl` | `RssArticleUrl` |
| `src/article/domain/value_objects/metadata/article_title.py` | `src/rss/article/domain/value_objects/metadata/rss_article_title.py` | `ArticleTitle` | `RssArticleTitle` |
| `src/article/domain/value_objects/metadata/article_author.py` | `src/rss/article/domain/value_objects/metadata/rss_article_author.py` | `ArticleAuthor` | `RssArticleAuthor` |
| `src/article/domain/value_objects/metadata/article_pub_date.py` | `src/rss/article/domain/value_objects/metadata/rss_article_pub_date.py` | `ArticlePubDate` | `RssArticlePubDate` |
| `src/article/domain/value_objects/content/article_content.py` | `src/rss/article/domain/value_objects/content/rss_article_content.py` | `ArticleContent` | `RssArticleContent` |
| `src/article/domain/value_objects/content/article_summary.py` | `src/rss/article/domain/value_objects/content/rss_article_summary.py` | `ArticleSummary` | `RssArticleSummary` |

### 2.3 Domain Events (Key Events)

| Old Path | New Path | Old Class | New Class |
|----------|----------|-----------|-----------|
| `src/article/domain/events/article_created.py` | `src/rss/article/domain/events/rss_article_created.py` | `ArticleCreated` | `RssArticleCreated` |
| `src/article/domain/events/article_content_scraped.py` | `src/rss/article/domain/events/rss_article_content_scraped.py` | `ArticleContentScraped` | `RssArticleContentScraped` |
| `src/article/domain/events/article_plaintext_extracted.py` | `src/rss/article/domain/events/rss_article_plaintext_extracted.py` | `ArticlePlaintextExtracted` | `RssArticlePlaintextExtracted` |
| `src/article/domain/events/article_markdown_converted.py` | `src/rss/article/domain/events/rss_article_markdown_converted.py` | `ArticleMarkdownConverted` | `RssArticleMarkdownConverted` |
| `src/article/domain/events/article_metrics_calculated.py` | `src/rss/article/domain/events/rss_article_metrics_calculated.py` | `ArticleMetricsCalculated` | `RssArticleMetricsCalculated` |
| `src/article/domain/events/article_language_detected.py` | `src/rss/article/domain/events/rss_article_language_detected.py` | `ArticleLanguageDetected` | `RssArticleLanguageDetected` |
| `src/article/domain/events/article_summary_generated.py` | `src/rss/article/domain/events/rss_article_summary_generated.py` | `ArticleSummaryGenerated` | `RssArticleSummaryGenerated` |
| `src/article/domain/events/article_keywords_extracted.py` | `src/rss/article/domain/events/rss_article_keywords_extracted.py` | `ArticleKeywordsExtracted` | `RssArticleKeywordsExtracted` |
| `src/article/domain/events/article_quality_calculated.py` | `src/rss/article/domain/events/rss_article_quality_calculated.py` | `ArticleQualityCalculated` | `RssArticleQualityCalculated` |
| `src/article/domain/events/article_published.py` | `src/rss/article/domain/events/rss_article_published.py` | `ArticlePublished` | `RssArticlePublished` |

### 2.4 Commands (Key Commands)

| Old Path | New Path | Old Command | New Command |
|----------|----------|-------------|-------------|
| `src/article/app/commands/scrape_article_content/` | `src/rss/article/app/commands/scrape_rss_article_content/` | `ScrapeArticleContentCommand` | `ScrapeRssArticleContentCommand` |
| `src/article/app/commands/extract_article_plaintext/` | `src/rss/article/app/commands/extract_rss_article_plaintext/` | `ExtractArticlePlaintextCommand` | `ExtractRssArticlePlaintextCommand` |
| `src/article/app/commands/convert_article_to_markdown/` | `src/rss/article/app/commands/convert_rss_article_to_markdown/` | `ConvertArticleToMarkdownCommand` | `ConvertRssArticleToMarkdownCommand` |
| `src/article/app/commands/calculate_article_metrics/` | `src/rss/article/app/commands/calculate_rss_article_metrics/` | `CalculateArticleMetricsCommand` | `CalculateRssArticleMetricsCommand` |
| `src/article/app/commands/detect_article_language/` | `src/rss/article/app/commands/detect_rss_article_language/` | `DetectArticleLanguageCommand` | `DetectRssArticleLanguageCommand` |
| `src/article/app/commands/generate_article_summary/` | `src/rss/article/app/commands/generate_rss_article_summary/` | `GenerateArticleSummaryCommand` | `GenerateRssArticleSummaryCommand` |
| `src/article/app/commands/extract_article_keywords/` | `src/rss/article/app/commands/extract_rss_article_keywords/` | `ExtractArticleKeywordsCommand` | `ExtractRssArticleKeywordsCommand` |
| `src/article/app/commands/calculate_article_quality/` | `src/rss/article/app/commands/calculate_rss_article_quality/` | `CalculateArticleQualityCommand` | `CalculateRssArticleQualityCommand` |

### 2.5 Queries

| Old Path | New Path | Old Query | New Query |
|----------|----------|-----------|-----------|
| `src/article/app/queries/get_article_by_id/` | `src/rss/article/app/queries/get_rss_article_by_id/` | `GetArticleByIdQuery` | `GetRssArticleByIdQuery` |
| `src/article/app/queries/get_pending_articles/` | `src/rss/article/app/queries/get_pending_rss_articles/` | `GetPendingArticlesQuery` | `GetPendingRssArticlesQuery` |
| `src/article/app/queries/get_stats/` | `src/rss/article/app/queries/get_rss_article_stats/` | `GetArticleStatsQuery` | `GetRssArticleStatsQuery` |

### 2.6 Repositories

| Old Path | New Path | Old Interface | New Interface |
|----------|----------|---------------|---------------|
| `src/article/domain/interfaces/repositories/article_read_repository.py` | `src/rss/article/domain/interfaces/repositories/rss_article_read_repository.py` | `IArticleReadRepository` | `IRssArticleReadRepository` |
| `src/article/domain/interfaces/repositories/article_write_repository.py` | `src/rss/article/domain/interfaces/repositories/rss_article_write_repository.py` | `IArticleWriteRepository` | `IRssArticleWriteRepository` |
| `src/article/infra/persistence/repositories/article_read_repository.py` | `src/rss/article/infra/persistence/repositories/rss_article_read_repository.py` | `SqlAlchemyArticleReadRepository` | `SqlAlchemyRssArticleReadRepository` |
| `src/article/infra/persistence/repositories/article_write_repository.py` | `src/rss/article/infra/persistence/repositories/rss_article_write_repository.py` | `SqlAlchemyArticleWriteRepository` | `SqlAlchemyRssArticleWriteRepository` |

### 2.7 Factories

| Old Path | New Path | Old Class | New Class |
|----------|----------|-----------|-----------|
| `src/article/domain/factories/article_factory.py` | `src/rss/article/domain/factories/rss_article_factory.py` | `ArticleFactory` | `RssArticleFactory` |

### 2.8 Services

| Old Path | New Path | Old Class | New Class |
|----------|----------|-----------|-----------|
| `src/article/domain/services/content_extraction.py` | `src/rss/article/domain/services/rss_article_content_extraction.py` | `ArticleContentExtractionService` | `RssArticleContentExtractionService` |
| `src/article/domain/services/language_detection.py` | `src/rss/article/domain/services/rss_article_language_detection.py` | `ArticleLanguageDetectionService` | `RssArticleLanguageDetectionService` |
| `src/article/domain/services/metrics_calculation.py` | `src/rss/article/domain/services/rss_article_metrics_calculation.py` | `ArticleMetricsCalculationService` | `RssArticleMetricsCalculationService` |
| `src/article/domain/services/summary_extraction.py` | `src/rss/article/domain/services/rss_article_summary_extraction.py` | `ArticleSummaryExtractionService` | `RssArticleSummaryExtractionService` |

### 2.9 Process Managers

| Old Path | New Path | Old Class | New Class |
|----------|----------|-----------|-----------|
| `src/article/app/process_managers/content_extraction_pipeline.py` | `src/rss/article/app/process_managers/rss_article_content_extraction_pipeline.py` | `ArticleContentExtractionPipeline` | `RssArticleContentExtractionPipeline` |
| `src/article/app/process_managers/content_analysis_pipeline.py` | `src/rss/article/app/process_managers/rss_article_content_analysis_pipeline.py` | `ArticleContentAnalysisPipeline` | `RssArticleContentAnalysisPipeline` |

### 2.10 ORM Models

| Old Path | New Path | Old Model | New Model | Old Table | New Table |
|----------|----------|-----------|-----------|-----------|-----------|
| `src/article/infra/persistence/models/article_model.py` | `src/rss/article/infra/persistence/models/rss_article_model.py` | `ArticleModel` | `RssArticleModel` | `articles` | `rss_articles` |

### 2.11 Mappers

| Old Path | New Path | Old Class | New Class |
|----------|----------|-----------|-----------|
| `src/article/infra/persistence/mappers/article_mapper.py` | `src/rss/article/infra/persistence/mappers/rss_article_mapper.py` | `ArticleMapper` | `RssArticleMapper` |

### 2.12 Container

| Old Path | New Path | Old Class | New Class |
|----------|----------|-----------|-----------|
| `src/article/container.py` | `src/rss/article/container.py` | `ArticleContainer` | `RssArticleContainer` |

## Part 3: Cross-BC Updates

### 3.1 Knowledge BC (formerly Chunking)

#### SourceReference Value Object (NEW)

| Path | Class | Description |
|------|-------|-------------|
| `src/knowledge/domain/value_objects/source_reference.py` | `SourceReference` | Generic reference to content source (rss_article, tweet, pdf, etc.) |

#### KnowledgeChunk Updates

| Old Property | New Property | Type Change |
|--------------|--------------|-------------|
| `article_id: str` | `source: SourceReference` | Changed from string to SourceReference VO |

### 3.2 RAG BC

All imports of `Article` and `Source` need to be updated to use new paths:

```python
# Old
from src.article.domain.aggregates.article import Article
from src.source.domain.aggregates.source import Source

# New
from src.rss.article.domain.aggregates.rss_article import RssArticle
from src.rss.feed.domain.aggregates.rss_feed import RssFeed
```

## Part 4: Import Pattern Changes

### 4.1 Source/Feed Imports

```python
# OLD IMPORTS
from src.source.domain.aggregates.source import Source
from src.source.domain.value_objects.id import SourceId
from src.source.domain.events.created import SourceCreated
from src.source.app.commands.create_source.command import CreateSourceCommand
from src.source.domain.interfaces.repositories.source_read_repository import ISourceReadRepository

# NEW IMPORTS
from src.rss.feed.domain.aggregates.rss_feed import RssFeed
from src.rss.feed.domain.value_objects.rss_feed_id import RssFeedId
from src.rss.feed.domain.events.rss_feed_created import RssFeedCreated
from src.rss.feed.app.commands.create_rss_feed.command import CreateRssFeedCommand
from src.rss.feed.domain.interfaces.repositories.rss_feed_read_repository import IRssFeedReadRepository
```

### 4.2 Article Imports

```python
# OLD IMPORTS
from src.article.domain.aggregates.article import Article
from src.article.domain.value_objects.metadata.article_id import ArticleId
from src.article.domain.events.article_created import ArticleCreated
from src.article.app.commands.scrape_article_content.command import ScrapeArticleContentCommand
from src.article.domain.interfaces.repositories.article_read_repository import IArticleReadRepository

# NEW IMPORTS
from src.rss.article.domain.aggregates.rss_article import RssArticle
from src.rss.article.domain.value_objects.metadata.rss_article_id import RssArticleId
from src.rss.article.domain.events.rss_article_created import RssArticleCreated
from src.rss.article.app.commands.scrape_rss_article_content.command import ScrapeRssArticleContentCommand
from src.rss.article.domain.interfaces.repositories.rss_article_read_repository import IRssArticleReadRepository
```

## Part 5: Test File Mappings

### 5.1 Source/Feed Tests

```
tests/unit/source/                    → tests/unit/rss/feed/
tests/integration/source/             → tests/integration/rss/feed/
tests/pbt/test_source_properties.py   → tests/pbt/test_rss_feed_properties.py
```

### 5.2 Article Tests

```
tests/unit/article/                   → tests/unit/rss/article/
tests/integration/article/            → tests/integration/rss/article/
tests/pbt/test_article_properties.py  → tests/pbt/test_rss_article_properties.py
```

## Part 6: Database Migration

### 6.1 Table Renames

```sql
-- Rename tables
ALTER TABLE sources RENAME TO rss_feeds;
ALTER TABLE articles RENAME TO rss_articles;

-- Update foreign keys
ALTER TABLE rss_articles 
  RENAME COLUMN source_id TO feed_id;

-- Update indexes
ALTER INDEX idx_articles_source_id 
  RENAME TO idx_rss_articles_feed_id;
```

## Summary

### Total Changes

- **Files Renamed**: ~230 files
- **Classes Renamed**: ~160 classes
- **Directories Moved**: 2 bounded contexts
- **Import Statements Updated**: ~500+ imports
- **Test Files Updated**: ~100 test files
- **Database Tables Renamed**: 2 tables

### Verification Commands

```bash
# Verify no old imports remain
grep -r "from src.source" src/ tests/
grep -r "from src.article" src/ tests/

# Verify new imports work
python -c "from src.rss.feed.domain.aggregates.rss_feed import RssFeed; print('✓ RssFeed')"
python -c "from src.rss.article.domain.aggregates.rss_article import RssArticle; print('✓ RssArticle')"
python -c "from src.knowledge.domain.value_objects.source_reference import SourceReference; print('✓ SourceReference')"

# Run all tests
pytest tests/ -v
```

## Notes

1. **Incremental Migration**: Migrate one BC at a time (Feed first, then Article)
2. **Test After Each Step**: Run tests after each major change
3. **Keep Old Files**: Mark as DEPRECATED but keep until migration is complete
4. **Update Documentation**: Update architecture docs as you go
5. **Database Migration**: Create Alembic migration for table renames

---

**Last Updated**: 2024-12-13
**Migration Status**: Specification Complete, Ready for Implementation
