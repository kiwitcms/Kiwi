#!/bin/bash

OPENSSL_SUBJ="/C=BG/ST=Sofia/L=Sofia"
OPENSSL_CA="${OPENSSL_SUBJ}/CN=fake-CA"
OPENSSL_SERVER="${OPENSSL_SUBJ}/CN=fake-server"
OPENSSL_CLIENT="${OPENSSL_SUBJ}/CN=fake-client"

mkdir -p db-certs/
pushd db-certs/

# Generate new CA certificate ca.pem file.
openssl genrsa 2048 > ca-key.pem

# TODO This has interaction that must be automated
openssl req -new -x509 -nodes -days 3600 \
    -subj "${OPENSSL_CA}" \
    -key ca-key.pem -out ca.pem


# Create the server-side certificates
# This has more interaction that must be automated

openssl req -newkey rsa:2048 -days 3600 -nodes \
    -subj "${OPENSSL_SERVER}" \
    -keyout server-key.pem -out server-req.pem
openssl rsa -in server-key.pem -out server-key.pem
openssl x509 -req -in server-req.pem -days 3600 \
    -CA ca.pem -CAkey ca-key.pem -set_serial 01 -out server-cert.pem

# Create the client-side certificates
openssl req -newkey rsa:2048 -days 3600 -nodes \
    -subj "${OPENSSL_CLIENT}" \
    -keyout client-key.pem -out client-req.pem
openssl rsa -in client-key.pem -out client-key.pem
openssl x509 -req -in client-req.pem -days 3600 \
    -CA ca.pem -CAkey ca-key.pem -set_serial 01 -out client-cert.pem

# Verify the certificates are correct
openssl verify -CAfile ca.pem server-cert.pem client-cert.pem

# make the keys readable b/c we're having issues with uid/gid inside the containers
chmod 644 client-key.pem server-key.pem ca-key.pem
popd
