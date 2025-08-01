#!/bin/bash

# Install CloudWatch Agent
CLOUDWATCH_AGENT_DEB_URL="https://s3.amazonaws.com/amazoncloudwatch-agent/ubuntu/amd64/latest/amazon-cloudwatch-agent.deb"

# Download and install the CloudWatch agent
echo "Downloading CloudWatch Agent..."
wget $CLOUDWATCH_AGENT_DEB_URL

# Install the package
echo "Installing CloudWatch Agent..."
sudo dpkg -i amazon-cloudwatch-agent.deb

# Clean up the installer file
rm amazon-cloudwatch-agent.deb
