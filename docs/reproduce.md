# Reproduce the Nano experiments

Use a Linux browser-controller host with Python 3.12 and uv 0.13.6 or newer. The tested GPU host had a 24 GB RTX 3090 and NVIDIA driver 595.99.02. Keep model serving separate from the Harness environment.

## 1. Model files and inference

Download `NorthCUA-Nano.Q8_0.gguf` and `NorthCUA-Nano.mmproj-f16.gguf` from [mradermacher/NorthCUA-Nano-GGUF](https://huggingface.co/mradermacher/NorthCUA-Nano-GGUF). Verify their hashes against [the manifest](../results/environment/manifest.json). Model weights aren't duplicated in this repository.

On the GPU host, after reviewing the launcher:

```sh
export MODEL_DIR=/path/to/NorthCUA-Nano-GGUF
bash scripts/launch_model.sh
curl http://127.0.0.1:19093/health
```

The launcher pins the tested image digest and checks that the selected GPU is a 3090. It binds only loopback and creates a temporary container without restart persistence. Wait for `{"status":"ok"}` before running tasks.

If the browser controller is on another host:

```sh
ssh -NT -L 127.0.0.1:19093:127.0.0.1:19093 YOUR_GPU_HOST
```

## 2. Harness and browser

From the root of this experiment repository:

```sh
mkdir -p vendor .runtime
git clone https://github.com/beipo-ai/NorthCUA.git vendor/NorthCUA
git -C vendor/NorthCUA checkout b904a8fc4fbc16de0197a142f6dd9ab2bd36ffff
cd vendor/NorthCUA
uv sync --locked --python 3.12 --extra local --extra device
uv run --no-sync playwright install chromium
cd ../..
```

Install browser OS dependencies if your machine needs them, following the upstream first-run guide. See the upstream dependency disclosure for its locked NexAU/Transformers environment.

## 3. Services and a fresh run

Start each service in a separate terminal, with this repository as the working directory:

```sh
python3 scripts/fixture_server.py
python3 scripts/capture_proxy.py
```

Then choose a fresh tag so existing evidence isn't overwritten:

```sh
python3 scripts/run_suite.py --case shop-a --tag my-first-run
```

The runner supplies a dummy local API key, records continuous browser video through an opt-in Playwright hook, runs the real model with screenshots and tools, and compares the fixture receipt with the expected values. The dummy key isn't a provider credential; it isn't forwarded by the proxy.

For the six baseline cases, execute one at a time:

```sh
for task in project-a shop-a settings-a project-b shop-b settings-b; do
  python3 scripts/run_suite.py --case "$task" --tag replica
done
```

Explicit follow-ups:

```sh
python3 scripts/run_suite.py --case project-a --tag replica-iso --iso-date-hint
python3 scripts/run_suite.py --case vision-a --tag replica-visual
python3 scripts/run_suite.py --case vision-a --tag coordinate-adapted-replica
python3 scripts/analyze.py
```

The `coordinate-adapted-` run prefix enables the separately logged, fixed-viewport coordinate adapter in `capture_proxy.py`. Other run names receive unmodified coordinates. This adapter changes tool arguments, so label its results separately. The date hint changes the prompt and also needs separate reporting.

The runner uses a process lock. Don't bypass it by launching separate harness processes if you intend to compare single-task latency. The summary retains overlap flags for the original experiment.

## 4. Inspect and clean up

For each run compare `results/runs/RUN_ID/outcome.json` with `results/harness/RUN_ID/result.json` and the fixture receipt. A successful harness status alone doesn't prove the requested action occurred.

Stop the fixture and proxy terminals, close the SSH tunnel, and stop the temporary model container after testing:

```sh
docker stop northcua-nano-3090-test
```

Original WebM recordings are under each run's `video/` directory. MP4 files in `results/videos/` are ordinary real-time transcodes for viewing. The analysis script is read-only against raw run evidence and rewrites only its derived CSV/JSON summaries.
