# PyPI publish setup (one-time)

CI publish failed because neither **trusted publishing** nor **`PYPI_API_TOKEN`** is configured.

## Option A — API token (fastest)

1. Create token at https://pypi.org/manage/account/token/ (scope: project `ordia-core` or entire account).
2. Add GitHub secret on **ordia-package**:
   ```powershell
   gh secret set PYPI_API_TOKEN -R tmac14/ordia-package
   ```
3. Re-run publish workflow:
   ```powershell
   gh workflow run publish.yml -R tmac14/ordia-package --ref ordia-core-v0.9.1
   ```
   Or delete and re-push the tag.

## Option B — Trusted publishing (OIDC, no long-lived token)

On https://pypi.org/manage/project/ordia-core/settings/publishing/ (create project first if needed):

| Field | Value |
|-------|-------|
| Owner | `tmac14` |
| Repository | `ordia-package` |
| Workflow | `publish.yml` |
| Environment | *(leave empty)* |

Then re-run the workflow on tag `ordia-core-v0.9.1`.

## Manual upload (local)

```powershell
cd packages/ordia-core
python -m build
python -m twine upload dist/*
```

After publish, verify: `pip install ordia-core==0.9.1`
