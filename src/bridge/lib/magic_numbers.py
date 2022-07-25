"""
Module of meaningful integer values.

This module consists of constants that are used to provide meaningful representations of
integer values used in infrastructure management.
"""

AWS_LOAD_BALANCER_NAME_MAX_LENGTH = 32
AWS_TARGET_GROUP_NAME_MAX_LENGTH = 32
AWS_RDS_DEFAULT_DATABASE_CAPACITY = 334  # For optimal performance on gp2 storage
CONCOURSE_PROMETHEUS_EXPORTER_DEFAULT_PORT = 9391
CONCOURSE_WEB_HOST_COMMUNICATION_PORT = 2222
CONCOURSE_WORKER_HEALTHCHECK_PORT = 8888
CONSUL_DNS_PORT = 8600
CONSUL_HTTP_PORT = 8500
CONSUL_LAN_SERF_PORT = 8301
CONSUL_RPC_PORT = 8300
CONSUL_WAN_SERF_PORT = 8302
DAYS_IN_MONTH = 30
DEFAULT_DNS_PORT = 53
DEFAULT_ELASTICSEARCH_PORT = 9200
DEFAULT_FASTLY_BACKEND_TTL = 86400
DEFAULT_HTTPS_PORT = 443
DEFAULT_HTTP_PORT = 80
DEFAULT_MEMCACHED_PORT = 11211
DEFAULT_MONGODB_PORT = 27017
DEFAULT_MYSQL_PORT = 3306
DEFAULT_POSTGRES_PORT = 5432
DEFAULT_REDIS_PORT = 6379
DEFAULT_RSA_KEY_SIZE = 2048
FIVE_MINUTES = 60 * 5
HALF_GIGABYTE_MB = 512
HOURS_IN_DAY = 24
HOURS_IN_MONTH = HOURS_IN_DAY * DAYS_IN_MONTH
HTTP_STATUS_NOT_FOUND = 404
HTTP_STATUS_OK = 200
HTTP_STATUS_SERVICE_UNAVAILABLE = 503
IAM_ROLE_NAME_PREFIX_MAX_LENGTH = 32
MAXIMUM_PORT_NUMBER = 65535
MAXIMUM_RSA_KEY_SIZE = 4096
ONE_GIGABYTE_MB = 1024
ONE_GIGAHERTZ = 1024
SECONDS_IN_ONE_DAY = 86400
VAULT_CLUSTER_PORT = 8201
VAULT_HTTP_PORT = 8200
FORUM_SERVICE_PORT = 4567
XQUEUE_SERVICE_PORT = 8040
