# AWS-ASG-Launch-Config-Automation
Automatically update ASG Launch Config with the latest AMI from a running instace inside the ASG.

## How it works
This script is based on tags. A tag (below) will need to be added to all ASGs that you want to be automatically update with this script. This script will only update the ASG with the latest AMI taken from a server within that ASG Group itself. It will NOT update the launch config with the latest AMI from the marketplace.

## Requirements
You need to tag any ASGs you want to be updated with the following tag key/value pair.

`AsgConfigUpdate` -> `true`

## Usage
Before using the script, you will need to configure an AWS CLI profile and insert it in the script.
Afterwards, you can simply run it: `python3 asg_config_update.py`

## Considerations
* This script will take an image of the first server in your ASG.
* The old launch config will be deleted as part of clean up operations.
* The script will NOT wait until the AMI is fully available to create new launch config and update ASG. Doing so will take too long to run the script.
* This script will NOT clean up old AMIs.
