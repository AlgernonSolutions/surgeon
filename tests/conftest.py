import json
import os
from os import path
from unittest.mock import patch

import pytest
import rapidjson


@pytest.fixture
def integration_environment():
    os.environ['GQL_ENDPOINT'] = 'https://jlgmowxwofe33pdekndakyzx4i.appsync-api.us-east-1.amazonaws.com/graphql'
    os.environ['GRAPH_GQL_ENDPOINT'] = 'https://jlgmowxwofe33pdekndakyzx4i.appsync-api.us-east-1.amazonaws.com/graphql'
    os.environ['ASSET_BUCKET'] = 'algernonsolutions-leech-dev'


@pytest.fixture(params=[
    '944f82670ea35b4f662eeb02108c3a86',
    '4ab55f79cc3170c00f0f2572e26ef428'
])
def encounter_internal_id(request):
    return request.param


@pytest.fixture(params=[
    'c2ae800091ec137422b9658fe64daddf'
])
def client_internal_id(request):
    return request.param


@pytest.fixture(params=[
    ("#vertex#Encounter#{\"id_source\": \"PSI\"}#", 'Community Support')
])
def comm_supt_data(request):
    return request.param


@pytest.fixture
def generate_queued_sns_event():
    def generate(event):
        event_string = rapidjson.dumps(event)
        message_object = {'Message': event_string}
        body_object = {'body': rapidjson.dumps(message_object)}
        return {'Records': [body_object]}
    return generate


@pytest.fixture
def retrieve_queued_sns_event():
    def retrieve(event_name):
        event = _read_test_event(event_name)
        event_string = rapidjson.dumps(event)
        message_object = {'Message': event_string}
        body_object = {'body': rapidjson.dumps(message_object)}
        return {'Records': [body_object]}
    return retrieve


@pytest.fixture
def mock_context():
    from unittest.mock import MagicMock
    context = MagicMock(name='context')
    context.__reduce__ = cheap_mock
    context.function_name = 'test_function'
    context.invoked_function_arn = 'test_function_arn'
    context.aws_request_id = '12344_request_id'
    context.get_remaining_time_in_millis.side_effect = [1000001, 500001, 250000, 0]
    return context


def cheap_mock(*args):
    from unittest.mock import Mock
    return Mock, ()


@pytest.fixture(autouse=True)
def silence_x_ray():
    x_ray_patch_all = 'algernon.aws.lambda_logging.patch_all'
    patch(x_ray_patch_all).start()
    yield
    patch.stopall()


def _read_test_event(event_name):
    with open(path.join('tests', 'test_events', f'{event_name}.json')) as json_file:
        event = json.load(json_file)
        return event

