import re
from decimal import Decimal

import boto3
import dateutil
import rapidjson


def _parse_s3_uri(storage_uri):
    pattern = re.compile(r'(s3://)(?P<bucket>[^/\s]*)(/)(?P<key>[^\s]*)')
    matches = pattern.search(storage_uri)
    bucket_name = matches.group('bucket')
    file_key = matches.group('key')
    return bucket_name, file_key


def retrieve_s3_property(storage_uri: str):
    bucket_name, file_key = _parse_s3_uri(storage_uri)
    stored_property = boto3.resource('s3').Object(bucket_name, file_key)
    response = stored_property.get()
    serialized_property = response['Body'].read()
    object_property = rapidjson.loads(serialized_property)
    return object_property
