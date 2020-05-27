#!/bin/bash

. /usr/share/beakerlib/beakerlib.sh

assert_up_and_running() {
    sleep 10
    IP_ADDRESS=`docker inspect -f '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' kiwi_web`
    # both HTTP and HTTPS display the login page
    rlRun -t -c "curl    -L -o- http://$IP_ADDRESS:8080/  | grep 'Welcome to Kiwi TCMS'"
    rlRun -t -c "curl -k -L -o- https://$IP_ADDRESS:8443/ | grep 'Welcome to Kiwi TCMS'"
}

rlJournalStart
    rlPhaseStartSetup
        # wait for tear-down from previous script b/c
        # in Travis CI subsequent tests can't find the db host
        sleep 5
    rlPhaseEnd

    rlPhaseStartTest "Plain HTTP works"
        rlRun -t -c "docker-compose run -d -e KIWI_DONT_ENFORCE_HTTPS=true --name kiwi_web web /httpd-foreground"
        sleep 10
        rlRun -t -c "docker exec -i kiwi_web /Kiwi/manage.py migrate"
        assert_up_and_running
    rlPhaseEnd

    rlPhaseStartCleanup
        rlRun -t -c "docker-compose down"
    rlPhaseEnd
rlJournalEnd

rlJournalPrintText
