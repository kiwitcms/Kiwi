#!/usr/bin/env python

import MySQLdb

config = {
    "user": "kiwi",
    "password": "kiwi",
    "host": "127.0.0.1",
    "ssl": {
        #        'ca': '/home/senko/Kiwi/tests/db-certs/ca.pem',
        #        'cert': '/home/senko/Kiwi/tests/db-certs/client-cert.pem',
        #        'key': '/home/senko/Kiwi/tests/db-certs/client-key.pem',
    },
}

db = MySQLdb.connect(**config)
cur = db.cursor()
cur.execute("SHOW STATUS LIKE 'Ssl_cipher'")
print(cur.fetchone())
cur.close()
db.close()
