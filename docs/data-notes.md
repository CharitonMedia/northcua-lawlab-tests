# Data notes

- Twelve real-model task runs are included. One scripted canvas fixture control is recorded separately and isn't part of the model score.
- Six baseline DOM-assisted browser runs produced three full completions and four correct saved states. A 20-step stopping limit applies to every model task.
- The LLM evaluator is disabled. Independent outcome checks use exact saved fixture values; the full-pass column additionally requires clean harness completion.
- Baseline Settings B overlapped with ISO-hint Project A and Project B. All three timings are flagged in the summary and excluded from single-request latency interpretation. The sequential Settings B repeat still failed to terminate. The suite lock was added after discovering overlap.
- Fourteen early capture records had a shared-file run-label error. The original file is preserved as `model-calls-original-before-attribution-fix.jsonl`. Canonical records in `model-calls.jsonl` use their request's `user` field; affected-era rows retain `original_recorded_run_id`. No model text, tool calls, timing values or outcomes were changed during that correction.
- The proxy forwards non-streaming requests, doesn't record or forward authentication headers, and replaces embedded image data in its capture with hashed image files. Original Harness evidence retains the tool observations.
- Coordinate-adapted records retain both the original model response and the delivered response, with every 0–1000-to-pixel transform recorded. The adapter applies only to `web_click_point` for run IDs starting `coordinate-adapted-`, with a fixed 1280 × 720 viewport.
- Prompts, fixtures, model settings, SHA-256 hashes and failed attempts remain visible. The synthetic task set is small and manually authored; there is no held-out benchmark claim or population reliability estimate.
- Public evidence replaces only local controller-root path strings with `$LAB_ROOT`. This doesn't alter task content or measurements. Raw task videos and screenshots are unmodified.
- Reported decode speed uses llama.cpp `predicted_n / predicted_ms`; it excludes image processing, prefill and browser/tool time. Three runs affected by overlap aren't used for single-task wall-time claims.
- Configured 128K capacity was not filled by these tasks. GPU memory is a loaded-idle observation rather than a measured peak. No energy measurements, Mini comparison or native Desktop acceptance is claimed.
