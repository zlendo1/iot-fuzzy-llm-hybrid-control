# Example Rules

## Fuzzy-LLM Hybrid IoT Management System

**Document Status:** Active\
**Last Updated:** 2026-02-05

This document provides a comprehensive guide to writing natural language rules
for the system, with detailed explanations of the demo rules and examples for
common automation scenarios.

______________________________________________________________________

## Table of Contents

1. [Understanding Rules](#1-understanding-rules)
2. [Demo Scenario Rules](#2-demo-scenario-rules)
3. [Writing Effective Rules](#3-writing-effective-rules)
4. [Rule Categories](#4-rule-categories)
5. [Advanced Patterns](#5-advanced-patterns)
6. [Common Mistakes](#6-common-mistakes)

______________________________________________________________________

## 1. Understanding Rules

### How Rules Work

1. **Sensor Reading**: A sensor publishes a value (e.g., temperature = 32.0)
2. **Fuzzy Processing**: The Fuzzy Engine converts the value to linguistic terms
   (e.g., "temperature is hot (0.85)")
3. **Rule Evaluation**: The LLM evaluates rules against the linguistic state
4. **Action Execution**: Matching rules trigger actuator commands

### Rule Structure

A natural language rule has two parts:

```
CONDITION → ACTION

"If <condition>, then <action>"
"When <condition>, <action>"
```

**Conditions** reference:

- Sensors by name or location
- Fuzzy linguistic terms (cold, hot, comfortable, etc.)
- Logical operators (and, or)

**Actions** reference:

- Actuators by name or location
- Device capabilities (turn_on, set_temperature, etc.)
- Specific values when needed

### Linguistic Terms

Rules use fuzzy linguistic terms defined in membership functions:

| Sensor Type | Available Terms                |
| ----------- | ------------------------------ |
| Temperature | cold, comfortable, warm, hot   |
| Humidity    | dry, comfortable, humid        |
| Light Level | dark, dim, bright, very_bright |
| Motion      | detected, not_detected         |

______________________________________________________________________

## 2. Demo Scenario Rules

The system includes 10 pre-configured rules demonstrating various automation
patterns.

### Climate Control Rules

#### Rule: climate_001

```
If the living room temperature is hot and humidity is high, 
turn on the air conditioner and set it to cooling mode at 22 degrees
```

**How it works:**

- Triggers when fuzzy engine reports "temperature is hot" AND "humidity is
  humid"
- Actions: Turn on AC, set to cooling, target 22 degrees
- Priority: 1 (highest)
- Tags: climate, cooling, comfort

**Sensor conditions that trigger this rule:**

- Temperature >= 30 degrees (in "hot" fuzzy region)
- Humidity >= 70% (in "humid" fuzzy region)

______________________________________________________________________

#### Rule: climate_002

```
If the living room temperature is warm and humidity is comfortable, 
no action is needed
```

**How it works:**

- Explicitly tells the LLM not to take action in acceptable conditions
- Prevents unnecessary HVAC activation
- Priority: 2 (evaluated after climate_001)

**Why this matters:** Without explicit "no action" rules, the LLM might invent
actions. Explicit rules guide the LLM toward correct behavior.

______________________________________________________________________

### Lighting Control Rules

#### Rule: lighting_001

```
When motion is detected in the hallway and the light level is dark, 
turn on the hallway light
```

**How it works:**

- Combines motion sensor with light sensor
- Only activates light when both conditions are met
- Safety feature for walking through dark hallway

______________________________________________________________________

#### Rule: lighting_002

```
When motion is detected in the living room and the light level is dim, 
turn on the living room light and set brightness to 70 percent
```

**How it works:**

- More nuanced than hallway - uses "dim" instead of "dark"
- Sets specific brightness level for comfort
- Demonstrates parameterized action

______________________________________________________________________

### Heating Control Rules

#### Rule: heating_001

```
If the bedroom temperature is cold, 
turn on the bedroom heater and set temperature to 21 degrees
```

**How it works:**

- Simple temperature-triggered heating
- Lower target temperature for sleeping comfort
- Location-specific (bedroom)

______________________________________________________________________

#### Rule: heating_002

```
If the office temperature is cold, 
turn on the office heater and set temperature to 22 degrees
```

**How it works:**

- Similar to bedroom but higher target for working
- Demonstrates room-specific comfort preferences

______________________________________________________________________

### Blind Control Rules

#### Rule: blinds_001

```
When the living room light level is very bright, 
close the living room blinds to 50 percent position
```

**How it works:**

- Reduces glare during intense sunlight
- Partial close (50%) balances light and view
- Uses "very_bright" fuzzy term (typically > 20,000 lux)

______________________________________________________________________

#### Rule: blinds_002

```
When the living room light level is dark and no motion is detected, 
open the living room blinds fully
```

**How it works:**

- Maximizes natural light in unoccupied room
- Combines light sensor with motion sensor
- Energy efficiency through natural lighting

______________________________________________________________________

### Energy Saving Rules

#### Rule: energy_001

```
If no motion is detected in the living room for a while and the light is on, 
turn off the living room light to save energy
```

**How it works:**

- Energy conservation automation
- Temporal awareness ("for a while")
- Explicit energy-saving intent helps LLM understanding

______________________________________________________________________

### Comfort Monitoring Rules

#### Rule: comfort_001

```
If the living room temperature is comfortable and humidity is comfortable, 
no action is needed as conditions are optimal
```

**How it works:**

- Confirms when no intervention needed
- Prevents unnecessary automation
- Documents optimal conditions explicitly

______________________________________________________________________

## 3. Writing Effective Rules

### Best Practices

1. **Be specific about location**

   ```
   Good: "If the living room temperature is hot..."
   Bad:  "If the temperature is hot..."
   ```

2. **Use linguistic terms from membership functions**

   ```
   Good: "temperature is comfortable" (matches fuzzy term)
   Bad:  "temperature is nice" (not defined)
   ```

3. **Reference actuators by name or location**

   ```
   Good: "turn on the living room AC"
   Bad:  "turn on the air conditioner" (ambiguous if multiple)
   ```

4. **Include specific values for parameterized actions**

   ```
   Good: "set brightness to 70 percent"
   Bad:  "set brightness higher"
   ```

5. **Use explicit "no action" rules**

   ```
   Good: "If conditions are comfortable, no action is needed"
   Bad:  (no rule, hoping LLM will figure it out)
   ```

### Rule Templates

**Simple condition-action:**

```
If the {location} {sensor_type} is {linguistic_term}, 
{action} the {location} {device}.
```

**Multi-condition:**

```
When {condition1} and {condition2}, 
{action1} and {action2}.
```

**No-action rule:**

```
If the {location} {sensor_type} is {acceptable_term}, 
no action is needed.
```

**Energy saving:**

```
If no motion is detected in {location} and {device} is on, 
turn off the {device} to save energy.
```

______________________________________________________________________

## 4. Rule Categories

### Climate Control

Control HVAC based on temperature and humidity.

```json
{
  "rule_id": "ac_cooling",
  "rule_text": "If the bedroom temperature is hot, turn on the bedroom AC and set it to 23 degrees",
  "priority": 1,
  "enabled": true,
  "metadata": { "tags": ["climate", "cooling"] }
}
```

```json
{
  "rule_id": "dehumidify",
  "rule_text": "If the bathroom humidity is very humid, turn on the exhaust fan",
  "priority": 1,
  "enabled": true,
  "metadata": { "tags": ["climate", "humidity"] }
}
```

### Lighting Automation

Control lights based on motion, time, or ambient light.

```json
{
  "rule_id": "entrance_light",
  "rule_text": "When motion is detected at the entrance and light level is dark, turn on the entrance light for 5 minutes",
  "priority": 1,
  "enabled": true,
  "metadata": { "tags": ["lighting", "motion", "entrance"] }
}
```

```json
{
  "rule_id": "reading_light",
  "rule_text": "When motion is detected in the study and light level is dim, turn on the desk lamp and set brightness to 80 percent",
  "priority": 2,
  "enabled": true,
  "metadata": { "tags": ["lighting", "comfort"] }
}
```

### Security Automation

Motion-triggered alerts and deterrents.

```json
{
  "rule_id": "night_motion",
  "rule_text": "If motion is detected in the hallway at night and all lights are off, turn on the hallway light as a security measure",
  "priority": 1,
  "enabled": true,
  "metadata": { "tags": ["security", "motion", "night"] }
}
```

### Energy Management

Reduce waste through smart automation.

```json
{
  "rule_id": "auto_off_ac",
  "rule_text": "If no motion is detected in the office for 30 minutes and the AC is running, turn off the office AC",
  "priority": 3,
  "enabled": true,
  "metadata": { "tags": ["energy", "climate"] }
}
```

```json
{
  "rule_id": "daylight_blinds",
  "rule_text": "When light level is bright and artificial lights are on in the living room, turn off the lights and open the blinds to use natural light",
  "priority": 2,
  "enabled": true,
  "metadata": { "tags": ["energy", "lighting", "blinds"] }
}
```

______________________________________________________________________

## 5. Advanced Patterns

### Compound Conditions

Combine multiple sensor readings:

```
If the bedroom temperature is cold and humidity is dry, 
turn on the heater and also turn on the humidifier
```

### Negation

Handle absence of conditions:

```
When no motion is detected in the living room and all lights are on, 
dim the lights to 20 percent after 10 minutes
```

### Priority-Based Overrides

Higher priority rules override lower:

```json
{
  "rule_id": "safety_override",
  "rule_text": "If smoke is detected anywhere, turn off all HVAC and open all windows",
  "priority": 1
}
```

```json
{
  "rule_id": "comfort_ac",
  "rule_text": "If temperature is hot, turn on AC",
  "priority": 5
}
```

The safety_override (priority 1) will take precedence.

### Contextual Rules

Different behavior based on context:

```
If motion is detected in the bedroom during nighttime hours, 
turn on the night light at 10 percent brightness
```

```
If motion is detected in the bedroom during daytime, 
open the bedroom blinds fully
```

______________________________________________________________________

## 6. Common Mistakes

### Mistake: Vague References

```
Bad:  "If it's hot, turn on the AC"
Good: "If the living room temperature is hot, turn on the living room AC"
```

### Mistake: Unknown Linguistic Terms

```
Bad:  "If temperature is freezing..." (not defined in membership function)
Good: "If temperature is cold..."
```

### Mistake: Ambiguous Actions

```
Bad:  "Make it cooler"
Good: "Turn on the AC and set temperature to 22 degrees"
```

### Mistake: Missing No-Action Rules

Without explicit no-action rules, the LLM may hallucinate actions:

```
Add: "If temperature is comfortable, no action is needed"
```

### Mistake: Conflicting Rules Without Priority

```
Rule A: "If hot, turn on AC"       (priority 5)
Rule B: "If humid, turn on fan"    (priority 5)

If both conditions are true, behavior is undefined.

Fix: Set different priorities or combine conditions:
"If hot and humid, turn on AC (priority 1)"
"If hot and not humid, use fan (priority 2)"
```

### Mistake: Overly Complex Rules

```
Bad:  "If the living room is hot and the bedroom is cold and nobody 
       is in the hallway and the kitchen light is on and..."

Good: Split into multiple simple rules with appropriate priorities
```

______________________________________________________________________

## See Also

- [User Guide](user-guide.md) - CLI commands for rule management
- [Configuration Guide](configuration-guide.md) - Membership function setup
- [Schema Reference](schema-reference.md) - Rule file format
- [Demo Walkthrough](demo-walkthrough.md) - Testing the demo rules
