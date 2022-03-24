import logging
from typing import Optional

import typer
from awstower.efs import list_efs, delete_efs

from awstower.eks import delete_old_e2e_cluster, list_eks_clusters
from awstower.s3 import clean_s3_buckets
from awstower.vpc import list_vpc

app = typer.Typer()

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
log = logging.getLogger(__name__)


@app.command()
def eks(e2e_only: bool = False, delete: bool = False):
    # TODO this should be split into multiple commands / eks subcommands
    if delete and e2e_only:
        delete_old_e2e_cluster(3, True)
    else:
        clusters = list_eks_clusters(e2e_only)
        log.info(f"All found clusters: {clusters}")


@app.command()
def s3(pattern: str, delete: bool = False):
    clean_s3_buckets(pattern=pattern, delete=delete)


@app.command()
def efs(pattern: str = None, delete: bool = False):
    if delete:
        delete_efs(pattern)
    else:
        list_efs(pattern=pattern)


@app.command()
def vpc():
    list_vpc()

# TODO need to delete dynamoDB

if __name__ == "__main__":
    app()
