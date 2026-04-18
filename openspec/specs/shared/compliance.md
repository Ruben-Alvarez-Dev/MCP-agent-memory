# shared/compliance Specification

## Purpose

Code verification engine. Checks source code against configurable project rules (Pydantic V2, no secrets, UTC datetime, no bare excepts, no eval, input validation).

## Requirements

### REQ-CP-01: Verify Compliance

The system SHALL accept code string and optional rule_ids filter, return violations.

#### Scenario: Pydantic V1 config detected

- GIVEN code containing `class Config:` inside a BaseModel subclass
- WHEN verify_compliance called
- AND returns violation with rule_id="PYDANTIC_V2_CONFIG", severity="error"

#### Scenario: Secret in code

- GIVEN code containing `password = "hardcoded123"`
- WHEN verify_compliance called
- AND returns violation for NO_SECRETS_IN_CODE

### REQ-CP-02: Default Rules

The system SHALL provide 6 built-in rules: PYDANTIC_V2_CONFIG, NO_SECRETS_IN_CODE, DATETIME_UTC, NO_BARE_EXCEPT, NO_EVAL, INPUT_VALIDATION.

### REQ-CP-03: Custom Rules

The system SHALL allow adding/removing rules via add_rule(ProjectRule) and remove_rule(rule_id).
