import yaml
import boto3
import os
import stat
import sys
import time
import paramiko
from botocore.exceptions import ClientError

ec2_client = boto3.client('ec2')

def tag_instance(instance_ids):
    i = 1
    for instance_id in instance_ids:
        response = ec2_client.create_tags(
            Resources=[
                instance_id,
            ],
            Tags = [
                {
                    'Key':'Name',
                    'Value': 'instance-'+str(i)
                },
            ]
        )
        i+=1

def get_instance_ids():
    resp = ec2_client.describe_instances()
    instance_response = resp['Reservations']
    inst_ids = []
    for inst_obj in instance_response:
        inst_ids.append(inst_obj['Instances'][0]['InstanceId'])
    return inst_ids
  

def create_ec2_instance(image_id, instance_type, key_name, instance_name):
    try:
        print("Provisioning instace "+ image_id)
        tags = [
            {
                "ResourceType": "instance",
                "Tags": [
                        {
                            "Key": "Name",
                            "Value": instance_name
                        }
                    ]
                }
        ]
        response = ec2_client.run_instances(
            ImageId=image_id,
            InstanceType=instance_type,
            MaxCount=1,
            MinCount=1,
            KeyName=key_name,
            TagSpecifications=tags
        )
        print("Finished Provision instance " + image_id)
    except ClientError as e:
        print(e)
        return None
    return response

# Create a file for the ssh key the name is what the .pem file will be named
def create_ssh_key(name):
    try:
        resp = ec2_client.create_key_pair(KeyName=name)
        fileName = name + '.pem'
        with open(fileName, "w") as file:
            file.write(resp['KeyMaterial'])
            file.close()
        os.chmod(fileName, stat.S_IREAD)
    except ClientError as c:
        print("key pair " + name + " already exists")
    
def wait_instance_deploy(instance_ids):
    ec2_resource = boto3.resource('ec2')
    num_instances = len(instance_ids)
    wait_list = []
    for instance_id in instance_ids:
        instance = ec2_resource.Instance(instance_id)
        if instance.state['Code'] == 16 or instance.state['Code'] == 0:
            instance.wait_until_running()

def filter_running_instances(instance_ids):
    newIds = []
    ec2_resource = boto3.resource('ec2')
    for instance_id in instance_ids:
        instance = ec2_resource.Instance(instance_id)
        if instance.state['Code'] == 16:
            newIds.append(instance_id)
    return newIds

def do_command(ssh_client, command):
    print("Executing " + command)
    stdin, stdout, stderr = ssh_client.exec_command(command)
    stdout_content = stdout.read()
    stderr_contents = stderr.read()
    if len(stderr_contents) > 0 :
        print("ERROR: " + stderr_contents.decode('utf-8')) 
    else:
        print(stdout_content.decode('utf-8'))
    
def connect_and_execute(instance_resource, ssh_file, yml_file):
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    print("connecting to "+ instance_resource.public_dns_name)
    for instance in yml_file:
        inst_tag = ''
        for tag in instance_resource.tags:
            if (tag['Key'] == 'Name'):
                inst_tag = tag['Value']
        if(instance['instance']['instance-tag'] == inst_tag):
            inst = instance['instance']
            if((inst['os-image-name'] == 'Linux') or (inst['os-image-name'] == 'Redhat') ):
                print('installing docker on linux or redhat')
                ssh.connect(hostname=str(instance_resource.public_dns_name), username='ec2-user', key_filename=ssh_file)
                do_command(ssh, "sudo yum -y update")
                do_command(ssh, "sudo yum install docker -y")
                do_command(ssh, "sudo service docker start")
                do_command(ssh, "sudo usermod -a -G docker ec2-user")
                for img in inst['docker-images']:
                    do_command(ssh, img['image']['command'])
            elif((inst['os-image-name'] == 'Ubuntu') or (inst['os-image-name'] == 'Suse')):
                print('installing docker on ubuntu')
                if(inst['os-image-name'] == 'Suse'):
                    time.sleep(20)
                    ssh.connect(hostname=str(instance_resource.public_dns_name), username='ec2-user', key_filename=ssh_file)    
                else:
                    ssh.connect(hostname=str(instance_resource.public_dns_name), username='ubuntu', key_filename=ssh_file)
                get_install_script = 'curl -fsSL https://get.docker.com -o get-docker.sh'
                do_command(ssh, get_install_script)
                run_install_script = 'sudo sh get-docker.sh'
                do_command(ssh, run_install_script)
                if(inst['os-image-name'] == 'Suse'):
                    do_command(ssh, "sudo service docker start")
                for img in inst['docker-images']:
                    do_command(ssh, img['image']['command'])
            

    ssh.close()



def main():
    ec2_resource = boto3.resource('ec2')
    with open("./ec2.yml") as file:
        yml = yaml.load(file, Loader=yaml.FullLoader)
    create_ssh_key(yml['ssh-key'])
    for instance in yml['instances']:
        resp = create_ec2_instance(instance['instance']['ami'], instance['instance']['type'], yml['ssh-key'], instance['instance']['instance-tag'])
    instance_ids = get_instance_ids()
    print("Waiting on instances to enter a running state....")
    wait_instance_deploy(instance_ids)
    instance_ids = filter_running_instances(instance_ids)
    time.sleep(10)
    for inst_id in instance_ids:
        connect_and_execute(ec2_resource.Instance(str(inst_id)), yml['ssh-key']+'.pem', yml['instances'])
    
    sys.exit(0)



main()