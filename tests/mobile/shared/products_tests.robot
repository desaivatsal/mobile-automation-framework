*** Settings ***
Documentation       Product catalogue and product-detail journeys.

Resource            ../../../resources/pages/login_page.resource
Resource            ../../../resources/pages/products_page.resource
Resource            ../../../resources/pages/product_details_page.resource

Suite Setup         Setup Mobile Suite
Suite Teardown      Teardown Mobile Suite
Test Setup          Log In As Standard User
Test Teardown       Teardown Mobile Test

Test Tags           mobile    products
Test Timeout        5 minutes


*** Test Cases ***
Catalogue Loads With Products
    [Documentation]    The catalogue renders at least one product after login.
    [Tags]    smoke    critical
    Products Screen Should Be Displayed
    Product List Should Not Be Empty

Opening A Product Shows Its Details
    [Documentation]    Tapping a product tile opens a detail screen with a price
    ...    and an add-to-cart control.
    [Tags]    smoke
    Open First Product
    Product Details Should Be Displayed
    ${price}=    Get Product Price
    Should Match Regexp    ${price}    ^\\$\\d+\\.\\d{2}$
    ...    msg=Product price '${price}' is not formatted as a dollar amount.

Returning From Details Restores The Catalogue
    [Documentation]    Back navigation from a product returns to the catalogue
    ...    with the list intact.
    [Tags]    regression
    ${before}=    Get Product Count
    Open First Product
    Product Details Should Be Displayed
    Go Back To Products
    Products Screen Should Be Displayed
    ${after}=    Get Product Count
    Should Be Equal As Integers    ${before}    ${after}
    ...    msg=Catalogue showed ${before} products before opening a detail page and ${after} after.

Named Product Can Be Opened
    [Documentation]    A specific, known product can be located and opened.
    [Tags]    regression
    Open Product By Name    ${TEST_DATA}[expected][first_product]
    Product Details Should Be Displayed


*** Keywords ***
Log In As Standard User
    [Documentation]    Test setup: fresh session, logged in, sitting on the catalogue.
    Setup Mobile Test
    Login As    standard
    Products Screen Should Be Displayed
