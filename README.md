# Mobile Automation Framework

Robot Framework + Appium + Sauce Labs. Python 3.11.

One test suite runs on **both Android and iOS** — the platform is a runtime
argument, not a copy of the code. Web and API layers have their seams cut
already, so adding them later is additive rather than a rewrite.

---

## Quick start

```bash
git clone https://github.com/desaivatsal/mobile-automation-framework.git
cd mobile-automation-framework

python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt -r requirements-dev.txt

cp .env.example .env          # then fill in SAUCE_USERNAME and SAUCE_ACCESS_KEY

python scripts/list_sauce_apps.py     # see what is in your Sauce app storage
#   -> paste the real file names into config/apps.yaml

./scripts/run_tests.sh -e qa -p android -i smoke
```

`SAUCE_USERNAME` is the username on
<https://app.saucelabs.com/user-settings> — **not** your login email. Getting
this wrong is the single most common cause of `Unauthorized`.

---

## Running tests

Everything goes through one entry point:

```bash
./scripts/run_tests.sh [-e env] [-p platform] [-t target] [-i tags] [-x tags] [-s suite] [-P n] [-r 0|1]
```

| Flag | Meaning | Values | Default |
|------|---------|--------|---------|
| `-e` | Environment | `dev` `qa` `staging` `prod` | `qa` |
| `-p` | Platform | `android` `ios` | `android` |
| `-t` | Where it runs | `sauce_vdc` `sauce_rdc` `local` | `sauce_vdc` |
| `-i` | Include tags | any Robot tag expression | `smoke` |
| `-x` | Exclude tags | any Robot tag expression | — |
| `-s` | Suite or file | path | `tests/mobile` |
| `-P` | Parallel processes (pabot) | integer | `0` (serial) |
| `-r` | Rerun failures once | `0` `1` | `1` |

```bash
./scripts/run_tests.sh                                          # qa / android / smoke
./scripts/run_tests.sh -e staging -p ios -i regression
./scripts/run_tests.sh -t sauce_rdc -p android -i smoke         # real devices
./scripts/run_tests.sh -s tests/mobile/shared/login_tests.robot -i ""
./scripts/run_tests.sh -P 4                                     # 4 parallel sessions
./scripts/run_tests.sh -p ios -i smoke -- --dryrun              # validate, no device
```

`prod` is guard-railed: the runner forces `--include smoke --exclude destructive`
regardless of what you asked for. That is not overridable by a flag, on purpose.

---

## The four requirements

### 1. Environments

Configuration is layered and deep-merged, lowest precedence first:

```
config/default.yaml
  -> config/platforms/<android|ios>.yaml
    -> config/environments/<dev|qa|staging|prod>.yaml
      -> environment variables (and .env locally)
        -> --variable on the command line
```

`config/variables.py` is the single Robot entry point
(`--variablefile config/variables.py:qa:android:sauce_vdc`). Adding a fifth
environment means adding one YAML file — no code changes.

Per-environment test data lives in `testdata/<env>.yaml` and reaches tests as
`${TEST_DATA}`. Tests never hardcode a username.

### 2. Page Object Model

Three layers, strictly separated:

```
resources/locators/<platform>/<screen>_locators.resource   data only, no logic
resources/pages/<screen>_page.resource                     keywords only
tests/mobile/**/*.robot                                    assertions only, no locators
```

The Android and iOS locator files declare **the same variable names**. A page
object imports `../locators/${PLATFORM}/...`, so one set of page keywords drives
both platforms. Where a flow genuinely differs, branch on `$IS_ANDROID` inside
the page object — never in a test.

Shared building blocks live in `resources/common/`:

| File | Purpose |
|------|---------|
| `libraries.resource` | the only place libraries are imported |
| `waits.resource` | explicit waits with diagnosable failure messages |
| `gestures.resource` | swipe / scroll / keyboard, normalised across platforms |
| `assertions.resource` | assertions that say what was expected and what was found |
| `locator_utils.resource` | parameterised locator templating |
| `session.resource` | suite and test setup/teardown |
| `imports.resource` | aggregate import surface for page objects |

**Dependencies** are pinned in `requirements.txt` (runtime),
`requirements-dev.txt` (lint/test), `requirements-web.txt` and
`requirements-api.txt` (optional layers). `pyproject.toml` holds tool
configuration. Dependabot raises weekly grouped upgrade PRs.

### 3. Continuous integration

| Workflow | Trigger | Secrets needed | What it does |
|----------|---------|----------------|--------------|
| `ci.yml` | every push and PR | none | ruff, black, robocop, unit tests, `robot --dryrun` for both platforms |
| `mobile-tests.yml` | push to main, nightly 02:00 UTC, manual | Sauce | real Sauce runs, matrix android/ios, artifacts, JUnit summary, Pages report |

`ci.yml` needs no secrets and finishes in about a minute — it catches broken
imports and typo'd keyword names before anything spends device minutes.

Set these up once:

- **Settings → Secrets and variables → Actions → Secrets**: `SAUCE_USERNAME`, `SAUCE_ACCESS_KEY`
- **Settings → Secrets and variables → Actions → Variables** *(optional)*: `SAUCE_REGION`
- **Settings → Pages → Source: GitHub Actions** *(optional, for hosted reports)*

Manual runs (**Actions → Mobile Tests → Run workflow**) take environment,
platform, device cloud, tag expression and app key as inputs.

### 4. Reporting, logging, screenshots

| Artefact | Where |
|----------|-------|
| Robot report + log | `results/<env>-<platform>-<timestamp>/report.html`, `log.html` |
| JUnit XML | `.../xunit.xml` — feeds the GitHub checks summary |
| Allure results | `.../allure-results/` — run `allure serve` on them |
| Failure screenshots | `.../screenshots/`, also embedded in `log.html` |
| Page source at failure | `.../page_source/*.xml` |
| Plain-text log | `results/logs/execution.log`, rotated at 10 MB × 5 |
| Sauce video + device log | linked from the Robot log, one click per failure |

`libs/listeners/EvidenceListener.py` captures evidence **at the moment a keyword
fails**, while the driver is still alive — not in teardown, by which point the
app may already be reset. Policy is per environment
(`reporting.screenshot_policy`: `failures_only`, `full`, `none`).

The Sauce job is named after the running test and its pass/fail status is pushed
back to the dashboard; Appium will not do that for you.

---

## Layout

```
.
├── .github/workflows/       ci.yml (no secrets) + mobile-tests.yml (Sauce)
├── config/
│   ├── default.yaml         base configuration
│   ├── apps.yaml            app registry: app_key -> Sauce storage reference
│   ├── environments/        dev / qa / staging / prod overrides
│   ├── platforms/           android / ios capabilities, per execution target
│   └── variables.py         Robot variable file - the single config entry point
├── libs/
│   ├── config_loader.py     layered YAML merge + validation
│   ├── capabilities.py      W3C capability construction (unit-tested)
│   ├── sauce_client.py      Sauce REST: job status, app storage
│   ├── MobileSession.py     Robot library: session lifecycle, retries, job links
│   ├── listeners/           EvidenceListener - screenshots, page source, links
│   └── utils/logger.py      rotating file log bridged into the Robot log
├── resources/
│   ├── common/              waits, gestures, assertions, session, imports
│   ├── locators/android|ios data only, matching variable names per platform
│   ├── pages/               page objects shared across platforms
│   └── web/  api/           extension points (see their READMEs)
├── tests/
│   ├── mobile/shared/       cross-platform suites (login, products, cart)
│   ├── mobile/android|ios/  platform-specific behaviour only
│   ├── unit/                pytest for the Python layer - no device needed
│   └── web/  api/           extension points
├── testdata/                per-environment data, exposed as ${TEST_DATA}
└── scripts/
    ├── run_tests.sh         single entry point
    ├── list_sauce_apps.py   print what is in Sauce app storage
    └── upload_app.py        upload an .apk/.ipa to Sauce app storage
```

---

## Adding a test

1. Add locators to **both** `resources/locators/android/` and
   `resources/locators/ios/`, using the same variable names.
2. Add keywords to the page object in `resources/pages/`.
3. Write the test in `tests/mobile/shared/`, tagged `smoke` (critical path) or
   `regression`.
4. `robocop check && pytest tests/unit -q`
5. `./scripts/run_tests.sh -p android -i "" -- --dryrun`, then the same for `ios`.

Rules worth enforcing in review:

- No locator in a `.robot` test file.
- No `Sleep`. Use `resources/common/waits.resource`.
- Prefer `accessibility_id`; XPath is a last resort and must never use
  positional indices.
- A test that only works on one platform belongs in
  `tests/mobile/android/` or `tests/mobile/ios/`, not in `shared/`.

---

## Managing apps

App binaries are **not** committed — they bloat clones and go stale immediately.

```bash
python scripts/upload_app.py build/app-qa.apk --description "QA build 1.4.2"
python scripts/list_sauce_apps.py
```

Then reference the file name from `config/apps.yaml`. Adding a second app under
test is a new key in that file, not a new framework.

---

## Known constraints

**iOS on virtual devices needs a simulator build.** An `.ipa` will not install
on a Sauce simulator — that needs a `.zip` of a `.app` compiled for the
simulator architecture. If you only have an `.ipa`, run iOS against
`-t sauce_rdc`. This is the most common reason an iOS suite fails while the
Android one is green.

**The default locators target the Sauce Labs demo app.** They are a working
reference implementation, not your app. Swapping in a different app means
editing `config/apps.yaml` plus the two locator directories — the rest of the
framework does not change.

**One session per test** is the default. It is slower than sharing a session
across a suite, and it is the right trade: clean state, safe parallelism, and
failures that mean what they say. `Setup Mobile Suite With Shared Session`
exists for read-only journeys where the cost is genuinely justified.

**One automatic rerun of failures.** Mobile cloud runs have real infrastructure
flake. One rerun keeps the signal honest; more than one hides genuinely unstable
tests. Disable with `-r 0`.

---

## Troubleshooting

| Symptom | Cause |
|---------|-------|
| `Unauthorized` from Sauce | `SAUCE_USERNAME` is your email instead of your Sauce username |
| `App not found in storage` | `config/apps.yaml` names a file that is not uploaded — run `scripts/list_sauce_apps.py` |
| iOS session never starts on `sauce_vdc` | `.ipa` on a simulator — use `-t sauce_rdc` or a simulator `.zip` build |
| `Variable '${PLATFORM}' not found` | you ran `robot` directly without `--variablefile config/variables.py:...` |
| Everything fails on the first keyword | the app opened on a different screen than expected — check `page_source/` in the results directory |
