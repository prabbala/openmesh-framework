# OpenMesh Framework Integration

This directory wires plug-n-play-crm-ai (BAI CRM-AI product) into the
EAIS-Mesh-Architecture (EA-MA) which inherits from the OpenMesh Framework (OM-FW).

## Dependency Chain

```
plug-n-play-crm-ai  →  ea-ma  →  openmesh-framework
     (this repo)       (EA-MA)      (OM-FW public)
```

## Setup

```bash
# From the plug-n-play-crm-ai root:

# 1. Clone the dependencies (one-time)
cd ..
git clone https://github.com/prabbala/openmesh-framework.git
git clone https://github.com/prabbala/ea-ma.git

# 2. Install in order
cd openmesh-framework && pip install -e ".[dev]" && cd ..
cd ea-ma && pip install -e ".[dev]" && cd ..
cd plug-n-play-crm-ai

# 3. Verify the integration
python openmesh-framework/verify.py
```
