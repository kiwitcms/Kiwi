image:
  repository: kiwitcms/kiwi
  pullPolicy: IfNotPresent
  # Full list of available tags can be found here:
  #   https://hub.docker.com/r/kiwitcms/kiwi/tags
  tag: latest

service:
  type: ClusterIP
  port:
    http: 8080
    https: 8443

ingress:
  enabled: false
  className: nginx
  annotations:
    acme.cert-manager.io/http01-edit-in-place: "true"
    cert-manager.io/cluster-issuer: letsencrypt-prod
    ingress.kubernetes.io/ssl-redirect: "true"
    kubernetes.io/ingress.allow-http: "false"
    kubernetes.io/tls-acme: "true"
    nginx.ingress.kubernetes.io/backend-protocol: "HTTPS"

  host: kiwi.example.org
  tls:
    enabled: true
    port: 443

resources:
  limits:
    cpu: 300m
    memory: 512Mi
  requests:
    cpu: 200m
    memory: 256Mi

storage:
  # If persistent storage is not enabled, chart will create in-memory directory
  # that will be destroyed upon pod restart
  persistent: true

  # Available class can be listed by "kubectl get storageclasses" command
  class: standard

  # The size of the storgae where uploaded files will be kept
  size: 32Gi

media:
  root: "/Kiwi/uploads"
  url: "/uploads/"

email:
  from: "kiwi@example.com"
  subject: "[Kiwi-TCMS] "

database:
  type: mariadb

  host: kiwi-mariadb
  port: 3306

  # Database can be either external, like managed AWS RDS service, or internal - part of this chart.
  # If it is internal, the dependency mentioned in Chart.yaml will be deployed
  internal: true

  # If external
  db_name: kiwi
  username: kiwi
  # Set a password value via the command line argument:
  # >>> helm upgrade --install --namespace <my_namespace> <helm_repo>/kiwi --set database.password=<my_password>
  # password:

mariadb:
  image:
    debug: true
  # If database is internal, the following config will be used
  auth:
    database: kiwi
    # checkov:skip=CKV_SECRET_6:Base64 High Entropy String
    username: kiwi
    # checkov:skip=CKV_SECRET_6:Base64 High Entropy String
    existingSecret: kiwi-credentials

  primary:
    persistence:
      size: 32Gi

    # Parameters can be taken from here: https://hub.docker.com/r/bitnami/mariadb
    extraEnvVars:
      - name: MARIADB_EXTRA_FLAGS
        value: --bind-address=0.0.0.0 --character-set-server=utf8mb4 --collation-server=utf8mb4_unicode_ci
      - name: MARIADB_SKIP_TEST_DB
        value: "yes"

    configuration: |
      [mysqld]
      max-connections=10
      character-set-server=UTF8
      collation-server=utf8mb4_general_ci

  initdbScripts:
    prepare.sh: |
      #!/bin/sh
      mysql -uroot -e "CREATE USER '${MARIADB_USER}'@'%';"
      mysql -uroot -e "SET PASSWORD FOR '${MARIADB_USER}'@'%' = PASSWORD('${MARIADB_PASSWORD}');"

      mysql -uroot -e "CREATE DATABASE IF NOT EXISTS ${MARIADB_DATABASE};"
      mysql -uroot -e "GRANT ALL PRIVILEGES ON ${MARIADB_DATABASE}.* TO '${MARIADB_USER}'@'%' IDENTIFIED BY '${MARIADB_PASSWORD}'; FLUSH PRIVILEGES;"

      mysql -uroot -e "SET PASSWORD FOR 'root'@'localhost' = PASSWORD('${MARIADB_ROOT_PASSWORD}');"
