*** Settings ***
Documentation    Aggregate import surface.
...
...              Page objects import this one file and get libraries, waits,
...              gestures, assertions and session management. Tests import page
...              objects, never this file directly - that boundary is what keeps
...              raw Appium keywords out of test cases.

Resource        libraries.resource
Resource        waits.resource
Resource        gestures.resource
Resource        assertions.resource
Resource        locator_utils.resource
Resource        session.resource
