# AWS-ASG-Launch-Config-Automation
Automatically update ASG Launch Config with the latest AMI from a running instace inside the ASG.

## How it works
This script is based on tags. A tag (below) will need to be added to all ASGs that you want to be automatically update with this script. This script will only update the ASG with the latest AMI taken from a server within that ASG Group itself. It will NOT update the launch config with the latest AMI from the marketplace.

### Workflow
Below is the workflow of this script and everything it does.

1. Gets a list of all Autoscaling groups.
2. Check each ASG to ensure it has running instances in it.
3. Check the tags on each ASG to ensure it has `AsgConfigUpdate` tag key with a value of `true`.
4. If step 2 is true (has running instances) and step 3 is true (has the tag added), then add the ASG to a list.
5. Grab the first instance in the ASG, and take an AMI of it. Return the new AMI ID.
6. Get the old ASG launch config, describe the attributes, and create a new launch config using the old attributes and new AMI ID.
7. If launch config creation was successful, update the ASG group with the new launch config.
8. If updating ASG group with new launch config was successful, delete the old launch config.
9. Repeat steps 5-8 for each ASG in the list gathered in steps 2-4.

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
