# shared/vault_manager Specification

## Purpose

Obsidian-compatible vault manager with atomic writes, backups, lock files, checksums, manifest tracking, and catastrophe recovery.

## Requirements

### REQ-VM-01: Write Note

The system SHALL write Markdown files atomically (write to temp, then rename) with YAML frontmatter.

#### Scenario: Write to folder

- GIVEN folder="Decisiones", filename="auth-model", content="..."
- WHEN write_note called
- AND creates directory if needed, writes with frontmatter (type, tags, author, dates)
- AND updates manifest with checksum

### REQ-VM-02: Process Inbox

The system SHALL classify notes in Inbox/ and move to appropriate folders based on content heuristics.

### REQ-VM-03: Integrity Check

The system SHALL verify all files against manifest checksums and report missing/corrupted files.

### REQ-VM-04: Rebuild

The system SHALL regenerate manifest from existing files when manifest is lost or corrupted.

## Storage

Vault path configured via environment. Each note is Markdown with YAML frontmatter.
Manifest tracks file paths and SHA-256 checksums.
