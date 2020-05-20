import paramiko
import boto3
import sys

def do_command(ssh_client, command):
    print("Executing " + command)
    stdin, stdout, stderr = ssh_client.exec_command(command)
    stdout_content = stdout.read()
    stderr_contents = stderr.read()
    if len(stderr_contents) > 0 :
        print("ERROR: " + stderr_contents.decode('utf-8')) 
    else:
        print(stdout_content.decode('utf-8'))


def connect_and_get_images(dns, ssh_key, image):
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    #CAse ubuntu
    if(image == 'ami-0d0eaed20348a3389'):
        ssh.connect(hostname=dns, username='ubuntu', key_filename=ssh_key)
        do_command(ssh, "sudo docker images")
    #Case podman
    elif(image == 'ami-0b85d4ff00de6a225'):
        ssh.connect(hostname=dns, username='ec2-user', key_filename=ssh_key)
        do_command(ssh, "sudo podman images")
    else:
        ssh.connect(hostname=dns, username='ec2-user', key_filename=ssh_key)
        do_command(ssh, "sudo docker images")
   
    
    ssh.close()


if(len(sys.argv) != 2):
    print("Please enter provide the path to the ssh key")
    sys.exit(0)
ec2 = boto3.resource('ec2')
public_dns = []
instances = ec2.instances
for inst in instances.all():
    try:
        public_dns.append(
            {   
                "name": inst.tags[0],
                "dns": inst.public_dns_name,
                "type": inst.image_id
            }
        )
    except Exception as e:
        print(e)
for inst in public_dns:
    if(inst['dns'] != ''):
        print("STATUS OF " + str(inst['name']['Value']))
        connect_and_get_images(inst['dns'], sys.argv[1],inst['type'])


