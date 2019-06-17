import logging

from algernon import queued, ajson
from algernon.aws import lambda_logged
from aws_xray_sdk.core import xray_recorder

from toll_booth import tasks


# @xray_recorder.capture('surgeon_handler')
@lambda_logged
@queued
def handler(event, context):
    logging.info(f'started a surgeons task, event/context: {event}/{context}')
    task_name = event['task_name']
    task_kwargs = event['task_kwargs']
    task = getattr(tasks, task_name, None)
    if task is None:
        raise RuntimeError(f'can not find task in surgeon module for task_name: {task_name}')
    results = task(**task_kwargs)
    logging.info(f'completed surgeon task: {task_name}, results: {results}')
    return ajson.dumps(results)
