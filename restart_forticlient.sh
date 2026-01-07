#!/bin/bash

echo "Stopping FortiClient processes..."

# Kill FortiClient processes
sudo pkill -f FortiClient
sudo pkill -f fcconfig
sudo pkill -f fctservctl2
sudo pkill -f epctrl
sudo pkill -f ztnafw

echo "Waiting 2 seconds..."
sleep 2

echo "Starting FortiClient..."
open /Applications/FortiClient.app

echo "FortiClient restart complete!"
