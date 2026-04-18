# sequential-thinking Specification

## Purpose

Structured reasoning, planning, and virtual sandbox execution.
Provides a 6-phase thinking framework, execution planning, and staged filesystem changes.

## Requirements

### REQ-ST-01: Sequential Thinking

The system SHALL break a problem into structured thinking steps with configurable max depth.

#### Scenario: Multi-step reasoning

- GIVEN problem="design auth system" and max_steps=5
- WHEN sequential_thinking called
- AND creates session with 6-phase framework
- AND returns session_id and first step prompt

### REQ-ST-02: Record Thought

The system SHALL persist a thinking step conclusion with confidence score.

#### Scenario: Record conclusion

- GIVEN session_id, step=2, conclusion="use JWT", confidence=0.85
- WHEN record_thought called
- AND appends to ~/.memory/thoughts/{session_id}.json

### REQ-ST-03: Create Plan

The system SHALL generate an execution plan from a goal with optional dependencies.

#### Scenario: Plan with dependencies

- GIVEN goal="add auth" and dependencies="database setup"
- WHEN create_plan called
- AND creates plan with steps and saves to ~/.memory/thoughts/plans/{session_id}.json

### REQ-ST-04: Update Plan Step

The system SHALL update step status (pending/in_progress/done/blocked/skipped).

#### Scenario: Mark step done

- GIVEN session_id and step=1
- WHEN update_plan_step(status="done", result="JWT implemented")
- AND updates the plan file with new status and result

### REQ-ST-05: Reflect

The system SHALL review a thinking session and identify gaps.

#### Scenario: Gap identification

- GIVEN session with 5 steps completed
- WHEN reflect called
- AND returns analysis of coverage and potential improvements

### REQ-ST-06: Get/List Sessions

The system SHALL return session data and list all sessions.

#### Scenario: Get session

- GIVEN existing session_id
- WHEN get_thinking_session called
- AND returns all steps from the session file

### REQ-ST-07: Propose Change Set (Virtual Sandbox)

The system SHALL stage file changes without touching the filesystem.

#### Scenario: Stage changes

- GIVEN session_id, title="fix bug", changes_json with file paths and content
- WHEN propose_change_set called
- AND writes change set to staging buffer as JSON
- AND returns change_set_id and status "staged"

### REQ-ST-08: Apply Sandbox

The system SHALL flush staged changes to disk only after explicit approval.

#### Scenario: Approved change

- GIVEN existing change_set_id and approved=True
- WHEN apply_sandbox called
- AND reads staged JSON, writes files to disk
- AND returns status "applied"

#### Scenario: Rejected change

- GIVEN existing change_set_id and approved=False
- WHEN apply_sandbox called
- AND deletes staged JSON without writing files
- AND returns status "rejected"

### REQ-ST-09: Daemon Status

The system SHALL report session counts, plan counts, and staged change sets.

## Storage

| Target | Path | Format |
|--------|------|--------|
| Thoughts | `~/.memory/thoughts/{session_id}.json` | JSON array of steps |
| Plans | `~/.memory/thoughts/plans/{session_id}.json` | JSON with steps and statuses |
| Staging | `~/.memory/staging_buffer/{change_set_id}.json` | JSON with file changes |

## Dependencies

- None from shared modules (fully standalone, filesystem-based)
