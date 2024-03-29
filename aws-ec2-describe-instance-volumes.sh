#!/bin/bash

# Usage
# $0 # without filters
# $0 "Name=tag:eks:nodegroup-name,Values=nodegroup" "Name=instance-state-name,Values=running" # with filters

aws ec2 describe-instances --filters $* | jq -r '.Reservations[].Instances[] | [.InstanceId, ((.Tags[] | select(.Key=="Name") | .Value) // "empty_name"), .BlockDeviceMappings[].Ebs.VolumeId] | @csv' | while read line; do
  instance_id=$(echo "$line" | cut -f1 -d ',' | tr -d '"')
  name=$(echo "$line" | cut -f2 -d ',' | tr -d '"')
  volume_ids=$(echo "$line" | cut -f3- -d ',' | tr  ',' ' '| tr -d '"')
  for volume_id in $(echo "$volume_ids" | cut -f1- -d' '); do
    echo -n "$instance_id,$name,$volume_id,"
    aws ec2 describe-volumes --volume-ids "$volume_id" | jq -r '.Volumes[] | [.Attachments[].Device, .Size]| @csv' | tr -d '"'
  done
done
