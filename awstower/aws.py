import boto3

# there is a problem with the region due to missing IAM permissions


blacklisted_regions = ["ap-northeast-3"]


def get_regions():
    # Retrieves all regions/endpoints that work with EC2
    ec2 = boto3.client("ec2")
    regions = ec2.describe_regions()["Regions"]

    result = [
        region["RegionName"]
        for region in regions
        if region["RegionName"] not in blacklisted_regions
    ]

    return result
