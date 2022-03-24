import logging

import boto3
from botocore.config import Config

from awstower.aws import get_regions

log = logging.getLogger("eks")
log.setLevel(level=logging.DEBUG)

e2e_identifier = "e2etest"


def list_vpc():
    vpcs = {}

    for region in get_regions():

        ec2_client = boto3.client('ec2', config=Config(region_name=region))
        vpcs_resp = ec2_client.describe_vpcs()["Vpcs"]

        vpcs_region = [{"VpcId": vpc["VpcId"], "Tags": vpc.get("Tags", {}).get("Name", "")} for vpc in vpcs_resp]

        log.debug(f"Region {region} has {len(vpcs_region)} vpcs: {vpcs_region}")

        if len(vpcs_region) > 0:
            vpcs[region] = vpcs_region

    return vpcs
