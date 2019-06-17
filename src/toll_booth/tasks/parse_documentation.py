import os
from datetime import datetime

from algernon.aws import Bullhorn
from algernon import ajson

from toll_booth.obj.gql.gql_client import GqlClient
from toll_booth.tasks import aws_tasks, parsers

documentation_map = {
    'PSI': 'dcdbh',
    'ICFS': 'dcdbh'
}


def _publish_documentation_node(encounter_id, parser_id, id_source, bullhorn):
    task_name = 'leech'
    leech_arn = bullhorn.find_task_arn(task_name)
    generation_utc_datetime = datetime.utcnow()
    documentation_node = {
        'encounter_id': encounter_id,
        'id_source': id_source,
        'parser_id': parser_id,
        'utc_generated_datetime': generation_utc_datetime.isoformat()
    }
    message = {
        'task_name': task_name,
        'task_kwargs': {
            'object_type': 'Documentation',
            'extracted_data': {'source': documentation_node}
        }
    }
    strung_event = ajson.dumps(message)
    bullhorn.publish('new_event', leech_arn, strung_event)


def _publish_documentation_field_node(encounter_id, id_source, parser_id, field_name, field_documentation, bullhorn):
    task_name = 'leech'
    leech_arn = bullhorn.find_task_arn(task_name)
    documentation_field_node = {
        'encounter_id': encounter_id,
        'id_source': id_source,
        'parser_id': parser_id,
        'field_name': field_name,
        'field_documentation': field_documentation
    }
    message = {
        'task_name': task_name,
        'task_kwargs': {
            'object_type': 'DocumentationField',
            'extracted_data': {'source': documentation_field_node}
        }
    }
    strung_event = ajson.dumps(message)
    bullhorn.publish('new_event', leech_arn, strung_event)


def _publish_results(encounter_id, parser_id, id_source, parser_results):
    bullhorn = Bullhorn.retrieve(profile=os.getenv('AWS_PROFILE'))
    publish_kwargs = {
        'encounter_id': encounter_id,
        'id_source': id_source,
        'parser_id': parser_id,
        'bullhorn': bullhorn
    }
    _publish_documentation_node(**publish_kwargs)
    for field_name, field_documentation in parser_results.items():
        publish_kwargs.update({
            'field_name': field_name,
            'field_documentation': field_documentation
        })
        _publish_documentation_field_node(**publish_kwargs)


def parse_documentation(encounter_internal_id):
    gql_endpoint = os.environ['GRAPH_GQL_ENDPOINT']
    client = GqlClient.from_gql_endpoint(gql_endpoint)
    documentation_property = client.get_documentation_property(encounter_internal_id)
    documentation_uri = documentation_property['documentation']['storage_uri']
    documentation = aws_tasks.retrieve_s3_property(documentation_uri)
    id_source = documentation_property['id_source']['property_value']
    encounter_id = documentation_property['encounter_id']['property_value']
    parser_name = id_source
    if id_source in documentation_map:
        parser_name = documentation_map[id_source]
    parser = getattr(parsers, parser_name)
    parser_results, parser_id = parser(documentation)
    if not parser_results:
        raise RuntimeError(f'could not parse anything for encounter: {encounter_internal_id}, with parser: {parser_id}')
    _publish_results(encounter_id, parser_id, id_source, parser_results)
    return parser_results
