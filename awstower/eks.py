import datetime
import logging

import boto3
from botocore.config import Config

log = logging.getLogger("eks")
log.setLevel(level=logging.DEBUG)


def list_eks_clusters(e2e_only: bool = False):
    # there is a problem with the region due to missing IAM permissions
    blacklisted_regions = ["ap-northeast-3"]

    clusters = {}

    for region in get_regions():

        region_name = region["RegionName"]

        if region_name in blacklisted_regions:
            log.warning(f"skipping region {region_name}")
            continue

        client = boto3.client('eks', config=Config(region_name=region_name))
        region_clusters = client.list_clusters()["clusters"]

        log.debug(f"region {region_name} has clusters: {region_clusters}")

        if e2e_only:
            region_clusters = [r for r in region_clusters if "e2etest" in r]

        if len(region_clusters) > 0:
            clusters[region_name] = region_clusters

    return clusters


def delete_old_e2e_cluster(age_in_hours: int = 0, delete: bool = False):
    region_clusters = list_eks_clusters(e2e_only=True)
    datetime_threshold = datetime.datetime.now().astimezone() - datetime.timedelta(hours=age_in_hours)
    log.info(f"Date threshold is = {datetime_threshold}")

    for region in region_clusters:
        client = boto3.client('eks', config=Config(region_name=region))
        for cluster in region_clusters[region]:
            # fetch information about cluster
            cluster_response = client.describe_cluster(name=cluster)
            cluster_created = cluster_response['cluster']['createdAt']

            # is the cluster older than threshold?
            age = datetime.datetime.now().astimezone() - cluster_created
            should_be_deleted = cluster_created < datetime_threshold

            log.debug(f"The cluster {cluster} in region {region} is {age} and should be deleted = {should_be_deleted}")

            if delete and should_be_deleted:
                delete_cluster(client, cluster, region)


def delete_cluster(client, cluster, region):
    log.debug(f"IN PROGRESS - deleting cluster {cluster}")
    node_groups_response = client.list_nodegroups(clusterName=cluster)
    node_groups = node_groups_response['nodegroups']
    for node_group in node_groups:
        delete_nodegroup(client, cluster, node_group, region)
    client.delete_cluster(name=cluster)
    waiter = client.get_waiter('cluster_deleted')
    waiter.wait(
        name=cluster,
        WaiterConfig={
            'Delay': 10,
            'MaxAttempts': 50
        }
    )
    log.info(f"DONE - cluster {cluster} deleted")


def delete_nodegroup(client, cluster, node_group, region):
    log.debug(f"IN PROGRESS - deleting node_group {node_group}")
    nodegroup_resp = client.describe_nodegroup(clusterName=cluster, nodegroupName=node_group)
    asgs = nodegroup_resp['nodegroup']['resources']['autoScalingGroups']
    for asg in asgs:
        delete_asg(asg, region)
    client.delete_nodegroup(clusterName=cluster, nodegroupName=node_group)
    waiter = client.get_waiter('nodegroup_deleted')
    waiter.wait(
        clusterName=cluster,
        nodegroupName=node_group,
        WaiterConfig={
            'Delay': 10,
            'MaxAttempts': 50
        }
    )


def delete_asg(asg, region):
    log.debug(asg)
    asg_client = boto3.client('autoscaling', config=Config(region_name=region))
    log.debug(f"IN PROGRESS - deleting {asg['name']}")
    response = asg_client.delete_auto_scaling_group(
        AutoScalingGroupName=asg['name'],
        ForceDelete=True,
    )
    log.info(f"DONE - deleted {asg['name']}")


def get_regions():
    # Retrieves all regions/endpoints that work with EC2
    ec2 = boto3.client('ec2')
    regions = ec2.describe_regions()["Regions"]
    return regions
