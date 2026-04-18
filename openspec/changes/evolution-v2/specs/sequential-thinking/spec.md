# Delta for Sequential Thinking

## ADDED Requirements

### Requirement: Memory-Driven Planning
The system MUST cross-reference each planning step with the L3 Semantic Memory layer to find related past decisions.

#### Scenario: Plan Step Memory Match
- GIVEN a new plan step "implement JWT auth"
- WHEN the step is recorded
- THEN the system SHALL automatically retrieve and link the "JWT auth decision" from L3 memory.
