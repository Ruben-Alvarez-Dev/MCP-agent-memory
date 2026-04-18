# Delta for Memory Router

## ADDED Requirements

### Requirement: Token Pruning
The system SHALL aggressively prune content from context packs to fit within the token budget while maintaining information density.

#### Scenario: Prune Long File
- GIVEN a file exceeding 4000 tokens
- WHEN retrieved for context
- THEN the system MUST remove non-essential comments and collapse distant function bodies.
