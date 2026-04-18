# Local Skill Registry Specification

## Purpose
Manage agent capabilities autonomously, eliminating external dependencies on Gentle AI.

## Requirements

### Requirement: Local Skill Loading
The system MUST load agent skills (instructions and scripts) exclusively from the local `MCP-servers/skills/` directory.

#### Scenario: Load Internal Skill
- GIVEN a local skill directory `skills/filesystem`
- WHEN the agent initializes
- THEN the system MUST register the tools and instructions from the local directory.
