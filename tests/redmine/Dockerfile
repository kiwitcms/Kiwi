FROM redmine

# enable the rest API
RUN sed -i "/rest_api_enabled:/{n;s/^  default: 0/  default: 1/;}" /usr/src/redmine/config/settings.yml
