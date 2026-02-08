#!/bin/bash

echo "=== SYSTEM LOAD ==="
uptime | awk -F'load averages:' '{print "Load Average:" $2}'

echo -e "\n=== MEMORY USAGE ==="
total_mem=$(sysctl -n hw.memsize | awk '{print $1/1024/1024/1024}')
free_mem=$(vm_stat | perl -ne '/page size of (\d+)/ and $size=$1; /Pages free[^\d]+(\d+)/ and printf("%.2f", $2 * $size / 1024 / 1024 / 1024);')
used_mem=$(echo "$total_mem - $free_mem" | bc)
util_pct=$(echo "scale=2; ($used_mem / $total_mem) * 100" | bc)
printf "Total Memory:  %.2f GB\n" $total_mem
printf "Free Memory:   %.2f GB\n" $free_mem
printf "Used Memory:   %.2f GB (%.1f%%)\n\n" $used_mem $util_pct
vm_stat | perl -ne '/page size of (\d+)/ and $size=$1; /Pages\s+([^:]+)[^\d]+(\d+)/ and printf("%-25s %10.2f MB\n", "$1:", $2 * $size / 1048576);' | grep -E "(free|active|inactive|wired|occupied by compressor)"

echo -e "\n=== TOP 10 MEMORY CONSUMERS ==="
printf "%-70s %15s\n" "PROCESS" "MEMORY"
printf "%-70s %15s\n" "-------" "------"
ps aux | awk 'NR>1 {mem=$6/1024; cmd=""; for(i=11;i<=NF;i++) cmd=cmd $i " "; printf "%12.2f|%-70s\n", mem, substr(cmd,1,70)}' | sort -t'|' -k1 -rn | head -10 | awk -F'|' '{printf "%-70s %12.2f MB\n", $2, $1}'

echo -e "\n=== TOP 10 CPU CONSUMERS ==="
printf "%-70s %15s\n" "PROCESS" "CPU %"
printf "%-70s %15s\n" "-------" "-----"
ps aux | awk 'NR>1 {cpu=$3; cmd=""; for(i=11;i<=NF;i++) cmd=cmd $i " "; printf "%14.1f|%-70s\n", cpu, substr(cmd,1,70)}' | sort -t'|' -k1 -rn | head -10 | awk -F'|' '{printf "%-70s %14.1f%%\n", $2, $1}'

echo -e "\n=== MEMORY BY PROCESS NAME ==="
printf "%-40s %15s\n" "PROCESS NAME" "TOTAL MEMORY"
printf "%-40s %15s\n" "------------" "------------"
ps aux | awk 'NR>1 {
  mem=$6/1024;
  cmd=$11;
  gsub(/^.*\//, "", cmd);
  total[cmd]+=mem;
}
END {
  for (cmd in total) printf "%12.2f|%-40s\n", total[cmd], cmd
}' | sort -t'|' -k1 -rn | head -10 | awk -F'|' '{printf "%-40s %12.2f MB\n", $2, $1}'
