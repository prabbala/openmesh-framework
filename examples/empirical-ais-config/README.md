# Empirical-AiS Inc. — Example Configuration

This directory demonstrates how **Empirical-AiS Inc.** consumes the OpenMesh framework
as a dependency and registers its business domains for observability.

## Entity Structure (4-Tier Model)

```
Entity: Empirical-AiS Inc.
├── Domain: Cybersecurity (DeCMMC)     → runtime_type: server
│   ├── Product_Family: Compliance Scanner
│   │   └── Resource: EC2 scanner instance
│   └── Product_Family: Threat Monitor
│       └── Resource: Docker container
├── Domain: GenAI Platform             → runtime_type: serverless
│   ├── Product_Family: Inference Engine
│   │   └── Resource: Lambda functions
│   └── Product_Family: Model Store
│       └── Resource: DynamoDB tables
└── Domain: RAG-AI Pipeline            → runtime_type: server
    └── Product_Family: Document Processor
        └── Resource: EC2 processing instance
```

## Domain Registrations

| File                  | Domain               | Runtime Type | Adapter           |
| --------------------- | -------------------- | ------------ | ----------------- |
| `cybersecurity.yaml`  | Cybersecurity DeCMMC | server       | ServerAdapter     |
| `genai-platform.yaml` | GenAI Platform       | serverless   | ServerlessAdapter |
| `rag-pipeline.yaml`   | RAG-AI Pipeline      | server       | ServerAdapter     |

## LOB Mapping

| LOB ID                | Category | Domains              |
| --------------------- | -------- | -------------------- |
| `p-lob-cybersecurity` | P_LOB    | Cybersecurity DeCMMC |
| `p-lob-genai`         | P_LOB    | GenAI Platform       |
| `p-lob-rag`           | P_LOB    | RAG-AI Pipeline      |

## How to Use

1. Install the framework: `pip install openmesh-core`
2. Place these YAML files in your project's config directory
3. Load registrations on startup:

```python
from packages.core.domain_registry.serialization import deserialize_from_yaml
from packages.core.domain_registry.registry import DomainRegistry

registry = DomainRegistry()

with open("cybersecurity.yaml") as f:
    reg = deserialize_from_yaml(f.read())
    registry.register(reg)
```
