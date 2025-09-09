*** Settings ***
Library           OperatingSystem
Library           SeleniumLibrary

*** Variables ***
${SERVER}               https://localhost
${BROWSER}              Headless Firefox
${DELAY}                0
${DASHBOARD_URL}        ${SERVER}/
${LOGIN_URL}            ${SERVER}/accounts/login/
${ADMIN_URL}            ${SERVER}/admin/auth/user/


*** Test Cases ***
Logout from Dashboard page works
    Open Browser    ${LOGIN_URL}    ${BROWSER}
    Set Window Size     3024    1890
    Set Selenium Speed    ${DELAY}
    Title Should Be    Kiwi TCMS - Login

    Input Text    inputUsername    testadmin
    Input Text    inputPassword    password
    Click Button  Log in

    Location Should Be    ${DASHBOARD_URL}
    Title Should Be       Kiwi TCMS - Dashboard

    Click Link  id=user-menu
    Click Link  id=logout_link
    Title Should Be       Kiwi TCMS - Login

    [Teardown]    Close Browser

Logout from Admin page works
    Open Browser    ${LOGIN_URL}    ${BROWSER}
    Set Window Size     3024    1890
    Set Selenium Speed    ${DELAY}
    Title Should Be    Kiwi TCMS - Login

    Input Text    inputUsername    testadmin
    Input Text    inputPassword    password
    Click Button  Log in

    Location Should Be    ${DASHBOARD_URL}
    Title Should Be       Kiwi TCMS - Dashboard

    Go To                 ${ADMIN_URL}
    Title Should Be       Select user to change | Grappelli
    Page Should Contain   Users

    Click Link  id=user-menu
    Click Link  id=logout_link
    Title Should Be       Kiwi TCMS - Login

    [Teardown]    Close Browser
