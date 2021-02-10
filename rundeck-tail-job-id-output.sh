#!/bin/bash

[[ -z "$RUNDECK_HOST" ]] && echo "ERROR: RUNDECK_HOST not set" && exit 1
[[ -z "$RUNDECK_AUTH_TOKEN" ]] && echo "ERROR: RUNDECK_AUTH_TOKEN not set" && exit 1

[[ -z "$RUNDECK_JOB_ID" ]] && RUNDECK_JOB_ID="$1"
[[ -z "$RUNDECK_JOB_ID" ]] && echo "ERROR: RUNDECK_JOB_ID not set" && exit 1

get_job_output() {
  curl -s -X GET -H "X-Rundeck-Auth-Token: $RUNDECK_AUTH_TOKEN" \
  -H 'Accept: application/json' \
  "http://$RUNDECK_HOST/api/36/execution/$RUNDECK_JOB_ID/output"
}

while : ; do
  job_output=$(get_job_output)
  log_entries="$(echo $job_output | jq  -r '.entries[].log')"

  if [[ -n "$MAX_LINES" ]] && [[ $MAX_LINES -gt 0 ]]; then
      echo -e "$log_entries" | tail -n $MAX_LINES
  else
      echo -e "$log_entries"
  fi
  
  state_output=$(curl -s -X GET -H "X-Rundeck-Auth-Token: $RUNDECK_AUTH_TOKEN" \
                 -H 'Accept: application/json' \
                 "http://$RUNDECK_HOST/api/36/execution/$RUNDECK_JOB_ID/state")
  job_state_updated=$(echo -e "$state_output" | jq -r '.executionState')

  if [[ "$job_state_updated" != "RUNNING" ]]; then
    echo "STATUS: Rundeck job completed. Exiting"

    break
  fi

  echo "*************************************************************"
  sleep 10
done

job_output=$(get_job_output)
echo $job_output | jq  -r '.entries[].log'

echo
echo "STATUS: View this job's output at http://$RUNDECK_HOST/project/$RUNDECK_PROJECT_ID/execution/show/$RUNDECK_JOB_ID"
echo
