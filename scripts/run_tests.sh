#!/usr/bin/env bash
# ---------------------------------------------------------------------------
# Single entry point for running tests locally and in CI.
#
#   ./scripts/run_tests.sh                                  # qa / android / sauce_vdc / smoke
#   ./scripts/run_tests.sh -e staging -p ios -t sauce_rdc
#   ./scripts/run_tests.sh -i regression -x flaky
#   ./scripts/run_tests.sh -s tests/mobile/shared/login_tests.robot
#   ./scripts/run_tests.sh -P 4                             # 4 parallel processes via pabot
#
# Exit code is Robot's: 0 = all passed, 1-249 = that many tests failed.
# ---------------------------------------------------------------------------
set -euo pipefail

cd "$(dirname "$0")/.."

ENVIRONMENT="${TEST_ENV:-qa}"
PLATFORM="${PLATFORM:-android}"
TARGET="${TEST_TARGET:-sauce_vdc}"
SUITE="tests/mobile"
INCLUDE="smoke"
EXCLUDE=""
PROCESSES="0"
RERUN="1"
EXTRA=()

usage() {
    sed -n '2,14p' "$0" | sed 's/^# \{0,1\}//'
    exit "${1:-0}"
}

while getopts ":e:p:t:s:i:x:P:r:h" opt; do
    case "${opt}" in
        e) ENVIRONMENT="${OPTARG}" ;;
        p) PLATFORM="${OPTARG}" ;;
        t) TARGET="${OPTARG}" ;;
        s) SUITE="${OPTARG}" ;;
        i) INCLUDE="${OPTARG}" ;;
        x) EXCLUDE="${OPTARG}" ;;
        P) PROCESSES="${OPTARG}" ;;
        r) RERUN="${OPTARG}" ;;
        h) usage 0 ;;
        \?) echo "Unknown option -${OPTARG}" >&2; usage 1 ;;
    esac
done
shift $((OPTIND - 1))
EXTRA=("$@")

# --- Production guard rail --------------------------------------------------
# Nothing that mutates state is allowed to run against prod, whatever the caller
# asked for. This is deliberately not overridable by a flag.
if [[ "${ENVIRONMENT}" == "prod" ]]; then
    echo "prod detected: forcing --include smoke and --exclude destructive" >&2
    INCLUDE="smoke"
    EXCLUDE="${EXCLUDE:+${EXCLUDE}AND}destructive"
fi

case "${PLATFORM}" in
    ios)     PLATFORM_LABEL="iOS" ;;
    android) PLATFORM_LABEL="Android" ;;
    *)       PLATFORM_LABEL="${PLATFORM}" ;;
esac

TIMESTAMP="$(date -u +%Y%m%d-%H%M%S)"
OUTPUT_DIR="results/${ENVIRONMENT}-${PLATFORM}-${TIMESTAMP}"
mkdir -p "${OUTPUT_DIR}"

ROBOT_ARGS=(
    --pythonpath .
    --variablefile "config/variables.py:${ENVIRONMENT}:${PLATFORM}:${TARGET}"
    --listener libs.listeners.EvidenceListener
    --listener "allure_robotframework:${OUTPUT_DIR}/allure-results"
    --outputdir "${OUTPUT_DIR}"
    --report report.html
    --log log.html
    --output output.xml
    --xunit xunit.xml
    --reporttitle "${PLATFORM_LABEL} ${ENVIRONMENT} - ${TIMESTAMP}"
    --name "Mobile ${PLATFORM_LABEL} ${ENVIRONMENT^^}"
    --metadata "Platform:${PLATFORM}"
    --metadata "Environment:${ENVIRONMENT}"
    --metadata "Target:${TARGET}"
    --consolewidth 120
    --removekeywords WUKS
)

[[ -n "${INCLUDE}" ]] && ROBOT_ARGS+=(--include "${INCLUDE}")
[[ -n "${EXCLUDE}" ]] && ROBOT_ARGS+=(--exclude "${EXCLUDE}")

# Android-only and iOS-only suites are skipped by path, not by a runtime Skip,
# so the report is not littered with dozens of skipped tests.
if [[ "${PLATFORM}" == "android" && "${SUITE}" == "tests/mobile" ]]; then
    ROBOT_ARGS+=(--exclude ios-only)
elif [[ "${PLATFORM}" == "ios" && "${SUITE}" == "tests/mobile" ]]; then
    ROBOT_ARGS+=(--exclude android-only)
fi

echo "=============================================================="
echo " env=${ENVIRONMENT} platform=${PLATFORM} target=${TARGET}"
echo " suite=${SUITE} include=${INCLUDE:-<all>} exclude=${EXCLUDE:-<none>}"
echo " output=${OUTPUT_DIR}"
echo "=============================================================="

set +e
if [[ "${PROCESSES}" -gt 0 ]]; then
    pabot --processes "${PROCESSES}" --testlevelsplit "${ROBOT_ARGS[@]}" "${EXTRA[@]}" "${SUITE}"
else
    robot "${ROBOT_ARGS[@]}" "${EXTRA[@]}" "${SUITE}"
fi
STATUS=$?
set -e

# --- Rerun failures once ----------------------------------------------------
# Mobile cloud runs have real infrastructure flake. One rerun keeps the signal
# honest; more than one hides genuinely unstable tests.
if [[ ${STATUS} -ne 0 && "${RERUN}" -gt 0 && -f "${OUTPUT_DIR}/output.xml" ]]; then
    echo "--- rerunning failed tests once ---"
    set +e
    robot "${ROBOT_ARGS[@]}" \
        --rerunfailed "${OUTPUT_DIR}/output.xml" \
        --output rerun.xml \
        --log rerun-log.html \
        --report rerun-report.html \
        "${EXTRA[@]}" "${SUITE}"
    RERUN_STATUS=$?
    set -e
    if [[ -f "${OUTPUT_DIR}/rerun.xml" ]]; then
        rebot --outputdir "${OUTPUT_DIR}" \
              --output merged.xml --log log.html --report report.html --xunit xunit.xml \
              --merge "${OUTPUT_DIR}/output.xml" "${OUTPUT_DIR}/rerun.xml"
        STATUS=$?
    else
        STATUS=${RERUN_STATUS}
    fi
fi

# Stable path for CI artifact upload, so workflows never guess the timestamp.
ln -sfn "$(basename "${OUTPUT_DIR}")" results/latest

echo "Report: ${OUTPUT_DIR}/report.html"
exit ${STATUS}
