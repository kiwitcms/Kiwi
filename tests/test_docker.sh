#!/bin/bash

. /usr/share/beakerlib/beakerlib.sh

assert_up_and_running() {
    sleep 10
    IP_ADDRESS=`docker inspect -f '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' kiwi_web`
    rlRun -t -c "curl -k -L -o- https://$IP_ADDRESS:8443/ | grep 'Welcome to Kiwi TCMS'"
}

rlJournalStart
    rlPhaseStartTest "Container up"
        rlRun -t -c "docker-compose up -d"
        sleep 10
        rlRun -t -c "docker exec -it kiwi_web /Kiwi/manage.py migrate"
        assert_up_and_running
    rlPhaseEnd

    rlPhaseStartTest "Container restart"
        rlRun -t -c "docker-compose restart"
        assert_up_and_running
    rlPhaseEnd

    rlPhaseStartTest "Container stop & start"
        rlRun -t -c "docker-compose stop"
        sleep 5
        rlRun -t -c "docker-compose start"
        assert_up_and_running
    rlPhaseEnd

    rlPhaseStartTest "Container kill & start"
        rlRun -t -c "docker-compose kill"
        sleep 5
        rlRun -t -c "docker-compose start"
        assert_up_and_running
    rlPhaseEnd

    rlPhaseStartCleanup
        rlRun -t -c "docker-compose down"
    rlPhaseEnd
rlJournalEnd

rlJournalPrintText
