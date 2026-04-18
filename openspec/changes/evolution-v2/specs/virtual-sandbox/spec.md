# Virtual Sandbox Specification

## Purpose
Provide a plan-first execution environment where changes are staged before disk application.

## Requirements

### Requirement: Virtual Diff Buffer
The system MUST support a staging buffer where the agent can propose and review file changes without modifying the source.

#### Scenario: Propose Change to Sandbox
- GIVEN an active `sequential-thinking` session
- WHEN the agent uses `propose_change_set`
- THEN the system MUST store the change in the L1.5 staging layer.

#### Scenario: Apply Sandbox to Disk
- GIVEN a validated sandbox change set
- WHEN the user approves the application
- THEN the system SHALL write the staged changes to the physical filesystem.
