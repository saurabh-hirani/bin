#!/bin/bash

aws route53 list-hosted-zones | jq -rc '.HostedZones[] | [.Id,.Name] | @csv' | sed 's/"//g;s/\.$//g' | while read line; do zone_id=$(echo $line | cut -f1 -d',' | cut -f3 -d'/'); domain=$(echo $line | cut -f2 -d','); aws route53 list-resource-record-sets --hosted-zone-id $zone_id | tee -a /var/tmp/aws-route53-$domain-records.json; done
