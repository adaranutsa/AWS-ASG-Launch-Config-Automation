# AWS-ASG-Launch-Config-Automation
Automatically update ASG Launch Config with the latest AMI from a running instace inside the ASG.

**NOTE: This is a work in progress**

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
You need to tag any ASGs you want to be updated with the following tag key/value pair. This will use all the default parameters (see default parameters table below).

`AsgConfigUpdate` -> `true`

### Default parameters
The following default parameters are stored in DynamoDB if using Lambda and within the script itself if using the standalone script.

| Parameter | Default value | Parameter Description |
|--|--|--|
| Enabled | None | Enable or disable script execution |
| No Reboot? | true | Whether to reboot the instance while taking an AMI or not. True = Don't reboot. False = Reboot. |
| LC Retainer | 2 | How many Launch Configurations to retain/keep. Any launch configurations created by this script over this defined value will be deleted |
| AMI Retainer | 2 | How many AMIs to retain/keep. Any AMIs created by this script over this define value will be deleted. |
| Source Instance | None | The Instance ID of the instance to use for creating the AMI. If this is empty, the first instance in the ASG is used. |


### Parameter Configuration
Parameters need to be configured in this exact order: `enabled;noreboot;lc_retainer;ami_retainer;source_instance`

Full Example: `true;false;5;5;i-avdf3423assd4`

You have the option of leaving certain parameters empty to use defaults and specifying other parameters.

The following example will enable ASG backup, use default no reboot, lc, and ami retainer, but specify a source instance.
Example: `true;;;;i-avdf3423assd4`

**NOTE: If you leave source instance blank, the script will automatically use the first instance in the ASG as the source instance. So if you have a golden image, make sure to use that instead.**

### Example Configurations
| Tag Value | Description |
| -- | -- |
| true | Enable script, use defaults |
| false | Disable script
| true;false | Enable script, set no reboot false |
| true;;5;5 | Enable script, lc and ami retainer is 5. Defaults for the rest |
| true;;;i-avdf3423assd4 | Enable script, set source instance. Defaults for the rest |
| true;false;5;5;i-avdf3423assd4 | Enable script, set no reboot false, lc and ami retainer is 5. Set instance source |
| false;;5;5 | Parameters configured, but script execution is disabled |

## Usage
Before using the script, you will need to configure an AWS CLI profile and insert it in the script.
Afterwards, you can simply run it: `python3 asg_config_update.py`

## Considerations
* The script will NOT wait until the AMI is fully available to create new launch config and update ASG. Doing so will take too long to run the script.
