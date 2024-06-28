#!/bin/bash
set -ex

sudo mv /tmp/amazon-cloudwatch-agent.json /opt/aws/amazon-cloudwatch-agent/etc/amazon-cloudwatch-agent.json
sudo chown cwagent:cwagent /opt/aws/amazon-cloudwatch-agent/etc/amazon-cloudwatch-agent.json
