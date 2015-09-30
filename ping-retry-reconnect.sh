#!/bin/bash

# ping, retry, reconnect, repeat.

target=${1:-'4.2.2.2'}

while :; do
  echo "STATUS: $target: pinging"
  ping -c 5 $target >/dev/null

  if [[ $? != 0 ]]; then
    echo "WARN: $target: ping failed. Sleep for 10 and re-ping..."
    sleep 10
    echo "STATUS: $target: re-pinging"

    ping -c 5 $target >/dev/null

    if [[ $? != 0 ]]; then
      msg="ALERT: $target: re-ping failed. Toggling wifi with 5 second gap"
      notify-send -t 3000 "$msg"
      echo $msg

      nmcli radio wifi off
      sleep 5

      msg="ALERT: $target: wifi off. Sleep for 5 and re-enable"
      notify-send -t 3000 "$msg"
      echo $msg

      sleep 5
      nmcli radio wifi on

      wifi_status=$(nmcli radio wifi)

      if [[ "X$wifi_status" == 'Xenabled' ]]; then
        msg="STATUS: wifi toggled. Sleep for 15 and re-ping"
        notify-send -t 3000 "$msg"
        echo $msg

        sleep 15
        ping -c 5 $target >/dev/null

        if [[ $? == 0 ]]; then
          msg="STATUS: we are back in business baby!"
          notify-send -t 3000 "$msg"
          echo $msg
        else
          msg="STATUS: Reconnect re-ping failed. God help us!!"
          notify-send -t 3000 "$msg"
          echo $msg
          exit 1
        fi
      else
        msg="STATUS: Failed to enable wifi. All yours."
        notify-send -t 3000 "$msg"
        echo $msg
        exit 1
      fi
    fi

  fi
  echo "SUCCESS: $target: pinged"
  sleep 5

done
