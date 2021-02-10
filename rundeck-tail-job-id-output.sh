#!/bin/bash

[[ -z "$RUNDECK_HOST" ]] && echo "ERROR: RUNDECK_HOST not set" && exit 1
[[ -z "$RUNDECK_AUTH_TOKEN" ]] && echo "ERROR: RUNDECK_AUTH_TOKEN not set" && exit 1

[[ -z "$RUNDECK_JOB_ID" ]] && RUNDECK_JOB_ID="$1"
[[ -z "$RUNDECK_JOB_ID" ]] && echo "ERROR: RUNDECK_JOB_ID not set" && exit 1

while : ; do
  job_output=$(curl -s -X GET -H "X-Rundeck-Auth-Token: $RUNDECK_AUTH_TOKEN" \
               -H 'Accept: application/json' \
               "http://$RUNDECK_HOST/api/36/execution/$RUNDECK_JOB_ID/output" | jq  -r '.entries[].log')

  if [[ -n "$MAX_LINES" ]] && [[ $MAX_LINES -gt 0 ]]; then
      echo -e "$job_output" | tail -n $MAX_LINES
  else
      echo -e "$job_output"
  fi
  
  state_output=$(curl -s -X GET -H "X-Rundeck-Auth-Token: $RUNDECK_AUTH_TOKEN" \
                 -H 'Accept: application/json' \
                 "http://$RUNDECK_HOST/api/36/execution/$RUNDECK_JOB_ID/state")
  job_state_updated=$(echo -e "$state_output" | jq -r '.executionState')

  if [[ "$job_state_updated" != "RUNNING" ]]; then
    echo "STATUS: Job completed. Exiting"
    break
  fi

  echo "==============="
  sleep 10
done

