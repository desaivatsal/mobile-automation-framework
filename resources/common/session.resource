*** Settings ***
Documentation    Suite and test setup/teardown for mobile suites.
...
...              Default model: one Appium session per test. It is slower than a
...              session per suite, but it is the only model that gives clean
...              state, safe parallelisation via pabot, and failures that mean
...              what they say. Use the ``Suite`` variants only for read-only
...              journeys where the cost is genuinely justified.

Resource        libraries.resource
Resource        waits.resource
Resource        gestures.resource
Resource        assertions.resource


*** Keywords ***
Setup Mobile Suite
    [Documentation]    Logs the resolved execution context once per suite.
    Log    Environment=${ENV} | Platform=${PLATFORM} | Target=${TARGET} | App=${APP_KEY}    console=${TRUE}
    Set Suite Metadata    Environment    ${ENV}
    Set Suite Metadata    Platform    ${PLATFORM}
    Set Suite Metadata    Target    ${TARGET}
    Set Suite Metadata    App    ${APP_KEY}
    Set Suite Metadata    Build    ${BUILD_NAME}

Teardown Mobile Suite
    [Documentation]    Belt and braces - closes anything a failing teardown left open.
    Run Keyword And Ignore Error    Close All Applications

Setup Mobile Test
    [Documentation]    Opens a fresh Appium session for the test.
    Open Test Application

Teardown Mobile Test
    [Documentation]    Reports the result to Sauce, then closes the session.
    ...    Evidence capture already happened in EvidenceListener, while the
    ...    driver was still healthy.
    Run Keyword And Ignore Error    Report Sauce Status
    Close Test Application

Setup Mobile Suite With Shared Session
    [Documentation]    Opens one session for the whole suite. Only for read-only flows.
    Setup Mobile Suite
    Open Test Application

Teardown Mobile Suite With Shared Session
    [Documentation]    Counterpart to `Setup Mobile Suite With Shared Session`.
    Run Keyword And Ignore Error    Report Sauce Status
    Run Keyword And Ignore Error    Close Test Application
    Teardown Mobile Suite
