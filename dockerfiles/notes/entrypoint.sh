#!/bin/bash

# -i exists but for some reason it doesn't work. = /
sed  '1 i\nameserver 127.0.0.1' /etc/resolv.conf > /etc/resolv.conf

export EDXNOTES_CONFIG_ROOT=/edx/etc/
SSM_CONFIG=/mitxonline-qa/notes/notes_cfg
aws ssm get-parameter --name "${SSM_CONFIG}" --with-decryption | jq -r '.Parameter.Value' > "${EDXNOTES_CONFIG_ROOT}/edx_notes_api.yml"

gunicorn --workers=2 --name notes -c /edx/app/notes/notesserver/docker_gunicorn_configuration.py --log-file - --max-requests=1000 notesserver.wsgi:application
