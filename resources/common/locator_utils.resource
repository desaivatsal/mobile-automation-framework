*** Settings ***
Documentation    Helpers for parameterised locators.
...
...              A parameterised locator is stored in a locator file with
...              ``{placeholder}`` tokens, e.g.
...              ``${PRODUCT_BY_NAME}    xpath=//*[@text="{name}"]``
...              and resolved with `Build Locator` at call time. This keeps
...              dynamic XPath construction out of page keywords and out of tests.

Resource        libraries.resource


*** Keywords ***
Build Locator
    [Documentation]    Substitutes ``{placeholder}`` tokens in a locator template.
    ...
    ...    Example:
    ...    | ${loc}= | Build Locator | ${PRODUCT_BY_NAME} | name=Sauce Labs Backpack |
    [Arguments]    ${template}    &{values}
    ${resolved}=    Evaluate    $template.format(**$values)
    RETURN    ${resolved}
