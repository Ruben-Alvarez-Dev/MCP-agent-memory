# engram-bridge Specification

## Purpose

Semantic Decision Memory (L3). Stores curated decisions, entities, and patterns as Markdown files with YAML frontmatter. Also manages an Obsidian-compatible vault. Pure filesystem — no Qdrant needed.

## Requirements

### REQ-EB-01: Save Decision

The system SHALL persist content as Markdown with YAML frontmatter under the configured engram path, organized by category and scope.

#### Scenario: Save with defaults

- GIVEN title="Chose SQLite" and content="**What:** ... **Why:** ..."
- WHEN save_decision called
- AND writes file to ~/.memory/engram/{scope}/decision/{slug}.md with YAML frontmatter (title, category, tags, scope, dates)
- AND returns file path

### REQ-EB-02: Search Decisions

The system SHALL perform keyword search over engram Markdown files.

#### Scenario: Query with category filter

- GIVEN query="database" and category="decision"
- WHEN search_decisions called
- AND returns only files matching both keywords in body AND category in metadata

### REQ-EB-03: Get Decision

The system SHALL return full content of a specific engram file by relative path.

#### Scenario: Valid path

- GIVEN file_path="agent/chose-sqlite.md"
- WHEN get_decision called
- AND returns metadata dict with parsed frontmatter and body

### REQ-EB-04: List Decisions

The system SHALL list engram files with optional category and scope filters.

#### Scenario: Filter by scope

- GIVEN scope="personal"
- WHEN list_decisions called
- AND returns only files under personal/ directory

### REQ-EB-05: Delete Decision

The system SHALL delete an engram file by relative path.

#### Scenario: Valid deletion

- GIVEN existing file path
- WHEN delete_decision called
- AND removes the file and returns confirmation

### REQ-EB-06: Status

The system SHALL report engram path, total file count, and scopes present.

### REQ-EB-07: Vault Write

The system SHALL write a note to a configured Obsidian vault folder.

#### Scenario: Write to Decisiones

- GIVEN folder="Decisiones", filename="auth-model", content="..."
- WHEN vault_write called
- AND writes Markdown file to vault/Decisiones/auth-model.md with frontmatter (type, tags, author)

### REQ-EB-08: Vault Process Inbox

The system SHALL classify and move notes from Inbox/ to appropriate folders.

### REQ-EB-09: Vault Integrity Check

The system SHALL run full vault audit — check manifest, checksums, and file structure.

### REQ-EB-10: Vault List Notes

The system SHALL list notes in a vault folder.

### REQ-EB-11: Vault Read Note

The system SHALL read and return a vault note's content.

## Storage

| Target | Path | Format |
|--------|------|--------|
| Engram | `~/.memory/engram/{scope}/{category}/` | Markdown + YAML frontmatter |
| Vault | Configured vault path | Obsidian-compatible Markdown |

## Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| ENGRAM_PATH | ~/.memory/engram | Root engram directory |

## Dependencies

- `shared.vault_manager`: vault singleton (atomic writes, backups, integrity)
