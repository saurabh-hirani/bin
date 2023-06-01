#!/bin/bash

# Install timer - https://github.com/rlue/timer

set -x
duration_mins="$1"

one_fourth_duration=$(echo "$duration_mins/4" | bc)
two_fourth_duration="$(echo "$duration_mins/3" | bc)"
three_fourth_duration=$(echo "$duration_mins/2" | bc)
status_file="/tmp/timer-status.txt"
success_count="0"

osascript -e 'Tell application "AnyBar" to set title to ""'
osascript -e 'Tell application "AnyBar_copy" to set title to ""'

update_remaining_minutes() {
  local_duration_mins="$1"
  for i in $(seq 0 "$local_duration_mins"); do
    remaining_time=$(echo "$local_duration_mins - $i" | bc)
    osascript -e 'Tell application "AnyBar_copy" to set title to "session_remaining_time='$remaining_time/$local_duration_mins' mins"'
    if [[ $remaining_time -eq 0 ]]; then
      echo "breaking"
      break
    fi
    ((i++))
    sleep 60
  done
}
update_remaining_minutes "$one_fourth_duration" &

osascript -e 'Tell application "System Events" to display dialog "Starting timer - do what needs to be done - you have '$duration_mins' minutes" with title "Starting"'
osascript -e 'Tell application "AnyBar" to set image name to "cyan"'

osascript -e 'Tell application "AnyBar" to set title to "timer_status=0/4 score='$success_count/4'"'
# osascript -e 'Tell application "AnyBar_copy" to set title to "remaining_time='$remaining_time' mins"'

timer "$one_fourth_duration" && osascript -e 'Tell application "System Events" to display dialog "'"$one_fourth_duration/$duration_mins mins completed"'" with title "1/4 time over"' > $status_file

if grep -q OK < $status_file; then
  success_count="1"
fi
osascript -e 'Tell application "AnyBar" to set title to "timer_status=1/4 score='$success_count/4'"'
osascript -e 'Tell application "AnyBar" to set image name to "yellow"'
update_remaining_minutes "$one_fourth_duration" &

timer "$one_fourth_duration" && osascript -e 'Tell application "System Events" to display dialog "'"$two_fourth_duration/$duration_mins mins completed. score=$success_count/4"'" with title "2/4 time over"' > $status_file
if grep -q OK < $status_file; then
  success_count=$((success_count+1))
fi
osascript -e 'Tell application "AnyBar" to set title to "timer_status=2/4 score='$success_count/4'"'
osascript -e 'Tell application "AnyBar" to set image name to "yellow"'
update_remaining_minutes "$one_fourth_duration" &


if [[ $success_count -gt 1 ]]; then
  osascript -e 'Tell application "AnyBar" to set image name to "green"'
fi

timer "$one_fourth_duration" && osascript -e 'Tell application "System Events" to display dialog "'"$three_fourth_duration/$duration_mins mins completed. score=$success_count/4"'" with title "3/4 time over"' > $status_file
if grep -q OK < $status_file; then
  success_count=$((success_count+1))
fi
osascript -e 'Tell application "AnyBar" to set title to "timer_status=3/4 score='$success_count/4'"'
update_remaining_minutes "$one_fourth_duration" &

timer "$one_fourth_duration" && osascript -e 'Tell application "System Events" to display dialog "'"$duration_mins/$duration_mins mins completed - were you focused?"'" with title "Timer completed"' > $status_file

if grep -q OK < $status_file; then
  success_count=$((success_count+1))
fi

if [[ $success_count -gt 2 ]]; then
  osascript -e 'Tell application "AnyBar" to set image name to "green"'
else
  osascript -e 'Tell application "AnyBar" to set image name to "yellow"'
fi

osascript -e 'Tell application "AnyBar" to set title to "timer_status=4/4 score='$success_count/4'"'
update_remaining_minutes "$one_fourth_duration" &

if [[ $success_count -lt 2 ]]; then
  osascript -e 'Tell application "AnyBar" to set image name to "red"'
fi

osascript -e 'Tell application "System Events" to display dialog "'"Total score = $success_count/4"'" with title "Timer completed"'

wait
