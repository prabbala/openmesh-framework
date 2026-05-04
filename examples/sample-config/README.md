# Sample Configuration

Generic domain registration examples for the OpenMesh Framework.
Copy these into your own project and customize for your business.

## Files

| File                  | Runtime Type | Adapter           | Description                |
| --------------------- | ------------ | ----------------- | -------------------------- |
| `server-infra.yaml`   | server       | ServerAdapter     | EC2/Docker/Nginx infra     |
| `serverless-api.yaml` | serverless   | ServerlessAdapter | Lambda/DynamoDB API layer  |

## Usage with PnP

```python
from packages.core.pnp import PnPMain, PnPConfig

config = PnPConfig(
    entity_id="my-company",
    entity_name="My Company Inc.",
    config_dir="path/to/your/config",
    jwt_secret="your-production-secret",
)
pnp = PnPMain(config)
pnp.bootstrap()

# Register a user
token = pnp.register_user(
    email="admin@mycompany.com",
    password="secure-password",
    user_id="admin-1",
    role="superuser",
    lob_assignments=["p-lob-infrastructure", "p-lob-api"],
)

# Render dashboard
panels = pnp.render_dashboard(token=token)
```

## Creating Your Own Downstream Repo

See `downstream/` in this repository for complete examples of how to
create a private repo that inherits from the OpenMesh Framework.
