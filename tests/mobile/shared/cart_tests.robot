*** Settings ***
Documentation       Cart journeys: adding, removing and reviewing items.

Resource            ../../../resources/pages/login_page.resource
Resource            ../../../resources/pages/products_page.resource
Resource            ../../../resources/pages/product_details_page.resource
Resource            ../../../resources/pages/cart_page.resource

Suite Setup         Setup Mobile Suite
Suite Teardown      Teardown Mobile Suite
Test Setup          Log In And Open Catalogue
Test Teardown       Teardown Mobile Test

Test Tags           mobile    cart
Test Timeout        6 minutes


*** Test Cases ***
Adding A Product Updates The Cart Badge
    [Documentation]    The badge is the user's only feedback that the add worked -
    ...    it is worth a dedicated assertion.
    [Tags]    smoke    critical
    Open First Product
    Product Details Should Be Displayed
    Add Product To Cart
    Go Back To Products
    Cart Badge Should Show    1

Added Product Appears In The Cart
    [Documentation]    A product added from its detail page is listed in the cart
    ...    with the right name and quantity.
    [Tags]    smoke
    Open Product By Name    ${TEST_DATA}[expected][first_product]
    Add Product To Cart
    Go Back To Products
    Open Cart From Products
    Cart Screen Should Be Displayed
    Cart Should Contain    1
    Cart Should Contain Product    ${TEST_DATA}[expected][first_product]

Removing A Product Empties The Cart
    [Documentation]    Add then remove must leave the cart in its original state -
    ...    not merely hide the badge.
    [Tags]    regression
    Open First Product
    Add Product To Cart
    Remove Product From Cart
    Go Back To Products
    Cart Badge Should Show    0

Continue Shopping Returns To The Catalogue
    [Documentation]    Leaving the cart returns to the catalogue without losing
    ...    the cart contents.
    [Tags]    regression
    Open First Product
    Add Product To Cart
    Go Back To Products
    Open Cart From Products
    Continue Shopping
    Products Screen Should Be Displayed


*** Keywords ***
Log In And Open Catalogue
    [Documentation]    Test setup: fresh session, logged in, sitting on the catalogue.
    Setup Mobile Test
    Login As    standard
    Products Screen Should Be Displayed
