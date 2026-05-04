# Sports-Avatar-Mesh-Architecture (SA-MA)

Private downstream repo for Sports-Avatar LLC built on the
[OpenMesh Framework](https://github.com/prabbala/openmesh-framework).

## Setup

```bash
git clone git@github.com:prabbala/sa-ma.git
cd sa-ma
pip install -e ".[dev]"
python -m sa_ma.main
```

## Architecture

```
Entity: Sports-Avatar LLC
├── Product: Animation Engine
│   ├── product_type: Blender Pipeline
│   └── product_type: Motion Capture
└── Product: Cric-Avatar
    ├── product_type: Live Stream
    └── product_type: Replay Engine
```

## Structure

```
sa-ma/
├── config/
│   ├── animation-engine.yaml
│   └── cric-avatar.yaml
├── sa_ma/
│   ├── __init__.py
│   ├── main.py
│   └── preset.py
├── tests/
│   └── test_sa_ma.py
├── pyproject.toml
└── README.md
```
