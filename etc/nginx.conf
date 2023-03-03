# For more information on configuration, see:
#   * Official English Documentation: http://nginx.org/en/docs/

daemon on;
worker_processes auto;
error_log /dev/stderr;
pid /tmp/nginx.pid;

# Load dynamic modules. See /usr/share/doc/nginx/README.dynamic.
include /usr/share/nginx/modules/*.conf;

events {
    worker_connections 1024;
}

http {
    log_format  main  '$remote_addr - $remote_user [$time_local] "$request" '
                      '$status $body_bytes_sent "$http_referer" '
                      '"$http_user_agent" "$http_x_forwarded_for"';

    access_log  /dev/stdout  main;

    sendfile            on;
    tcp_nopush          on;
    tcp_nodelay         on;
    keepalive_timeout   65;
    types_hash_max_size 4096;

    include             /etc/nginx/mime.types;
    default_type        application/octet-stream;

    gzip on;
    gzip_disable "msie6";

    # note: this should be bigger than
    # FILE_UPLOAD_MAX_SIZE from Kiwi TCMS which defaults to 5M.
    client_max_body_size 10m;

    # limit URI size, see
    # https://github.com/kiwitcms/Kiwi/issues/1054
    large_client_header_buffers 4 10k;

    ssl_certificate     /Kiwi/ssl/localhost.crt;
    ssl_certificate_key /Kiwi/ssl/localhost.key;

    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers off;

    # default proxy settings
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;

    map $request_uri $limit_key {
        default "";
        ~^/accounts/ $binary_remote_addr;
    }
    limit_req_zone $limit_key zone=ten-per-sec:10m rate=10r/s;
    limit_req_status 429;

    upstream kiwitcms {
        server unix:///tmp/kiwitcms.sock;
    }

    # WARNING: make sure these match tcms.core.middleware.ExtraHeadersMiddleware
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;
    add_header Content-Security-Policy "script-src 'self' cdn.crowdin.com;";

    server {
        listen       8080;
        listen       [::]:8080;
        server_name  _;

        location / {
                return 301 https://$host$request_uri;
        }
    }

    server {
        listen       8443 ssl;
        listen       [::]:8443 ssl;
        server_name  _;

        location /uploads/  {
            alias /Kiwi/uploads/;
        }

        location /static/ {
            alias /Kiwi/static/;
        }

        location / {
            include     /etc/nginx/uwsgi_params;
            uwsgi_pass  kiwitcms;

            limit_req zone=ten-per-sec burst=20 nodelay;
        }
    }
}
