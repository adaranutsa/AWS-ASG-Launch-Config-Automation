"""
    @Name: AWS ASG Launch Config Automation
    @Author: Aleks Daranutsa
    @Date: 01/05/2018
    @Description: Automatically update ASG Launch Config with the latest AMI from a running instace inside the ASG.
"""

import boto3, time

class AsgConfig:
    
    def __init__(self, profile, region, dryrun, noReboot):

        self.session = boto3.Session(profile_name = profile, region_name = region)
        
        # Store dryrun operation value
        self.dryrun = dryrun
        
        # Store instance restart value
        self.noReboot = noReboot
        
        # The tag to check for and the value
        self.asg_tag_key = 'AsgConfigUpdate'
        self.asg_tag_value = 'true'
        
    def scanAsgs(self):
        """
        Scan all ASGs and check to ensure they are
        not empty before storing them in the list
        """
        
        # ASG boto3 client
        client = self.session.client('autoscaling')
        
        # List to store all ASGs in
        asg_list = []
        
        # Get all ASGs
        asgs = client.describe_auto_scaling_groups()['AutoScalingGroups']
        
        # Loop the ASGs and check if they have instances running in them
        for asg in asgs:

            # If there are instances in the ASG, send the
            # tags to self.checkTags to be checked for the
            # required tags
            if (len(asg['Instances']) > 0):
                
                # If the required tag(s) exists
                # append the ASG to asg_list
                if (self.checkTags(asg['Tags'])):
                    asg_list.append(asg)
        
        # Return the list of ASGs
        return asg_list
     
    def checkTags(self, tags):
        """
        Check tags for the tag key and value
        that is needed for this script and
        return True if it's found
        """
        
        # Check for the required tag
        for tag in tags:
            
            # If the tag key/value pair exists, return True
            if (tag['Key'].lower() == self.asg_tag_key.lower() and tag['Value'].lower() == self.asg_tag_value.lower()):
                return True
            
    
    def updateConfig(self, asgs):
        """
        Get the first instance in each ASG
        and take an AMI of it and update launch config
        """
        
        # Loop all ASGs
        for asg in asgs:
            
            # Create an AMI of one of the ASG instances and get the AMI ID
            ami = self.createAmi(asg['AutoScalingGroupName'], asg['Instances'][0]['InstanceId'])
            
            # Create new launch config with new AMI ID
            result = self.createLaunchConfig(ami, asg['AutoScalingGroupName'], asg['LaunchConfigurationName'])
            
    def createAmi(self, asgName, instanceId):
        """
        Create AMI from given instance and return
        the new AMI ID
        """
        
        # Create the boto resource
        ec2 = self.session.resource('ec2')
        instance = ec2.Instance(instanceId)
        
        # If dryrun is false, create AMI
        if not self.dryrun:
            ami = instance.create_image(
                    NoReboot = self.noReboot,
                    Name = "ami - {} - {}".format(asgName, time.time())
                )
        
        if self.dryrun:
            return False
        
        # Return the AMI ID
        return ami.id
    
    def createLaunchConfig(self, ami, asgName, oldConfigName):
        """
        Clone the old launch config, create a new one with the new
        AMI ID and attach it to the ASG. Then remove the old launch config
        """
        
        # ASG boto3 client
        client = self.session.client('autoscaling')
        
        # Get the old launch configuration
        old_config = client.describe_launch_configurations(
                LaunchConfigurationNames = [
                        oldConfigName
                    ]
            )['LaunchConfigurations'][0]
        
        # Store the new launch config name
        new_name = 'lc-{}-{}'.format(asgName, time.time())
        
        # Arguments for creating the launch config
        args = {
            'LaunchConfigurationName': new_name,
            'ImageId': ami,
            'UserData': old_config['UserData'],
            'InstanceType': old_config['InstanceType'],
            'BlockDeviceMappings': old_config['BlockDeviceMappings'],
            'InstanceMonitoring': old_config['InstanceMonitoring'],
            'EbsOptimized': old_config['EbsOptimized']
        }
        
        # If the keyname exists, add it to the args
        if 'KeyName' in old_config:
            args['KeyName'] = old_config['KeyName']
        
        # If security groups exist, add them to the args
        if 'SecurityGroups' in old_config:
            args['SecurityGroups'] = old_config['SecurityGroups']
        
        # If ClassicLinkVPCId exists, add it to the args
        if 'ClassicLinkVPCId' in old_config:
            args['ClassicLinkVPCId'] = old_config['ClassicLinkVPCId']
          
        # If ClassicLinkVPCSecurityGroups exists, add it to the args
        if 'ClassicLinkVPCSecurityGroups' in old_config:
            args['ClassicLinkVPCSecurityGroups'] = old_config['ClassicLinkVPCSecurityGroups']
        
        # If IamInstanceProfile exists, add it to the args
        if 'IamInstanceProfile' in old_config:
            args['IamInstanceProfile'] = old_config['IamInstanceProfile']
            
        # If AssociatePublicIpAddress exists, add it to the args
        if 'AssociatePublicIpAddress' in old_config:
            args['AssociatePublicIpAddress'] = old_config['AssociatePublicIpAddress']
        
        # Create a new launch configuration
        new_config = client.create_launch_configuration(**args)['ResponseMetadata']
            
        # If the creation of the launch config was successful
        # update the ASG group
        if new_config['HTTPStatusCode'] == 200:
            response = client.update_auto_scaling_group(
                    AutoScalingGroupName = asgName,
                    LaunchConfigurationName = new_name
                )['ResponseMetadata']
        else:
            return "Creating new launch config failed!"
            
        # If updating the ASG was successful
        # delete the old launch config
        if response['HTTPStatusCode'] == 200:
            del_response = client.delete_launch_configuration(
                    LaunchConfigurationName = oldConfigName
                )['ResponseMetadata']
                
        # Ensure deletion of the old config was successful
        if del_response['HTTPStatusCode'] != 200:
            return "Deleting old launch config failed!"
            
        return True
    
    def run(self):
        """
        Run the script to create get ASGs, create AMIs,
        Create new launch configs, and update ASGs
        """
        
        # Get list of ASGs to update AMI on
        asgs = self.scanAsgs()
        
        # Create AMI, Create new launch Config, Update ASG
        self.updateConfig(asgs)
        
if __name__ == '__main__':
    
    # AWS CLI Profile and Region
    profile = 'wind'
    region = 'us-west-2'
    
    # Dry Run operation?
    dryrun = False
    
    # Don't reboot instance when taking AMI?
    # True = Don't reboot instance
    # False = Reboot instance
    noReboot = True
    
    # Instantiate the AsgConfig class with proper parameters
    asg = AsgConfig(profile, region, dryrun, noReboot)
    
    # Launch the operation
    asg.run()
    
    
