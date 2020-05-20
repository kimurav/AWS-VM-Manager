# AWS EC2 Virtual Machine Deployer and Manager
These collection of scripts are used to interact with Amazon Web Services Elastic Compute Cluster to create Virtual Machines within the AWS cloud. Much like Terraform these scrpts will read a `.yml` file that contains information about a desired instance. Specifically a machine image `ami`, vm type, and the docker images to pull and run in the deployed vm. 

## Example config for a VM
``` yaml
instances:
    - instance:
        ami: ami-0fa94ecf2fef3420b
        os-image-name: Linux
        instance-tag: Linux-1
        type: t2.micro
        key-name: instance_ssh_key
        docker-images:
        - image:
            name: gcc
            command: sudo docker pull gcc
        - image:
            name: golang
            command: sudo docker pull golang
        - image:
            name: julia
            command: sudo docker pull julia
        - image:
            name: swift
            command: sudo docker pull swift
```

- The above blurb of yaml will create a Linux Virtual machine with a t2.micro storage type and pull the `golang`, `gcc`, `juila` and `swift` images into the newly created virtual machine. 

- The `ec2_status_checker.py` script will ping the created VM's and check the health of the containers running in the vm. 

