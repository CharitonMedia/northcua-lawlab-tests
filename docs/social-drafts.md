# Follow-up publication drafts

Status: prepared, not posted.

## X

NorthCUA-Nano on one RTX 3090: fixing coordinate handling, recovery and a missing browser system prompt took our six original tasks from 3/6 to 6/6. Four task variations passed too. Code, failures and videos:
https://github.com/CharitonMedia/northcua-lawlab-tests

## Facebook

NorthCUA-Nano went from completing three of our six browser tasks to completing all six after we fixed the harness.

The most revealing discovery was in the requests sent to the model. The generated setup was using NexAU's generic default prompt, including a line saying no tools were available. The browser-specific instructions weren't being sent.

We fixed that path, added coordinate conversion based on the current viewport, and gave malformed dates a bounded correction path. We also corrected a recovery-message delivery problem and added a configurable check for visible completion receipts.

The final configuration passed the six original tasks, the original visual-clicking probe and four additional task variations. One moved the targets and changed the viewport to 1440 by 900.

This is a small synthetic test set. Every final result was checked against saved fixture data. The public repository preserves all 41 model runs, including unsuccessful development stages, with source, patches and continuous browser recordings.

The before-and-after analysis and videos are here:
https://github.com/CharitonMedia/northcua-lawlab-tests/blob/main/docs/hardening.md
