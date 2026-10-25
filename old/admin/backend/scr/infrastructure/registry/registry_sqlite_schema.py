"""SQLite schema constants for the registry index."""

from __future__ import annotations

import sqlite3
from contextlib import suppress


SCHEMA_VERSION = 1

SORTABLE_FIELDS = {
    "entity_key": "entity_key",
    "title": "title",
    "display_name": "display_name",
    "status": "status",
    "sort_order": "sort_order",
    "priority": "priority",
    "updated_at": "updated_at",
    "synced_at": "synced_at",
}

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS schema_migrations (
    version INTEGER PRIMARY KEY,
    applied_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    description TEXT
);

CREATE TABLE IF NOT EXISTS registry_entities (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    entity_type TEXT NOT NULL,
    entity_key TEXT NOT NULL,
    slug TEXT,
    title TEXT,
    display_name TEXT,
    description TEXT,
    summary TEXT,
    status TEXT NOT NULL DEFAULT 'active',
    visibility TEXT NOT NULL DEFAULT 'public',
    sort_order INTEGER NOT NULL DEFAULT 0,
    priority INTEGER NOT NULL DEFAULT 0,
    source_kind TEXT NOT NULL DEFAULT 'yaml',
    source_path TEXT,
    source_hash TEXT,
    source_mtime INTEGER,
    metadata_json TEXT,
    created_at TEXT,
    updated_at TEXT,
    synced_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(entity_type, entity_key)
);

CREATE TABLE IF NOT EXISTS categories (
    entity_id INTEGER PRIMARY KEY,
    path TEXT NOT NULL UNIQUE,
    parent_path TEXT,
    depth INTEGER NOT NULL DEFAULT 0,
    slug TEXT NOT NULL,
    label TEXT NOT NULL,
    full_label TEXT,
    icon TEXT,
    color TEXT,
    description TEXT,
    seo_title TEXT,
    seo_description TEXT,
    article_count INTEGER NOT NULL DEFAULT 0,
    published_article_count INTEGER NOT NULL DEFAULT 0,
    draft_article_count INTEGER NOT NULL DEFAULT 0,
    child_count INTEGER NOT NULL DEFAULT 0,
    first_article_at TEXT,
    last_article_at TEXT,
    is_leaf INTEGER NOT NULL DEFAULT 1,
    is_featured INTEGER NOT NULL DEFAULT 0,
    is_hidden INTEGER NOT NULL DEFAULT 0,
    extra_json TEXT,
    FOREIGN KEY(entity_id) REFERENCES registry_entities(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS tags (
    entity_id INTEGER PRIMARY KEY,
    slug TEXT NOT NULL UNIQUE,
    name TEXT NOT NULL,
    normalized_name TEXT NOT NULL,
    description TEXT,
    color TEXT,
    icon TEXT,
    article_count INTEGER NOT NULL DEFAULT 0,
    published_article_count INTEGER NOT NULL DEFAULT 0,
    draft_article_count INTEGER NOT NULL DEFAULT 0,
    first_article_at TEXT,
    last_article_at TEXT,
    is_featured INTEGER NOT NULL DEFAULT 0,
    is_hidden INTEGER NOT NULL DEFAULT 0,
    aliases_json TEXT,
    extra_json TEXT,
    FOREIGN KEY(entity_id) REFERENCES registry_entities(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS articles (
    entity_id INTEGER PRIMARY KEY,
    slug TEXT NOT NULL,
    title TEXT NOT NULL,
    content_type TEXT NOT NULL DEFAULT 'blog',
    file_path TEXT NOT NULL UNIQUE,
    url_path TEXT,
    status TEXT NOT NULL DEFAULT 'draft',
    excerpt TEXT,
    cover_image TEXT,
    author_key TEXT,
    word_count INTEGER NOT NULL DEFAULT 0,
    reading_minutes INTEGER NOT NULL DEFAULT 0,
    published_at TEXT,
    created_at TEXT,
    updated_at TEXT,
    frontmatter_json TEXT,
    extra_json TEXT,
    FOREIGN KEY(entity_id) REFERENCES registry_entities(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS article_categories (
    article_entity_id INTEGER NOT NULL,
    category_path TEXT NOT NULL,
    is_primary INTEGER NOT NULL DEFAULT 0,
    sort_order INTEGER NOT NULL DEFAULT 0,
    PRIMARY KEY(article_entity_id, category_path),
    FOREIGN KEY(article_entity_id) REFERENCES articles(entity_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS article_tags (
    article_entity_id INTEGER NOT NULL,
    tag_slug TEXT NOT NULL,
    sort_order INTEGER NOT NULL DEFAULT 0,
    PRIMARY KEY(article_entity_id, tag_slug),
    FOREIGN KEY(article_entity_id) REFERENCES articles(entity_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS source_files (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_kind TEXT NOT NULL,
    file_path TEXT NOT NULL UNIQUE,
    file_hash TEXT,
    file_size INTEGER,
    file_mtime INTEGER,
    last_synced_at TEXT,
    last_error TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS sync_runs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    sync_type TEXT NOT NULL,
    status TEXT NOT NULL,
    started_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    finished_at TEXT,
    scanned_files INTEGER NOT NULL DEFAULT 0,
    changed_files INTEGER NOT NULL DEFAULT 0,
    upserted_entities INTEGER NOT NULL DEFAULT 0,
    deleted_entities INTEGER NOT NULL DEFAULT 0,
    error_count INTEGER NOT NULL DEFAULT 0,
    message TEXT,
    error_json TEXT
);

CREATE INDEX IF NOT EXISTS idx_entities_type_key
ON registry_entities(entity_type, entity_key);
CREATE INDEX IF NOT EXISTS idx_entities_type_status
ON registry_entities(entity_type, status);
CREATE INDEX IF NOT EXISTS idx_entities_title
ON registry_entities(title);
CREATE INDEX IF NOT EXISTS idx_entities_updated_at
ON registry_entities(updated_at);
CREATE INDEX IF NOT EXISTS idx_categories_parent
ON categories(parent_path);
CREATE INDEX IF NOT EXISTS idx_categories_label
ON categories(label);
CREATE INDEX IF NOT EXISTS idx_categories_article_count
ON categories(article_count DESC);
CREATE INDEX IF NOT EXISTS idx_tags_name
ON tags(name);
CREATE INDEX IF NOT EXISTS idx_tags_normalized_name
ON tags(normalized_name);
CREATE INDEX IF NOT EXISTS idx_tags_article_count
ON tags(article_count DESC);
CREATE INDEX IF NOT EXISTS idx_articles_status
ON articles(status);
CREATE INDEX IF NOT EXISTS idx_articles_published_at
ON articles(published_at DESC);
DROP INDEX IF EXISTS idx_templates_type;
DROP INDEX IF EXISTS idx_templates_usage_count;
DROP INDEX IF EXISTS idx_articles_template;
DROP TABLE IF EXISTS templates;
"""

SEARCH_TABLE_SQL = """
CREATE VIRTUAL TABLE IF NOT EXISTS registry_search USING fts5(
    entity_type,
    entity_key,
    title,
    display_name,
    description,
    summary,
    tokenize='unicode61'
)
"""


def ensure_registry_schema(conn: sqlite3.Connection) -> None:
    """Create or migrate the registry index schema."""
    conn.executescript(SCHEMA_SQL)
    conn.execute(
        "INSERT OR IGNORE INTO schema_migrations(version, description) VALUES (?, ?)",
        (SCHEMA_VERSION, "registry index initial schema"),
    )
    ensure_search_table(conn)


def ensure_search_table(conn: sqlite3.Connection) -> None:
    """Create the optional FTS search table when SQLite supports FTS5."""
    with suppress(sqlite3.OperationalError):
        conn.execute(SEARCH_TABLE_SQL)

