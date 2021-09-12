#!/bin/bash

region=${AWS_DEFAULT_REGION:-ap-south-1}

quota="$(aws service-quotas get-service-quota --region "$region" --service-code ec2 --quota-code L-1216C47A --query 'Quota.Value')"
echo "quota: $quota"

used="$(aws ec2 describe-instances --region ap-south-1 --filters "Name=instance-state-name,Values=running" --query 'Reservations[*].Instances[*].{"InstanceType": InstanceType,"CpuOptions": CpuOptions}' | jq -r '.[][].CpuOptions | [.CoreCount, .ThreadsPerCore] | @csv' | tr ',' '*' | while read -r line; do echo "$line" | bc ; done | paste -sd+ | bc)"
echo "used: $used"

available=$(echo "$quota - $used" | bc)
echo "available: $available"
