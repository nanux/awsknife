import datetime
import logging

import boto3
from botocore.config import Config
from click import Abort
import typer

from awstower.eks import get_regions

log = logging.getLogger(__name__)
log.setLevel(level=logging.DEBUG)


def list_efs(pattern: str = None) -> dict: 
    now = datetime.datetime.now().astimezone()
    filesystems_result = {}

    for region in get_regions():

        client = boto3.client("efs", config=Config(region_name=region))
        fs_response = client.describe_file_systems()

        filesystems = fs_response["FileSystems"]
        if pattern:
            filesystems = [f for f in filesystems if pattern in f.get('Name', '')]

        for fs in filesystems:
            log.info(
                f"EFS, region={region} fs_name={fs.get('Name', 'null')} fs_id={fs['FileSystemId']}, age={now - fs['CreationTime']}")

        if len(filesystems) > 0:
            filesystems_result[region] = filesystems

    return filesystems_result


# TODO add the time age to prevent messing up with running end to end tests
# Right now, the won't be deleted as this function won't fail because the will be marked as "InUse"
def delete_efs(pattern: str):
    filesystems = list_efs(pattern)

    typer.echo(f"EFS systems to delete:")
    typer.echo(filesystems)
    delete = typer.confirm("Are you sure you want to delete it?", abort=True)
    if delete:
        # FIXME coloring doesn't work
        typer.secho("Deleting filesystems", color=typer.colors.RED)
        for region in filesystems.keys():
            client = boto3.client("efs", config=Config(region_name=region))
            for fs in filesystems[region]:
                fs_id = fs['FileSystemId']
                log.debug(f"IN PROGRESS - deleting EFS {fs_id} in region {region}")

                targets = client.describe_mount_targets(FileSystemId=fs_id)
                for target in targets["MountTargets"]:
                    target_id = target["MountTargetId"]
                    log.debug(f"IN PROGRESS - deleting EFS mount target {target_id} in region {region}")
                    # FIXME this doesn't wait so we need to create a custom wait method as there is no official EFS waiter
                    client.delete_mount_target(MountTargetId=target_id)
                    log.info(f"DONE - deleted EFS {target_id} in region {region}")

                client.delete_file_system(FileSystemId=fs["FileSystemId"])
                log.info(f"DONE - deleted EFS {fs_id} in region {region}")

