# test

The suite started. An expectation failed. Quote the test name and the expected versus received values.

## When to follow this

The CLI category is `test`. Signals include `AssertionError`, `expect(received)`, a `FAIL path` line, `--- FAIL:` from `go test`, `Expected:`, pytest `FAILED path`, `Failed asserting that` (PHPUnit), `Failure/Error:` (RSpec), and `test result: FAILED` (cargo).

Corpus: `npm-test-assertion`, `pytest-assertion`, `go-test-want-got`, `maven-surefire-assertion`, `phpunit-assert-failed`, `rspec-failure-error`, `cargo-test-result-failed`, `gradle-test-assertion`.

## Near misses

| What you see | What to do |
| --- | --- |
| The same assertion and "Exceeded timeout of N" tie (`timeout-and-assertion-unknown`) | Stay `unknown`. Do not "fix" the assertion until a rerun shows the assertion without the timeout, or the reverse. |
| Timeout or "passed on the previous run" outranks the assertion | Follow `flake`. A deterministic assertion that never moves is not flake. |
| `ERESOLVE` or lockfile drift, and the suite never printed a test summary | Follow `deps`. A stray `FAIL` line under a heap OOM is `infra` when infra leads, as in the heap fixture. |
| Confidence is medium because `alternates` contains `infra` | Quote both lines. If the runner was killed, do not edit the assertion to absorb it. |

## Recipe

1. Quote the test id (file, example name, or `--- FAIL:` / `Failure/Error:` / `FAILED` line) and the expected versus received values. If the log has only `test result: FAILED`, say the count and ask for the failing test name before editing.
2. Decide which side is wrong from the evidence, in one sentence: the product behavior or the assertion. If you cannot tell, say so and do not edit yet. Asking is not an attempt.
3. Propose one edit:
   - change the product code the test names, or
   - change the assertion when the log shows the test's expectation is stale.
4. Do not delete, skip, `.only`, `#[ignore]`, or `xtest` the test to force a green job.
5. Do not treat a deterministic `AssertionError` / `Failed asserting that` / RSpec `Failure/Error` as a flake.

## Verify

- Reproduce with the command the job ran (`npm test`, `pytest`, `go test`, `mvn -q test`, `vendor/bin/phpunit`, `bundle exec rspec`, `cargo test`). Name that command in the report.
- Then re-run that job or that single test. The edit plus this check is one attempt.
- Same failure: same test id, same expected and received.
- New failure: a different test or a different expected/received pair. That is a new hypothesis. A second edit is attempt 2.
- Fixture check does not prove the product fix. It only re-reads the saved log.

## Stop

- Two unsuccessful edits. Summarize both diffs and the last evidence. Do not widen into a refactor.
- You still cannot see expected versus received. Stop and ask for the assertion block. Do not rewrite the module "while you are here".
- The failure changed into a timeout that passes on rerun, or into an OOM line. Switch playbooks. If that was already attempt 2, report the new category and stop.

## 中文

引用测试名和期望值/实际值。只改产品代码或断言其中一边。不要删除、跳过或 `.only` 测试来换绿。`timeout-and-assertion-unknown` 是打平，先别改断言。`cargo` 只有 `test result: FAILED` 时，先要失败用例的名字，这还不算一次尝试。用日志里的同一条命令复现；第二次仍失败就停下并总结两次 diff。
