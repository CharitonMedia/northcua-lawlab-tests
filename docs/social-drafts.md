# Social publication drafts

Status: prepared for publication; not posted to either platform.

## X

NorthCUA-Nano on one RTX 3090 completed 3 of 6 browser tasks. Four saved correct data, but one kept looping. We published the failures, videos and a coordinate-adapter follow-up, plus the scripts to repeat the tests.
https://github.com/CharitonMedia/northcua-lawlab-tests

## Facebook

We tested a 9B computer-use model on a single RTX 3090. NorthCUA-Nano completed three of six baseline browser tasks.

It selected the correct in-stock product and submitted two test orders with the right quantities and totals. It also completed a settings task across two tabs.

The failures were instructive. Two forms stopped because the model supplied a date format the browser tool rejected. Another run saved every requested setting but kept switching tabs until it hit the step limit.

We also tried a visual target board. The model returned coordinates on a 0–1000 scale while the browser expected pixels. Both clicks missed, and it still claimed success. In a separate run, an explicit coordinate adapter converted the positions and both clicks registered correctly.

The public repository includes all 12 model runs, continuous browser recordings, raw traces, model hashes and the analysis. Date-format hints and coordinate conversion are labeled as assisted follow-ups.

The small task set doesn't establish general reliability. It does show why checking the saved result matters.

Watch the successful runs and the failures:
https://github.com/CharitonMedia/northcua-lawlab-tests
