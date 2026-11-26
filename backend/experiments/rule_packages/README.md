# Stopped implementation revisions

`historical-v1` reproduces the original worker byte for byte. `indexed-r1`
applies only the four previously measured membership-index substitutions,
using the original semantic wire versions and immutable admission catalog.

`manifest.json` is a separately pinned implementation registry. Build with
`node frontend/scripts/shared-rules/build-packages.mjs`; generated files go to
new ignored `.local/phase6c03-packages` paths. The builder writes only a candidate
manifest there; it does not repin this reviewed manifest or the original registry.

**Phase 6C-03 is incomplete. C03-COMP-01 is OPEN.** The existing tenant schema
cannot losslessly identify the selected implementation revision for each
owner/collection/generation. `storage-compatibility.json` records the stop.
The new seed-reference codec is not a complete durable adapter. There is no
typed SQL projection, survivor publication, save route or persistence activation.
Successful unit tests and benchmarks do not approve adoption or merging.
