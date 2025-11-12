---
applyTo: '**'
---
Whenever you run pytest directly, ALWAYS direct the output into a file in {rootdir}/tmp and evaluate that file. Full test runs take 30+ minutes.

Do NOT do calls like "pytest test/ {args} 2>&1 | Select-String -Pattern "FAILED|PASSED|SKIPPED" | Select-Object -Last 50" as those lose ALL the error details.

If you want to validate a particular issue run one or two targeted tests; never run the full suite unless told.