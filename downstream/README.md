# Downstream Repo Scaffolds

These directories are complete scaffolds for private repos that inherit
the OpenMesh Framework (OM-FW) as a dependency.

## Repos

| Directory | Full Name                          | Entity             | Products                                |
| --------- | ---------------------------------- | ------------------ | --------------------------------------- |
| `ea-ma/`  | EAIS-Mesh-Architecture             | Empirical-AiS Inc. | BAI, Cybersecurity-AI, GenAI, RAG       |
| `sa-ma/`  | Sports-Avatar-Mesh-Architecture    | Sports-Avatar LLC  | Animation Engine, Cric-Avatar           |

## How to Extract to Private Repos

```bash
# EA-MA
cp -r downstream/ea-ma /path/to/ea-ma
cd /path/to/ea-ma
git init
git remote add origin git@github.com:prabbala/ea-ma.git
# Update pyproject.toml with your actual org
pip install -e ".[dev]"
pytest

# SA-MA
cp -r downstream/sa-ma /path/to/sa-ma
cd /path/to/sa-ma
git init
git remote add origin git@github.com:prabbala/sa-ma.git
pip install -e ".[dev]"
pytest
```

Each downstream repo depends on OM-FW via pip and contains only
business-specific configuration — no framework code duplication.
