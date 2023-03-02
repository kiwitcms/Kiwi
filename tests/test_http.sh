#!/bin/bash

. /usr/share/beakerlib/beakerlib.sh

assert_up_and_running() {
    sleep 10
    # HTTP redirects; HTTPS display the login page
    rlRun -t -c "curl       -o- http://localhost/  | grep '301 Moved Permanently'"
    rlRun -t -c "curl -k -L -o- https://localhost/ | grep 'Welcome to Kiwi TCMS'"
}

get_dashboard() {
    rlRun -t -c "curl -k -L -o- -c /tmp/testcookies.txt $1/"
    CSRF_TOKEN=$(grep csrftoken /tmp/testcookies.txt | cut -f 7)
    rlRun -t -c "curl -e $1/accounts/login/ -d username=testadmin -d password=password \
        -d csrfmiddlewaretoken=$CSRF_TOKEN -k -L -i -o /tmp/testdata.txt \
        -b /tmp/testcookies.txt -c /tmp/login-cookies.txt $1/accounts/login/"
    rlAssertGrep "<title>Kiwi TCMS - Dashboard</title>" /tmp/testdata.txt
}

exec_wrk() {
    URL=$1
    LOGS_DIR=$2
    LOG_BASENAME=$3
    EXTRA_HEADERS=${4:-"X-Dummy-Header: 1"}

    WRK_FILE="$LOGS_DIR/$LOG_BASENAME.log"

    wrk -d10s -t4 -c4 -H "$EXTRA_HEADERS" "$URL" > "$WRK_FILE"

    TOTAL_REQUESTS=$(grep 'requests in ' "$WRK_FILE" | tr -s ' ' | cut -f2 -d' ')
    FAILED_REQUESTS=$(grep 'Non-2xx or 3xx responses:' "$WRK_FILE" | tr -d ' ' | cut -f2 -d:)
    test -z "$FAILED_REQUESTS" && FAILED_REQUESTS="0"
    COMPLETED_REQUESTS=$((TOTAL_REQUESTS - FAILED_REQUESTS))

    return "$COMPLETED_REQUESTS"
}

rlJournalStart
    rlPhaseStartSetup
        # wait for tear-down from previous script b/c
        # in CI subsequent tests can't find the db host
        sleep 5

        WRK_DIR=$(mktemp -d ./wrk-logs-XXXX)
        chmod go+rwx "$WRK_DIR"

        rlRun -t -c "docker-compose up -d"
        sleep 10
        rlRun -t -c "docker exec -i kiwi_web /Kiwi/manage.py migrate"
        assert_up_and_running
    rlPhaseEnd

    rlPhaseStartTest "Should not display SSL warning for HTTPS connection"
        rlRun -t -c "docker exec -i kiwi_web /Kiwi/manage.py createsuperuser \
            --username testadmin --email testadmin@domain.com --noinput"
        rlRun -t -c "cat tests/set_testadmin_pass.py | docker exec -i kiwi_web /Kiwi/manage.py shell"

        get_dashboard "https://localhost"
        rlAssertNotGrep "You are not using a secure connection." /tmp/testdata.txt
    rlPhaseEnd

    rlPhaseStartTest "Should allow file upload with UTF-8 filenames"
        cat > ~/.tcms.conf << _EOF_
[tcms]
url = https://localhost/xml-rpc/
username = testadmin
password = password
_EOF_

        rlRun -t -c "./tests/test_utf8_uploads.py -v"
    rlPhaseEnd

    rlPhaseStartTest "Should send ETag header"
        rlRun -t -c "curl -k -D- https://localhost/static/images/kiwi_h20.png 2>/dev/null | grep 'ETag'"
    rlPhaseEnd

    rlPhaseStartTest "Should NOT send Cache-Control header"
        rlRun -t -c "curl -k -D- https://localhost/static/images/kiwi_h20.png 2>/dev/null | grep 'Cache-Control'" 1
    rlPhaseEnd

    rlPhaseStartTest "Should send X-Frame-Options header"
        rlRun -t -c "curl -k -D- https://localhost 2>/dev/null | grep 'X-Frame-Options: DENY'"
    rlPhaseEnd

    rlPhaseStartTest "Should send X-Content-Type-Options header"
        rlRun -t -c "curl -k -D- https://localhost 2>/dev/null | grep 'X-Content-Type-Options: nosniff'"
    rlPhaseEnd

    rlPhaseStartTest "Performance baseline for /accounts/register/"
        exec_wrk "https://localhost/accounts/login/" "$WRK_DIR" "register-account-page"
    rlPhaseEnd

    rlPhaseStartTest "Performance baseline for /accounts/login/"
        exec_wrk "https://localhost/accounts/login/" "$WRK_DIR" "login-page"
    rlPhaseEnd

    rlPhaseStartTest "Performance baseline for /accounts/passwordreset/"
        exec_wrk "https://localhost/accounts/login/" "$WRK_DIR" "password-reset-page"
    rlPhaseEnd

    rlPhaseStartTest "Performance baseline for static file"
        exec_wrk "https://localhost/static/images/kiwi_h20.png" "$WRK_DIR" "static-image"
    rlPhaseEnd

    rlPhaseStartTest "Performance baseline for / aka dashboard"
        # Note: the cookies file is created in get_dashboard() above
        SESSION_ID=$(grep sessionid /tmp/login-cookies.txt | cut -f 7)
        exec_wrk "https://localhost/" "$WRK_DIR" "dashboard" "Cookie: sessionid=$SESSION_ID"
    rlPhaseEnd

    rlPhaseStartCleanup
        rlRun -t -c "docker-compose down"
        rm -f /tmp/testcookies.txt
        rm -f /tmp/testdata.txt
        if [ -n "$ImageOS" ]; then
            rlRun -t -c "docker volume rm kiwi_db_data"
        fi
    rlPhaseEnd
rlJournalEnd

rlJournalPrintText
