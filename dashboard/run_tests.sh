#!/usr/bin/env bash
# Run the regression suite with each test FILE in its own process.
#
# Why: several unit-test files (test_foundation_unit, test_what_changed_unit,
# test_score_explainer_unit, test_universe_unit, test_model_validation_unit)
# install stub modules into sys.modules (utils.config, utils.taxonomy) at import
# time so they can test pure engines without the real config/DB. When the whole
# suite runs in ONE process, whichever file is imported first wins that slot, so
# the others silently receive the wrong module and fail (e.g. `assert 5 == 47`).
# Running each file in its own interpreter gives every file a clean sys.modules.
#
# Plain `pytest tests/` still works for the page/DB tests; this script is the
# reliable way to run EVERYTHING green in one command.
#
# Usage:  bash run_tests.sh            # run all test files, isolated
#         bash run_tests.sh -v         # pass extra args through to pytest
set -u
cd "$(dirname "$0")"

fail=0
failed_files=""
for f in tests/test_*.py; do
    echo "──────────────────────────────────────────────────────────────"
    echo "▶ $f"
    if ! python -m pytest "$f" -q "$@"; then
        fail=1
        failed_files="$failed_files $f"
    fi
done

echo "══════════════════════════════════════════════════════════════"
if [ "$fail" -eq 0 ]; then
    echo "✅ All test files passed."
else
    echo "❌ Failing files:$failed_files"
fi
exit $fail
