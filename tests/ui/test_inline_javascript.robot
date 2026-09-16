*** Settings ***
Library           SeleniumLibrary

*** Variables ***
${SERVER}               https://localhost
${BROWSER}              Headless Firefox
${DELAY}                0
${DASHBOARD_URL}        ${SERVER}/
${LOGIN_URL}            ${SERVER}/accounts/login/
${SVG_URL}              ${SERVER}/uploads/attachments/auth_user/2/inline_javascript.svg
${HTML_URL}             ${SERVER}/uploads/attachments/auth_user/2/html_with_external_script.html


*** Test Cases ***
Accessing an SVG image should not execute inline JavaScript
    Open Browser    ${LOGIN_URL}    ${BROWSER}
    Set Window Size     3024    1890
    Set Selenium Speed    ${DELAY}
    Title Should Be    Kiwi TCMS - Login

    Input Text    inputUsername    testadmin
    Input Text    inputPassword    password
    Click Button  Log in

    Location Should Be    ${DASHBOARD_URL}
    Title Should Be       Kiwi TCMS - Dashboard

    Go To                 ${SVG_URL}
    Location Should Be    ${SVG_URL}

    [Teardown]    Close Browser


Accessing an HTML file should not execute JavaScript
    Open Browser    ${LOGIN_URL}    ${BROWSER}
    Set Window Size     3024    1890
    Set Selenium Speed    ${DELAY}
    Title Should Be    Kiwi TCMS - Login

    Input Text    inputUsername    testadmin
    Input Text    inputPassword    password
    Click Button  Log in

    Location Should Be    ${DASHBOARD_URL}
    Title Should Be       Kiwi TCMS - Dashboard

    Go To                 ${HTML_URL}
    Location Should Be    ${HTML_URL}

    [Teardown]    Close Browser


Accessing an SVG image without permissions should 403
    Open Browser    ${LOGIN_URL}    ${BROWSER}
    Set Window Size     3024    1890
    Set Selenium Speed    ${DELAY}
    Title Should Be    Kiwi TCMS - Login

    Input Text    inputUsername    regular
    Input Text    inputPassword    password
    Click Button  Log in

    Location Should Be    ${DASHBOARD_URL}
    Title Should Be       Kiwi TCMS - Dashboard

    Go To                 ${SVG_URL}
    Location Should Be    ${SVG_URL}
    Page Should Contain   403 Forbidden

    [Teardown]    Close Browser


Directly accessing an SVG image should 403
    Open Browser    ${SVG_URL}    ${BROWSER}
    Maximize Browser Window
    Set Selenium Speed    ${DELAY}

    Location Should Be    ${SVG_URL}
    Page Should Contain   403 Forbidden

    [Teardown]    Close Browser


Directly accessing an HTML file should 403
    Open Browser    ${HTML_URL}    ${BROWSER}
    Maximize Browser Window
    Set Selenium Speed    ${DELAY}

    Location Should Be    ${HTML_URL}
    Page Should Contain   403 Forbidden

    [Teardown]    Close Browser
