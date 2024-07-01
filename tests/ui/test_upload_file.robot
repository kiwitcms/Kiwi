*** Settings ***
Library           OperatingSystem
Library           SeleniumLibrary

*** Variables ***
${SERVER}               https://localhost
${BROWSER}              Headless Firefox
${DELAY}                0
${LOGIN_URL}            ${SERVER}/accounts/login/
${DASHBOARD_URL}        ${SERVER}/
${TEST_PLAN_URL}        ${SERVER}/plan/1/


*** Test Cases ***
Uploading file works via file upload
    Open Browser    ${LOGIN_URL}    ${BROWSER}
    Set Window Size     3024    1890
    Set Selenium Speed    ${DELAY}
    Title Should Be    Kiwi TCMS - Login

    Input Text    inputUsername    testadmin
    Input Text    inputPassword    password
    Click Button  Log in

    Location Should Be    ${DASHBOARD_URL}
    Title Should Be       Kiwi TCMS - Dashboard

    Go To                 ${TEST_PLAN_URL}
    Create File   ${TEMPDIR}${/}hello-robots.txt   Hello Robots
    Choose File   id:id_attachment_file    ${TEMPDIR}${/}hello-robots.txt
    Click Button  Add attachment
    Page Should Contain   Your attachment was uploaded

    [Teardown]    Close Browser
