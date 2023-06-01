#!/bin/bash

# Install timer - https://github.com/rlue/timer

duration_mins="$1"

set -x
one_fourth_duration=$(echo "scale=2;$duration_mins/4" | bc)
two_fourth_duration="$(echo "scale=2;$duration_mins/3" | bc)"
three_fourth_duration=$(echo "scale=2;$duration_mins/2" | bc)
remaining_time=$duration_mins
status_file="/tmp/timer-status.txt"
success_count="0"

osascript -e 'Tell application "AnyBar" to set title to ""'
osascript -e 'Tell application "System Events" to display dialog "Starting timer - do what needs to be done - you have '$duration_mins' minutes" with title "Starting"'
osascript -e 'Tell application "AnyBar" to set image name to "cyan"'
osascript -e 'Tell application "AnyBar" to set title to "timer_status=0/4 score='$success_count/4' remaining_time='$remaining_time' mins"'

timer "$one_fourth_duration" && osascript -e 'Tell application "System Events" to display dialog "'"$one_fourth_duration/$full_duration mins completed"'" with title "1/4 time over"' > $status_file

if grep -q OK < $status_file; then
  success_count="1"
fi
remaining_time=$(echo "$duration_mins - $one_fourth_duration" | bc)
# osascript -e 'Tell application "AnyBar" to set title to "timer_status=1/4 status="$success_count/4 remaining_time=$remaining_time mins'"'
osascript -e 'Tell application "AnyBar" to set title to "timer_status=1/4 score='$success_count/4' remaining_time='$remaining_time' mins"'
osascript -e 'Tell application "AnyBar" to set image name to "yellow"'

timer "$one_fourth_duration" && osascript -e 'Tell application "System Events" to display dialog "'"$two_fourth_duration/$full_duration mins completed. score=$success_count/4"'" with title "2/4 time over"' > $status_file
if grep -q OK < $status_file; then
  success_count=$((success_count+1))
fi
osascript -e 'Tell application "AnyBar" to set title to "timer_status=2/4 score='$success_count/4' remaining_time='$remaining_time' mins"'
osascript -e 'Tell application "AnyBar" to set image name to "yellow"'

if [[ $success_count -gt 1 ]]; then
  osascript -e 'Tell application "AnyBar" to set image name to "green"'
fi

timer "$one_fourth_duration" && osascript -e 'Tell application "System Events" to display dialog "'"$three_fourth_duration/$full_duration mins completed. score=$success_count/4"'" with title "3/4 time over"' > $status_file
if grep -q OK < $status_file; then
  success_count=$((success_count+1))
fi
remaining_time=$(echo "$duration_mins - $two_fourth_duration" | bc)
osascript -e 'Tell application "AnyBar" to set title to "timer_status=3/4 score='$success_count/4' remaining_time='$remaining_time' mins"'

if [[ $success_count -gt 2 ]]; then
  osascript -e 'Tell application "AnyBar" to set image name to "green"'
else
  osascript -e 'Tell application "AnyBar" to set image name to "yellow"'
fi

timer "$one_fourth_duration" && osascript -e 'Tell application "System Events" to display dialog "'"$full_duration/$full_duration mins completed - were you focused?"'" with title "Timer completed"' > $status_file
if grep -q OK < $status_file; then
  success_count=$((success_count+1))
fi
remaining_time=$(echo "$duration_mins - $three_fourth_duration" | bc)
osascript -e 'Tell application "AnyBar" to set title to "timer_status=4/4 score='$success_count/4' remaining_time='$remaining_time' mins"'

if [[ $success_count -lt 2 ]]; then
  osascript -e 'Tell application "AnyBar" to set image name to "red"'
fi

osascript -e 'Tell application "System Events" to display dialog "'"Total score = $success_count/4"'" with title "Timer completed"'
osascript -e 'Tell application "AnyBar" to set title to "timer_status=4/4 score='$success_count/4' remaining_time=0 mins"'
