#!/bin/bash

echo "=== CHROME EXTENSION MEMORY USAGE ==="
echo

ps aux | grep "Google Chrome" | grep "extension-process" | grep -v grep | \
awk '{
  mem = $6/1024
  cpu = $3
  cmd = $0
  if (match(cmd, /--renderer-client-id=([0-9]+)/)) {
    client_id = substr(cmd, RSTART+21, RLENGTH-21)
  } else {
    client_id = "unknown"
  }
  printf "%s|%.2f|%.1f\n", client_id, mem, cpu
}' | sort -t'|' -k2 -rn | \
awk -F'|' '
BEGIN {
  printf "%-12s %12s %10s\n", "CLIENT ID", "MEMORY", "CPU %"
  printf "%-12s %12s %10s\n", "---------", "------", "-----"
  total_mem = 0
  total_cpu = 0
}
{
  printf "%-12s %9.2f MB %9.1f%%\n", $1, $2, $3
  total_mem += $2
  total_cpu += $3
}
END {
  printf "\n%-12s %9.2f MB %9.1f%%\n", "TOTAL", total_mem, total_cpu
  printf "\nExtension processes: %d\n", NR
}'

echo
echo "To identify extensions by name:"
echo "1. Open Chrome"
echo "2. Press Shift+Esc (opens Chrome Task Manager)"
echo "3. Match memory values above with extension names in Task Manager"
echo "4. Or visit chrome://extensions to see all installed extensions"
