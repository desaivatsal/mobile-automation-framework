*** Settings ***
Documentation       Single place where external libraries are imported.
...
...                 Every other resource imports this file rather than importing
...                 libraries itself, so swapping a library (or adding one for the
...                 future web/API layers) is a one-file change.
...
...                 ``libs.MobileSession`` is imported by module path, which requires
...                 the project root on ``PYTHONPATH``. ``scripts/run_tests.sh`` and
...                 the CI workflows pass ``--pythonpath .``; the library also
...                 bootstraps its own path as a fallback.
...
...                 ``run_on_failure`` is disabled because ``EvidenceListener``
...                 captures the screenshot, page source and Sauce link in one
...                 place - otherwise AppiumLibrary fires a bare screenshot on
...                 every nested keyword failure.

Library             Collections
Library             DateTime
Library             OperatingSystem
Library             String
Library             AppiumLibrary    timeout=20    run_on_failure=No Operation
Library             libs.MobileSession
