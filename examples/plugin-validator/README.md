# Ordia plugin validator example

Minimal [`ordia.validators`](../../packages/ordia-core/docs/VALIDATOR.md) entry point.

## Setup

```powershell
pip install -e packages/ordia-core
pip install -e examples/plugin-validator
```

## Use

In a project with `ordia init`:

```powershell
ordia validate --project
```

The plugin warns when `PROFILE.md` does not mention the `ordia.yaml` profile id.

## Strict mode

```powershell
ordia validate --project --strict-profile
```

Promotes the plugin warning to an error.
