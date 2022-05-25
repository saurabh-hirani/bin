#!/bin/bash

# Assume the role
content=$(cat -)

# Dump creds in output file
echo export AWS_ACCESS_KEY_ID="$(echo -e "$content" | jq -r '.Credentials.AccessKeyId')"
echo export AWS_SECRET_ACCESS_KEY="$(echo -e "$content" | jq -r '.Credentials.SecretAccessKey')"
echo export AWS_SESSION_TOKEN="$(echo -e "$content" | jq -r '.Credentials.SessionToken')"
