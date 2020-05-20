import boto3
import pprint
import logging
from botocore.exceptions import ClientError


ec2_client = boto3.client('ec2')
pp = pprint.PrettyPrinter()

def terminate_vms(instance_ids):
    try:
        states = ec2_client.terminate_instances(InstanceIds=instance_ids)
    except ClientError as e:
        logging.error(e)
        return None
    return states['TerminatingInstances']


def get_instance_ids():
    resp = ec2_client.describe_instances()
    instance_response = resp['Reservations']
    inst_ids = []
    for inst_obj in instance_response:
        inst_ids.append(inst_obj['Instances'][0]['InstanceId'])
    return inst_ids

def main():
    logging.basicConfig(level=logging.DEBUG,
                        format='%(levelname)s: %(asctime)s: %(message)s')
    inst_ids = get_instance_ids()
    states = terminate_vms(inst_ids)
    if states is not None:
        logging.debug('Terminating the following EC2 instances')
        for state in states:
            logging.debug(f'ID: {state["InstanceId"]}')
            logging.debug(f'  Current state: Code {state["CurrentState"]["Code"]}, '
                          f'{state["CurrentState"]["Name"]}')
            logging.debug(f'  Previous state: Code {state["PreviousState"]["Code"]}, '
                          f'{state["PreviousState"]["Name"]}')

main()