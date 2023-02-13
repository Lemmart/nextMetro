import logging
import os
import boto3
import time
import math
from botocore.exceptions import ClientError


def create_presigned_url(object_name):
    """Generate a presigned URL to share an S3 object with a capped expiration of 60 seconds

    :param object_name: string
    :return: Presigned URL as string. If error, returns None.
    """
    s3_client = boto3.client('s3',
                             region_name=os.environ.get('S3_PERSISTENCE_REGION'),
                             config=boto3.session.Config(signature_version='s3v4',s3={'addressing_style': 'path'}))
    try:
        bucket_name = os.environ.get('S3_PERSISTENCE_BUCKET')
        response = s3_client.generate_presigned_url('get_object',
                                                    Params={'Bucket': bucket_name,
                                                            'Key': object_name},
                                                    ExpiresIn=60*1)
    except ClientError as e:
        logging.error(e)
        return None

    # The response contains the presigned URL
    return response


def get_time_left_str(departure_seconds):
    epoch_time_seconds = int(time.time())
    time_left = departure_seconds - epoch_time_seconds
    hours = math.floor(time_left / 3600)
    hours_as_seconds = hours * 3600
    minutes = math.floor((time_left - hours_as_seconds) / 60)
    minutes_as_seconds = minutes * 60
    seconds = math.floor(time_left - hours_as_seconds - minutes_as_seconds)
    if hours > 0:
        return f"{hours} hours, {minutes} minutes, and {seconds} seconds"
    elif minutes > 0:
        return f"{minutes} minutes, and {seconds} seconds"
    else:
        return f"{seconds} seconds"
    