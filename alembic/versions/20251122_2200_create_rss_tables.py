"""Create RSS tables

Revision ID: 20251122_2200
Revises: 
Create Date: 2025-11-22 22:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '20251122_2200'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create RSS-related tables."""
    
    # Create sources table (matching SourceModel schema)
    op.create_table(
        'sources',
        sa.Column('source_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('url', sa.Text(), nullable=False),
        sa.Column('domain', sa.String(100), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('status', sa.String(20), nullable=False, server_default='inactive'),
        sa.Column('fetch_interval_minutes', sa.Integer(), nullable=False, server_default='360'),
        sa.Column('timeout_seconds', sa.Integer(), nullable=False, server_default='30'),
        sa.Column('max_retries', sa.Integer(), nullable=False, server_default='3'),
        sa.Column('user_agent', sa.String(255), nullable=True),
        sa.Column('follow_redirects', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('verify_ssl', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('custom_headers', postgresql.JSONB(), nullable=True),
        sa.Column('configuration', postgresql.JSONB(), nullable=True),
        sa.Column('scraping_config', postgresql.JSONB(), nullable=True),
        sa.Column('total_fetch_attempts', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('successful_fetches', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('failed_fetches', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('last_fetch_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('last_successful_fetch_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('average_response_time_ms', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('consecutive_failures', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('last_error_message', sa.Text(), nullable=True),
        sa.Column('last_error_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('total_articles_discovered', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('last_articles_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('version', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        # BaseModel columns
        sa.Column('is_deleted', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('deleted_by', sa.String(255), nullable=True),
        sa.Column('metadata_json', postgresql.JSONB(), nullable=True),
        sa.Column('created_by', sa.String(255), nullable=True),
        sa.Column('updated_by', sa.String(255), nullable=True),
        sa.PrimaryKeyConstraint('source_id')
    )
    # Indexes matching SourceModel
    op.create_index('idx_sources_url_unique', 'sources', ['url'], unique=True)
    op.create_index('idx_sources_status', 'sources', ['status'])
    op.create_index('idx_sources_domain', 'sources', ['domain'])
    op.create_index('idx_sources_domain_status', 'sources', ['domain', 'status'])
    op.create_index('idx_sources_fetch_due', 'sources', ['last_fetch_at', 'status', 'fetch_interval_minutes'])
    op.create_index('idx_sources_errors', 'sources', ['consecutive_failures', 'last_error_at'])
    op.create_index('idx_sources_health', 'sources', ['successful_fetches', 'failed_fetches', 'status'])
    op.create_index('idx_sources_created_at', 'sources', ['created_at'])
    op.create_index('idx_sources_updated_at', 'sources', ['updated_at'])
    
    # Create articles table (matching ArticleModel schema)
    op.create_table(
        'articles',
        sa.Column('article_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('source_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('rss_guid', sa.String(500), nullable=True),
        sa.Column('title', sa.String(1000), nullable=False),
        sa.Column('url', sa.Text(), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('pub_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('content_scrapped', sa.Text(), nullable=True),
        sa.Column('content_plaintext', sa.Text(), nullable=True),
        sa.Column('content_markdown', sa.Text(), nullable=True),
        sa.Column('content_excerpt', sa.Text(), nullable=True),
        sa.Column('summary', sa.Text(), nullable=True),
        sa.Column('categories', postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column('tags', postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column('keywords', postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column('coin_mentions', postgresql.JSONB(), nullable=True),
        sa.Column('enclosures', postgresql.JSONB(), nullable=True),
        sa.Column('thumbnail_url', sa.String(1000), nullable=True),
        sa.Column('processing_stage', sa.String(50), nullable=True),
        sa.Column('content_hash', sa.String(64), nullable=True),
        sa.Column('quality_score', sa.Integer(), nullable=True),
        sa.Column('quality_level', sa.String(20), nullable=True),
        sa.Column('word_count', sa.Integer(), nullable=True),
        sa.Column('reading_time_minutes', sa.Integer(), nullable=True),
        sa.Column('is_coin_checked', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('author', sa.String(255), nullable=True),
        sa.Column('author_email', sa.String(255), nullable=True),
        sa.Column('fetched_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('processed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('published_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('archived_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('error_type', sa.String(50), nullable=True),
        sa.Column('retry_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('language', sa.String(10), nullable=True),
        sa.Column('view_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('engagement_score', sa.Float(), nullable=True),
        sa.Column('is_duplicate', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('duplicate_of_article_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('validation_score', sa.Float(), nullable=True),
        sa.Column('validated_by', sa.String(255), nullable=True),
        sa.Column('validated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('has_error', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('error_marked_by', sa.String(255), nullable=True),
        sa.Column('error_marked_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('readability_score', sa.Float(), nullable=True),
        sa.Column('version', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['source_id'], ['sources.source_id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('article_id')
    )
    # Indexes matching ArticleModel
    op.create_index('idx_articles_source_id', 'articles', ['source_id'])
    op.create_index('idx_articles_content_hash', 'articles', ['content_hash'])
    op.create_index('idx_articles_processing_stage', 'articles', ['processing_stage'])
    op.create_index('idx_articles_quality_level', 'articles', ['quality_level'])
    op.create_index('idx_articles_language', 'articles', ['language'])
    op.create_index('idx_articles_created_at', 'articles', ['created_at'])
    op.create_index('idx_articles_fetched_at', 'articles', ['fetched_at'])
    op.create_index('idx_articles_pub_date', 'articles', ['pub_date'])
    op.create_index('idx_articles_source_pub_date', 'articles', ['source_id', 'pub_date'])
    op.create_index('idx_articles_rss_guid', 'articles', ['rss_guid'])
    op.create_index('idx_articles_url_source', 'articles', ['url', 'source_id'])
    op.create_index('idx_articles_title_source', 'articles', ['title', 'source_id'])
    op.create_index('uq_articles_url_source', 'articles', ['url', 'source_id'], unique=True)
    op.create_index('idx_articles_is_coin_checked', 'articles', ['is_coin_checked'])
    op.create_index('idx_articles_has_error', 'articles', ['has_error'])
    op.create_index('idx_articles_is_duplicate', 'articles', ['is_duplicate'])
    op.create_index('idx_articles_duplicate_of', 'articles', ['duplicate_of_article_id'])
    
    # Create fetch_sessions table (matching FetchSessionModel schema)
    op.create_table(
        'fetch_sessions',
        sa.Column('fetch_session_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('source_id', sa.String(), nullable=False),
        sa.Column('status', sa.String(50), nullable=False, server_default='pending'),
        sa.Column('cancelled_reason', sa.Text(), nullable=True),
        sa.Column('max_concurrent_fetches', sa.Integer(), nullable=False, server_default='5'),
        sa.Column('timeout_seconds', sa.Integer(), nullable=False, server_default='30'),
        sa.Column('timeout_config', postgresql.JSONB(), nullable=True),
        sa.Column('sources_to_fetch', postgresql.ARRAY(sa.String()), nullable=False),
        sa.Column('sources_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('sources_in_progress', postgresql.ARRAY(sa.String()), nullable=False),
        sa.Column('sources_completed', postgresql.ARRAY(sa.String()), nullable=False),
        sa.Column('sources_failed', postgresql.ARRAY(sa.String()), nullable=False),
        sa.Column('articles_discovered', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('articles_new', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('articles_updated', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('sources_successful', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('sources_failed_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('total_processing_time_seconds', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('average_response_time_ms', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('error_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('errors_by_type', postgresql.JSONB(), nullable=True),
        sa.Column('last_error_message', sa.Text(), nullable=True),
        sa.Column('fetch_errors', postgresql.JSONB(), nullable=True),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('expected_completion_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('version', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        # BaseModel columns
        sa.Column('is_deleted', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('deleted_by', sa.String(255), nullable=True),
        sa.Column('metadata_json', postgresql.JSONB(), nullable=True),
        sa.Column('created_by', sa.String(255), nullable=True),
        sa.Column('updated_by', sa.String(255), nullable=True),
        sa.PrimaryKeyConstraint('fetch_session_id')
    )
    # Indexes matching FetchSessionModel
    op.create_index('idx_fetch_sessions_status', 'fetch_sessions', ['status'])
    op.create_index('idx_fetch_sessions_started_at', 'fetch_sessions', ['started_at', 'status'])
    op.create_index('idx_fetch_sessions_completed', 'fetch_sessions', ['completed_at', 'status'])
    op.create_index('idx_fetch_sessions_created_at', 'fetch_sessions', ['created_at'])
    op.create_index('idx_fetch_sessions_updated_at', 'fetch_sessions', ['updated_at'])
    op.create_index('idx_fetch_sessions_sources_count', 'fetch_sessions', ['sources_count'])
    op.create_index('idx_fetch_sessions_articles', 'fetch_sessions', ['articles_discovered'])


def downgrade() -> None:
    """Drop RSS-related tables."""
    # Drop fetch_sessions table and all its indexes
    op.drop_index('idx_fetch_sessions_articles', table_name='fetch_sessions')
    op.drop_index('idx_fetch_sessions_sources_count', table_name='fetch_sessions')
    op.drop_index('idx_fetch_sessions_updated_at', table_name='fetch_sessions')
    op.drop_index('idx_fetch_sessions_created_at', table_name='fetch_sessions')
    op.drop_index('idx_fetch_sessions_completed', table_name='fetch_sessions')
    op.drop_index('idx_fetch_sessions_started_at', table_name='fetch_sessions')
    op.drop_index('idx_fetch_sessions_status', table_name='fetch_sessions')
    op.drop_table('fetch_sessions')
    
    # Drop articles table and all its indexes
    op.drop_index('idx_articles_duplicate_of', table_name='articles')
    op.drop_index('idx_articles_is_duplicate', table_name='articles')
    op.drop_index('idx_articles_has_error', table_name='articles')
    op.drop_index('idx_articles_is_coin_checked', table_name='articles')
    op.drop_index('uq_articles_url_source', table_name='articles')
    op.drop_index('idx_articles_title_source', table_name='articles')
    op.drop_index('idx_articles_url_source', table_name='articles')
    op.drop_index('idx_articles_rss_guid', table_name='articles')
    op.drop_index('idx_articles_source_pub_date', table_name='articles')
    op.drop_index('idx_articles_pub_date', table_name='articles')
    op.drop_index('idx_articles_fetched_at', table_name='articles')
    op.drop_index('idx_articles_created_at', table_name='articles')
    op.drop_index('idx_articles_language', table_name='articles')
    op.drop_index('idx_articles_quality_level', table_name='articles')
    op.drop_index('idx_articles_processing_stage', table_name='articles')
    op.drop_index('idx_articles_content_hash', table_name='articles')
    op.drop_index('idx_articles_source_id', table_name='articles')
    op.drop_table('articles')
    
    # Drop sources table and all its indexes
    op.drop_index('idx_sources_updated_at', table_name='sources')
    op.drop_index('idx_sources_created_at', table_name='sources')
    op.drop_index('idx_sources_health', table_name='sources')
    op.drop_index('idx_sources_errors', table_name='sources')
    op.drop_index('idx_sources_fetch_due', table_name='sources')
    op.drop_index('idx_sources_domain_status', table_name='sources')
    op.drop_index('idx_sources_domain', table_name='sources')
    op.drop_index('idx_sources_status', table_name='sources')
    op.drop_index('idx_sources_url_unique', table_name='sources')
    op.drop_table('sources')
