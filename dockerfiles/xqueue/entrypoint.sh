#!/bin/sh

set -eux


sed -i '1 i\nameserver 127.0.0.1' /etc/resolv.conf

# cat for testing only
cat /etc/resolv.conf


export XQUEUE_CFG=/edx/app/xqueue/xqueue_cfg.yml
export DJANGO_SETTINGS_MODULE=xqueue.production
SSM_CONFIG=/mitxonline-qa/xqueue/xqueue_cfg

# Now that have multiple containers on this NIC, it can take a second for networking to come up. 
sleep 30

aws ssm get-parameter --name "${SSM_CONFIG}" --with-decryption | jq -r '.Parameter.Value' > "${XQUEUE_CFG}"

./manage.py migrate
./manage.py update_users
gunicorn -c /edx/app/xqueue/xqueue/docker_gunicorn_configuration.py --bind=0.0.0.0:8040 --workers 2 --max-requests=1000 xqueue.wsgi:application
