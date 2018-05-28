import boto3
import json
import os


def lambda_handler(event, context):
    # Print the Payload
    print("Received event: " + json.dumps(event['Records'][0]['Sns']['Message'], indent=2))

    # Parse the JSON for the Message Key. This key comes from SNS in a JSON String. We use json.loads to make the keys reachable
    data = json.loads(event['Records'][0]['Sns']['Message'])

    # Extract the Instance ID from the Message key
    instance_id = data['EC2InstanceId']
    print("From SNS: " + instance_id)

    # Extract the LifeCycle Hook Name from the Message key
    lifecyclehook = data['LifecycleHookName']
    print("LifeCycleHookName: " + lifecyclehook)

    # Extract the Auto Scaling Group Name from the Message key
    AutoScalingGroupName = data['AutoScalingGroupName']
    print("AutoScalingGroupName: " + AutoScalingGroupName)

    # Extract the event type
    EventType = data['LifecycleTransition']
    print("LifecycleTransition: " + EventType)

    # Retrieve Private IP using the Instance ID retrived above
    ec2 = boto3.client('ec2')
    response = ec2.describe_instances(
        InstanceIds=[instance_id],
    )
    print(response)

    # Extract the Private IP of the instance and load in a variable
    priv = response['Reservations'][0]['Instances'][0]['PrivateIpAddress']
    print(priv)

    # The calls to AWS STS AssumeRole must be signed with the access key ID
    # and secret access key of an existing IAM user or by using existing temporary
    # credentials such as those from antoher role. (You cannot call AssumeRole
    # with the access key for the root account.) The credentials can be in
    # environment variables or in a configuration file and will be discovered
    # automatically by the boto3.client() function. For more information, see the
    # Python SDK documentation:
    # http://boto3.readthedocs.io/en/latest/reference/services/sts.html#client

    # create an STS client object that represents a live connection to the
    # STS service
    sts_client = boto3.client('sts', region_name='us-west-2')

    # Call the assume_role method of the STSConnection object and pass the role
    # ARN and a role session name.
    assumedRoleObject = sts_client.assume_role(
        RoleArn="arn:aws:iam::105543924355:role/adfs-prod-waf-admins",
        RoleSessionName="LambdaAddTargetstoALB"
    )

    # From the response that contains the assumed role, get the temporary
    # credentials that can be used to make subsequent API calls
    credentials = assumedRoleObject['Credentials']

    # Use the temporary credentials that AssumeRole returns to make a
    # connection to Amazon ELBV2
    client = boto3.client('elbv2',
                          region_name='us-west-2',
                          aws_access_key_id=credentials['AccessKeyId'],
                          aws_secret_access_key=credentials['SecretAccessKey'],
                          aws_session_token=credentials['SessionToken'],
                          )


    if EventType == 'autoscaling:EC2_INSTANCE_LAUNCHING':

    # Use the Amazon ELBV2 resource object that is now configured with the
    # credentials to access the load balancer

    # Make the call to register the instaince with the target group identified below in the prod Waf account.
        register1 = client.register_targets(
            TargetGroupArn='arn:aws:elasticloadbalancing:us-west-2:105543924355:targetgroup/jefftest/fecf5b42e7f315e8',
            Targets=[
                {
                    'Id': priv,
                    'Port': 80,
                    'AvailabilityZone': 'all'
                   
    
                },
            ]
        )
        register2 = client.register_targets(
            TargetGroupArn='arn:aws:elasticloadbalancing:us-west-2:105543924355:targetgroup/test2/e0235c2d71c8b31f',
            Targets=[
                {
                    'Id': priv,
                    'Port': 80,
                    'AvailabilityZone': 'all'
                   
    
                },
            ]
        )
        register3 = client.register_targets(
            TargetGroupArn='arn:aws:elasticloadbalancing:us-west-2:105543924355:targetgroup/test3/f5f08d031364d307',
            Targets=[
                {
                    'Id': priv,
                    'Port': 80,
                    'AvailabilityZone': 'all'
                   
    
                },
            ]
        )
             
        
        
    elif EventType == 'autoscaling:EC2_INSTANCE_TERMINATING':

        register1 = client.deregister_targets(
            TargetGroupArn='arn:aws:elasticloadbalancing:us-west-2:105543924355:targetgroup/jefftest/fecf5b42e7f315e8',
            Targets=[
                {
                    'Id': priv,
                    'Port': 80,
                    
                    
                },
            ]
        )
        register2 = client.deregister_targets(
            TargetGroupArn='arn:aws:elasticloadbalancing:us-west-2:105543924355:targetgroup/test2/e0235c2d71c8b31f',
            Targets=[
                {
                    'Id': priv,
                    'Port': 80,
                    'AvailabilityZone': 'all'
                   
    
                },
            ]
        )
        register3 = client.deregister_targets(
            TargetGroupArn='arn:aws:elasticloadbalancing:us-west-2:105543924355:targetgroup/test3/f5f08d031364d307',
            Targets=[
                {
                    'Id': priv,
                    'Port': 80,
                    'AvailabilityZone': 'all'
                   
    
                },
            ]
        )
      

    # Create an auto scaling client to terminate the life cycle hook scaling up event.
    asg = boto3.client('autoscaling')

    endhook = asg.complete_lifecycle_action(
        LifecycleHookName=lifecyclehook,
        AutoScalingGroupName=AutoScalingGroupName,
        LifecycleActionResult='CONTINUE',
        InstanceId=instance_id
    )
