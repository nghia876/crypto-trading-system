# Scoped Windows execution guideline - 2026-11-01

Applies to subsequent development of this repository on this Windows host.

## Later user authorization: full validated Phase 3 backup

The user subsequently requested review and GitHub backup of all current Phase 3
work, and authorized the offered temporary, one-window execution-policy change.
This supersedes the earlier backup limit through 8717005 below. Use the newly
reviewed parent-workspace Push-Phase3-Validated-Backup.ps1 in ordinary non-elevated
host Windows PowerShell, with RemoteSigned at Process scope only. Close that
window afterward. No persistent execution-policy change, Bypass/Unrestricted,
Defender setting change, exclusion, threat restoration or retry after a Defender
block is authorized. The script pins the reviewed commit and exact history,
requires a clean tracked tree and the expected remote, and verifies the push.
This exception does not authorize any other security-setting changes or script.

## Evidence and uncertainty

The user reports Defender detected `Ransom:PowerShell/FileFix.DZ!MTB` at
2026-11-01 11:01, status Removed. The supplied command description identifies
the Work runtime's `pwsh.exe -Command` with a large Python here-string piped
to `Set-Content tradingagents/information/event_evaluation.py`, and generated
test fixtures. User reports a subsequent Microsoft Defender FULL scan found
NO THREATS. These are supplied security observations; the original Defender
event and removed artifact were not independently recovered in this session.

Inspected repository source implements offline synthetic event evaluation;
no download, encryption or token exfiltration behavior was observed in that
source. This is limited code evidence, not proof about every process or the
removed artifact. A command-shape heuristic false positive is a possible
explanation, not an established root cause. Do not claim a verified false
positive or a malware-free machine from the clean scan.

## Required workflow

- Use direct file editing/patch tools. Do not inject large source files through
  monolithic PowerShell `-Command` here-strings, pipelines or encoded commands.
  Keep necessary shell commands small, literal, auditable and unencoded.
- Inspect scripts before execution, including their paths, inputs, network
  behavior and mutations. Reuse reviewed existing local dependencies; no
  unreviewed downloads, installers or remote-script execution.
- Use ordinary non-elevated permissions and the current checkout/canonical
  evidence store. Restrict writes to intended files. Never modify synced
  `sources/` or `.phase12-tools/`. Stage explicit paths only.
- Never disable Defender, change security settings except the user-authorized
  temporary Process-scope RemoteSigned adjustment above, add exclusions, restore
  blocked threats, or make any other execution-policy change to make a command run.
- If Defender blocks again, stop the affected execution immediately. Record
  the exact path/command and reported detection/status; report the result.
  Do not retry, rename, encode, switch runtimes or otherwise bypass the block.
- Do not repeat the known failing Work Git/MSYS credential-helper method.
  The following narrower backup authorization is historical and superseded by
  the later explicit authorization above.
  Authorized backup through `8717005bc505bfd66c3206c40a49140193291890`
  uses the reviewed parent-workspace `Push-Phase33-Authorized.ps1` only in
  ordinary non-elevated host Windows PowerShell. Its pinned SHA refspec must
  exclude Phase 3.4 and every later commit. No force, merge, rewrite or main
  operation. Verify the remote SHA after pushing. Keep local development
  moving if ordinary host execution is unavailable.

No new security alert was observed through the execution tools during this
change. This is not a Defender event-log audit or proof that no alert occurred.
