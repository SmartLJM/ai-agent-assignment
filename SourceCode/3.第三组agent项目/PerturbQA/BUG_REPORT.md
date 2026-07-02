# Benchmark Runner Hang Bug

## Summary

`node_modules/.bin/tsx src/evaluation/runner.ts 2>&1` ran in the background as task `bc0enomo8`, but the benchmark stopped making progress at question `gp-017`.

The process did not crash or exit. It stayed alive with near-zero CPU usage and no new log output, which indicates a hang while waiting for an async operation to complete.

## Observed State

- Command: `node_modules/.bin/tsx src/evaluation/runner.ts 2>&1`
- Main Node process: `PID 530826`
- Parent shell process: `PID 530824`
- Working directory: `/home/duanyu/Python/Myproject/perturbqa`
- Real output file:
  `/tmp/claude-1000/-home-duanyu-Python-Myproject-perturbqa/b46821bb-5a76-430d-95fe-45964dbb5bdf/tasks/bc0enomo8.output`
- Last output file modification time: `2026-06-02 23:36:33 +0800`
- Process inspection time: `2026-06-03 00:04:54 +0800`
- Last visible benchmark item:
  `[17/22] gp-017: What is the Perturb-CITE-seq method and what additional info...`
- Process state:
  - `PID 530826` was in `ep_poll`
  - CPU usage was `0.0%`
  - The process tree was still alive under the parent shell

## Evidence From Logs

The benchmark successfully completed questions `gp-001` through `gp-016`, printing scores and PASS/FAIL statuses. It then printed the start of `gp-017` but never printed a score, PASS/FAIL status, error, or final benchmark summary.

This means the runner most likely entered `gp-017`, started processing it, and then waited indefinitely before returning a result.

## Likely Cause

This is likely a hang in an async LLM or agent call rather than a normal long-running computation.

Relevant code:

- `src/evaluation/runner.ts` calls `await runWithPiAgent(q.question, store)` for each question.
- `src/agents/pi-agent.ts` calls `await complete(...)` inside the Pi agent loop.
- `src/evaluation/runner.ts` later calls `await autoScore(...)`, which uses `callPiModel(...)`.
- Neither the per-question runner call nor the model calls have an explicit timeout.

Because the benchmark loop is serial, one stuck Promise blocks all remaining questions.

## Impact

- The benchmark can hang forever on a single question.
- No partial result file is written until the full loop completes.
- Questions after the stuck item are never evaluated.
- The process may appear "running" even though it is no longer making progress.

## Recommended Fix

Add timeout protection around each benchmark question, and preferably around each model call.

Suggested behavior:

- Apply a per-question timeout, for example 2-5 minutes.
- On timeout, record the question as failed with `generatedAnswer: "TIMEOUT"`.
- Continue to the next benchmark question.
- Write partial progress incrementally, or at least after each question, so completed results are not lost.

Potential implementation points:

- Wrap `runWithPiAgent(...)` in `src/evaluation/runner.ts` with a timeout helper.
- Wrap `autoScore(...)` with the same timeout helper.
- Consider adding a lower-level timeout to `complete(...)` and `completeSimple(...)` calls if the Pi API supports abort signals.

## Immediate Recovery

If this exact process is still running and no longer needed, terminate the parent shell or Node process:

```bash
kill 530824
```

Then rerun the benchmark after adding timeout handling, or rerun only the remaining IDs if partial results are available.
