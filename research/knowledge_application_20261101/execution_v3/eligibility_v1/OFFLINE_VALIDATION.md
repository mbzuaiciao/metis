# V3 execution wrapper offline validation — 2026-11-01

See [full v3 report](../v3/OFFLINE_VALIDATION.md) for exact file inventory,failures,matching data hashes and limitations. Scientific freeze **4a65d1ed2eab32e24fe228d0f79ed045a4b4135de6a6c465f5c3ec249efda983**;execution manifest **8e7011211c9913090db946c01a5c82b0e9c4c7555149af62474d21fa7c2031a6**. Frozen v1/v2 and execution_v2 remain byte-identical; all private failed runs preserved.

Final wrapper16pass/0skip,0.471s/tool0.461s with real installed Modal1.2.3 lazy API declarations only,network/model-import/process audit guards. V3 scientific18pass/1explicit exact-Transformers skip,0.576s/tool0.567s. Local4.56.2 unavailable;5.x never substituted. The exact configuration regression is implemented but UNVERIFIED. Default regression exits2/PackageNotFoundError without passing evidence or output creation.

Minimal wrapper changes: v3 source/freeze/paths/study identity;reuse original smoke solely for package/model provenance plus the same Git layer;validate same config except study;mandatory passing exact-version regression evidence before GPU work;v3-only acceptance/accounting/previous-stage bindings;A/B/C full effective-config equality. Same resource,budget,timeout,retry,history,technical-completeness,phase/redaction and private-artifact gates. No stage starts automatically;baseline calls A/B only.

**NO-GO for GPU execution** pending real exact-version regression,new freeze acceptance and refreshed accounting including historical v2 costs. [Exact future command](READINESS.md). No Modal call/build/GPU/download/inference/training,commit,push or merge during preparation.
