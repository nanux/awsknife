import datetime
import logging

import boto3
from botocore.config import Config

from awstower.aws import get_regions

log = logging.getLogger("eks")
log.setLevel(level=logging.DEBUG)

e2e_identifier = "e2etest"


def list_eks_clusters(e2e_only: bool = False):
    clusters = {}

    for region in get_regions():
        
        eks_client = boto3.client('eks', config=Config(region_name=region))
        region_clusters = eks_client.list_clusters()["clusters"]

        log.debug(f"Region {region} has clusters: {region_clusters}")

        if e2e_only:
            region_clusters = [cluster for cluster in region_clusters if e2e_identifier in cluster]

        if len(region_clusters) > 0:
            clusters[region] = region_clusters

    return clusters


def delete_old_e2e_cluster(age_in_hours: int = 0, delete: bool = False):
    region_clusters = list_eks_clusters(e2e_only=True)
    datetime_threshold = datetime.datetime.now().astimezone() - datetime.timedelta(hours=age_in_hours)
    log.info(f"Date threshold is = {datetime_threshold}")

    for region in region_clusters:
        eks_client = boto3.client('eks', config=Config(region_name=region))
        for cluster in region_clusters[region]:
            # fetch information about cluster
            cluster_response = eks_client.describe_cluster(name=cluster)
            cluster_created = cluster_response['cluster']['createdAt']

            # is the cluster older than threshold?
            age = datetime.datetime.now().astimezone() - cluster_created
            should_be_deleted = cluster_created < datetime_threshold

            log.debug(f"The cluster {cluster} in region {region} is {age} and should be deleted = {should_be_deleted}")

            if delete and should_be_deleted:
                delete_cluster(eks_client, cluster, region)


def delete_cluster(eks_client, cluster, region):
    log.debug(f"IN PROGRESS - deleting cluster {cluster}")
    node_groups_response = eks_client.list_nodegroups(clusterName=cluster)
    node_groups = node_groups_response['nodegroups']
    for node_group in node_groups:
        delete_nodegroup(eks_client, cluster, node_group, region)
    eks_client.delete_cluster(name=cluster)
    # delete_cluster doesn't wait so we need to invoke waiter
    waiter = eks_client.get_waiter('cluster_deleted')
    waiter.wait(
        name=cluster,
        WaiterConfig={
            'Delay': 10,
            'MaxAttempts': 50
        }
    )
    log.info(f"DONE - cluster {cluster} deleted")


def delete_nodegroup(eks_client, cluster, node_group, region):
    log.debug(f"IN PROGRESS - deleting node_group {node_group}")
    nodegroup_resp = eks_client.describe_nodegroup(clusterName=cluster, nodegroupName=node_group)
    asgs = nodegroup_resp['nodegroup']['resources']['autoScalingGroups']
    for asg in asgs:
        delete_asg(asg, region)
    eks_client.delete_nodegroup(clusterName=cluster, nodegroupName=node_group)

    # delete_nodegroup doesn't wait so we need to invoke waiter
    waiter = eks_client.get_waiter('nodegroup_deleted')
    waiter.wait(
        clusterName=cluster,
        nodegroupName=node_group,
        WaiterConfig={
            'Delay': 10,
            'MaxAttempts': 50
        }
    )


def delete_asg(asg, region):
    asg_client = boto3.client('autoscaling', config=Config(region_name=region))
    log.debug(f"IN PROGRESS - deleting {asg['name']}")
    asg_client.delete_auto_scaling_group(
        AutoScalingGroupName=asg['name'],
        ForceDelete=True,
    )
    log.info(f"DONE - deleted {asg['name']}")

