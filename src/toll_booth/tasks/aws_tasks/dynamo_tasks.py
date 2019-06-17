import boto3
from boto3.dynamodb.conditions import Key, Attr


def push_surgical_data(data_identifier, data_id, surgical_data):
    table = boto3.resource('dynamodb')
    table.put_item(
        Item=surgical_data,
        ConditionExpression=Attr('data_identifier_stem').not_exists() & Attr('data_id').not_exists()
    )
