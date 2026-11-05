# rebalance-min-tail-11-05-26.plan-review

## Round 1 — 11-05-26

```
verdict: rejected
next: plan-wrong
blocking: 1
non-blocking: 3
```

### Findings
- [blocking] `parse_range` `lo < 0` branch (plan 3.1) is unreachable, and 4.1's test advice is wrong. rebalance_due.py:54-78 does `text.split("-", 1)`, so any string with a leading `-` (e.g. `-1-30`, `-1-5`) gives `lo_str == ""`, `int("")` raises, and the result is the "malformed" message, not an LO message. Once the `lo < 1` check is relaxed, no input can produce a negative LO. Consequences: (a) the new `--range START must be >= 0` message is dead code, contradicting the plan's own delete-dead-code convention; (b) 4.1's rewrite of `test_e2e_range_invalid_forms_each_get_a_distinct_message` ("use a negative LO such as `-1-30`") would yield the same text as `abc`, so `len({msg_lo, msg_hi, msg_malformed}) == 3` fails; only two distinct failure modes remain reachable (malformed, HI<LO); (c) 1.1 case 5 (`parse_range("-1-5")` raises ValueError) is true but only via the malformed path. Planner must either drop the LO branch and reduce the test to two distinct messages, or change parsing so a negative start is intentionally detected (and say so).
- [non-blocking] 2.1/2.2: `move_card` only ever grows `end_day` (due_plan.py:484-493), so in no-range mode the gate window is the original latest day or later. The tail cannot shrink out of the gate. This matches R1 (verified), but 2.1 should say explicitly that the gate uses the live `state.end_day`.
- [non-blocking] Plan cites `plan_rebalance` flat branch at 940-942 and `_check_post_conditions` max loop at 783-788; verified close (784 loop present). Line refs for README docs (lines 52-87, 257 etc.) were not re-verified here (Record stage).
- [non-blocking] `plan-lifecycle.sh check` could not run on a proposal file (it requires a directory under the plans dir: "usage: check [<path>]", exit 1). validate-plan.sh passed ("structurally valid (7 subphases)"). Re-run `check` after promotion.

### Verified
- Exempt tail: `_reached_exempt_tail` (542), callers `apply_min_pass` (552-554) and `_short_days` (720-725) exist as described; `apply_min_pass` only searches later sources (`range(d+1, end_day+1)`) and has no `set_earlier` argument, confirming the repro cause.
- `plan_rebalance` flat/sliding branches (~908-945), `later_move_used` at 908, `_check_post_conditions` call at 954 match.
- `--start-offset` default is 1 in both rebalance_due.py:361 and due_stats.py:86; `start_day = today + args.start_offset` (492); `collect_cards` skips `card.due < start_day` (161-163), so start offset 0 includes today and excludes overdue. `plan_rebalance`, `parse_range`, `short_days` are used only by due_stats.py, due_plan.py, rebalance_due.py (the plan's unverified assumption is confirmed for `anki_tools/`).
- Precheck: global upper-bound downgrade under `--set-earlier` (1121-1125), global lower bound (1130-1138), `suggested_min = total // horizon_days` (1183), `window_violations` (1034-1076) exist as described; min-side Hall condition design is a sound necessary condition.
- Single lane serial: all scopes overlap the shared files, so no lane disjointness issue.
- Ask diff: no missing, extra, or inverted deliverable (hard min, today included, exempt tail removed, fail on unmet, start/stop window with 0 = today default). Not flagged.

### Open questions
- 3.1: Drop the `lo < 0` branch (parse_range cannot see negatives), or intentionally parse negative starts to give a dedicated message? The user said "take in a start and stop day"; negative starts are out of scope either way.

## Round 2 — 11-05-26

```
verdict: ready
next: proceed
blocking: 0
non-blocking: 1
```

### Findings
- [non-blocking] Plan-review `check` still cannot run on a proposal file; re-run `plan-lifecycle.sh check` after promotion. README line refs in the Record paragraph remain unverified (Record stage).

### Verified
- Round-1 blocker resolved: 3.1 now deletes the `lo < 1` branch with no replacement. rebalance_due.py:54-78 confirms `split("-", 1)` sends any leading `-` to the malformed path, so no negative start is reachable; the two remaining failure modes (malformed, HI < LO) keep distinct messages.
- 4.1 now reduces `test_e2e_range_invalid_forms_each_get_a_distinct_message` (test_rebalance_due.py:1736) to two forms with `len({msg_hi, msg_malformed}) == 2`, and explicitly warns against a negative-start substitute. Consistent with the code.
- 1.1 case 5: `parse_range("0-10")`, `"0"` pass once `lo < 1` is gone (bare `0` yields lo=hi=0); `"-1-5"` raises via the malformed path.
- Round-1 non-blocking note adopted: 2.1 item 4 specifies the live `state.end_day` at gate time; `move_card` (due_plan.py:484-493) only grows it.
- `validate-plan.sh`: "OK: plan is structurally valid (7 subphases)".
- Ask diff: no missing, extra, or inverted deliverable.

### Open questions
- None.
