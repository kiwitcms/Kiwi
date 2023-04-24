# checkov:skip=CKV_DOCKER_2:Ensure that HEALTHCHECK instructions have been added to container images
FROM redmine:5

# enable the rest API
RUN sed -i "/rest_api_enabled:/{n;s/^  default: 0/  default: 1/;}" /usr/src/redmine/config/settings.yml

# this is redmine
USER 999
