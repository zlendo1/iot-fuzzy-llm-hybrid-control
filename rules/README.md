# Rules Directory

This directory stores the active rules for the Fuzzy-LLM Hybrid IoT Management
System.

## Purpose

Contains the rule database that defines the natural language control logic for
IoT devices. Rules are evaluated by the LLM to determine when and what actions
to take based on linguistic sensor descriptions.

## File Format

`active_rules.json` - JSON file containing all configured rules. Each rule
includes:

- `rule_id` - Unique identifier for the rule
- `rule_text` - Natural language rule description (e.g., "If the temperature is
  hot and humidity is high, turn on the air conditioner")
- `priority` - Integer for conflict resolution (higher takes precedence)
- `enabled` - Boolean to enable/disable without deleting
- `created_timestamp` - ISO 8601 format creation date
- `last_triggered` - ISO 8601 format when rule last fired
- `trigger_count` - Number of times this rule has triggered
- `metadata` - Optional tags and annotations

## Example

```json
{
  "rules": [
    {
      "rule_id": "rule_001",
      "rule_text": "If the temperature is hot and humidity is high, turn on the air conditioner",
      "priority": 1,
      "enabled": true,
      "created_timestamp": "2026-01-15T10:00:00Z",
      "last_triggered": "2026-01-15T14:30:00Z",
      "trigger_count": 12,
      "metadata": { "tags": ["climate", "cooling"] }
    }
  ]
}
```

## Rule Management

- The Rule Manager provides CRUD operations for rules
- Rules can be added, modified, deleted, enabled, or disabled
- Import/export functionality for backup and sharing
- Full change auditing with timestamps

## Evaluation Rules

- Rules are evaluated when sensor state changes or on scheduled interval
  (default 5 seconds)
- The Rule Interpreter matches linguistic sensor states to rule conditions
- LLM processes each rule independently (per-rule prompting design decision
  DD-06)
- Conflicts resolved by priority when multiple rules target same device

## Design Decision

As noted in DD-05, file-based persistence was chosen to eliminate database
dependencies while supporting rule backup via simple file copy operations.
