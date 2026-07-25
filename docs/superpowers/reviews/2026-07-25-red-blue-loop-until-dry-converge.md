# Converge — force `loop-until-dry` in red/blue rules (2026-07-25)

**Trigger:** User required `loop-until-dry` as a **forced** red/blue rule after scorecard adversarial run.  
**Process:** Sequential red→blue on the rule text itself (**loop-until-dry**).

## Rounds

| Round | What happened |
|------:|---------------|
| 1 | Draft `.cursor/rules/red-blue-adversarial.mdc` + git-commit pointer + scorecard converge note |
| 1 `/review-pr` | Critical: skip re-attack after Apply; not-dry missing from hard blockers; soft Prefer artifacts; narrow trigger |
| 2 | Hardened: mandatory re-attack after claim-relevant Apply; MUST artifacts + dry attestation; broadened triggers; git-commit hard blocker for not-dry |
| 2 re-pass | code-reviewer + silent-failure → **Critical=0** → **dry** |

## Dry checklist

- [x] Critical = 0 open  
- [x] Important deferred/none blocking (residual “claim-relevant” gaming ~70% noted, not Critical)  
- [x] Post-Apply re-attack run; no new Critical  
- [x] Partner/claim narrative N/A (rule process, not product scorecard)  
- [x] This attestation records rounds + dry  

## Applied files

- `.cursor/rules/red-blue-adversarial.mdc` (new, `alwaysApply`)
- `.cursor/rules/git-commit-workflow.mdc` (pointer + hard blocker)
- `docs/superpowers/reviews/2026-07-25-lumi-scorecard-converge.md` (retrospective note)
