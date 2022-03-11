import logging

import boto3

log = logging.getLogger(__name__)
log.setLevel(level=logging.DEBUG)


def clean_s3_buckets(pattern: str, delete: bool = False):
    s3 = boto3.resource('s3')
    # TODO is there a paginator?
    buckets = s3.buckets.all()

    for bucket in buckets:
        if pattern in bucket.name:
            log.debug(f"Processing {bucket} S3 bucket")
            
            if delete:
                bucket_versioning = s3.BucketVersioning(bucket.name)

                # we need to delete versioning first
                if bucket_versioning.status == 'Enabled':
                    bucket.object_versions.delete()
                
                log.debug(f"IN PROGRESS - deleting content in {bucket.name}")
                bucket.objects.all().delete()
                log.debug(f"DONE - deleting content in {bucket.name}")

                log.debug(f"IN PROGRESS - deleting bucket {bucket.name}")
                bucket.delete()
                log.info(f"DONE - deleted bucket {bucket.name}")
