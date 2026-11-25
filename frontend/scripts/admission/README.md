# Offline Phase 6C-01 registry

From `frontend`, using existing frozen dependencies and Node 22.15.0:

```powershell
node scripts/admission/generate.mjs --write
node scripts/admission/generate.mjs
npx tsc -p scripts/admission/tsconfig.json
```

The first command updates only the new registry/manifest. Default mode checks
without writing; CI uses this mode. Existing Vitest invokes the unchanged gated
`assessSelectedFiles` pipeline offline. Fetch and WebSocket throw in the harness.
No expected labels compute results. No new dependency, service/executor, app
import or public endpoint is introduced.

Review the [proposed contract](../../../docs/PHASE6C01-MINIMIZED-CONTRACT.md),
all complete batch JSON and the provenance manifest. An indented read-only view:

```powershell
python -m json.tool ../backend/experiments/admission_data/manifest.json
```

70 profiles cover 29 selections, six survivors and reversals; 32 distinct complete
batches share content-addressed files. Source order, features, references and
group membership remain exact. This is AI-assisted engineering review evidence,
not independent human approval or proof that events occurred.

The server pins the manifest separately. Changes to profiles, source, generator,
engines, dependencies or canonical rules require review, regeneration, a conscious
version/pin decision and full checks. Never auto-pin incoming batches or widen
profiles to turn rejection green. Missing/corrupt files fail closed.

From `backend`, export/check the separate proposed schema:

```powershell
uv run --frozen python -m scripts.export_minimized
uv run --frozen python -m scripts.export_minimized --check
```

Never serve the fixture. There is no frontend intake/save integration. Original
source gate, engines, workers and 5000-ms deadline are unchanged. Mandatory CI
privacy/rollback checks remain; P5-F01 is OPEN and its candidate remains rejected.
