# Documentation

## Fuzzy-LLM Hybrid IoT Management System

This directory contains all project documentation organized into two categories:

- **[user/](user/)** - User and reference documentation for operating the system
- **[dev/](dev/)** - Development documentation for understanding and extending
  the system

**Core Concept:** The system uses fuzzy logic as a **semantic bridge** between
numerical sensor values and linguistic concepts that an LLM can understand,
enabling natural language rule processing for IoT device management.

______________________________________________________________________

## Quick Start

| Task               | Document                                                   |
| ------------------ | ---------------------------------------------------------- |
| Install the system | [user/installation-guide.md](user/installation-guide.md)   |
| Learn CLI commands | [user/user-guide.md](user/user-guide.md)                   |
| Configure devices  | [user/configuration-guide.md](user/configuration-guide.md) |
| Write rules        | [user/example-rules.md](user/example-rules.md)             |
| Run the demo       | [user/demo-walkthrough.md](user/demo-walkthrough.md)       |

______________________________________________________________________

## User Documentation

Location: **[user/](user/)**

Documentation for system operators, administrators, and evaluators.

| Document                                                | Purpose                                                  |
| ------------------------------------------------------- | -------------------------------------------------------- |
| [installation-guide.md](user/installation-guide.md)     | Docker and local installation instructions               |
| [user-guide.md](user/user-guide.md)                     | CLI usage, commands, and workflows                       |
| [configuration-guide.md](user/configuration-guide.md)   | Device, MQTT, LLM, and membership function configuration |
| [schema-reference.md](user/schema-reference.md)         | Complete JSON schema documentation                       |
| [api-reference.md](user/api-reference.md)               | Python API reference for all layers                      |
| [example-rules.md](user/example-rules.md)               | Natural language rule examples and patterns              |
| [demo-walkthrough.md](user/demo-walkthrough.md)         | Step-by-step demo execution guide                        |
| [demo-troubleshooting.md](user/demo-troubleshooting.md) | Common issues and solutions                              |
| [evaluation-report.md](user/evaluation-report.md)       | Test coverage, performance, and accuracy metrics         |

______________________________________________________________________

## Development Documentation

Location: **[dev/](dev/)**

Documentation for developers, architects, and thesis reviewers.

| Document                                         | Purpose                                                 |
| ------------------------------------------------ | ------------------------------------------------------- |
| [thesis-setup.md](dev/thesis-setup.md)           | Original thesis assignment and research scope           |
| [project-brief.md](dev/project-brief.md)         | Project overview, objectives, and deliverables          |
| [srs.md](dev/srs.md)                             | Software Requirements Specification (100+ requirements) |
| [add.md](dev/add.md)                             | Architecture Design Document (5-layer architecture)     |
| [wbs.md](dev/wbs.md)                             | Work Breakdown Structure                                |
| [engineering-tasks.md](dev/engineering-tasks.md) | Detailed implementation task list (150+ tasks)          |

### Document Flow

```
thesis-setup.md → project-brief.md → srs.md → add.md → wbs.md → engineering-tasks.md
     ↓                  ↓                ↓         ↓
  Research          Objectives      Requirements  Architecture
   Scope            & Scope         Specification   Design
```

______________________________________________________________________

## Key Information

### Performance Targets

| Metric              | Target       |
| ------------------- | ------------ |
| End-to-end response | < 5 seconds  |
| LLM inference       | < 3 seconds  |
| Fuzzy processing    | < 100 ms     |
| System startup      | < 30 seconds |

### Technology Stack

| Component     | Technology                        |
| ------------- | --------------------------------- |
| Runtime       | Python 3.9+                       |
| LLM           | Ollama (CPU-only, edge-optimized) |
| Messaging     | MQTT (Mosquitto)                  |
| Configuration | JSON with schema validation       |
| Deployment    | Docker Compose                    |

### Thesis MVP Features

- Fuzzy logic semantic bridge with JSON configuration
- Ollama-based LLM inference (qwen3:0.6b default)
- Natural language rule processing
- MQTT device communication
- Command-line interface
- Docker Compose containerization
- Smart home demo (14 devices, 10 rules)

### Test Results

- **806 tests** passing
- **83% code coverage**
- All performance targets met

______________________________________________________________________

## For Thesis Evaluation

1. **Research Context**: [dev/thesis-setup.md](dev/thesis-setup.md)
2. **Core Concept**: Semantic bridge implementation in [dev/add.md](dev/add.md)
3. **Requirements**: [dev/srs.md](dev/srs.md)
4. **Results**: [user/evaluation-report.md](user/evaluation-report.md)
5. **Demo**: [user/demo-walkthrough.md](user/demo-walkthrough.md)
