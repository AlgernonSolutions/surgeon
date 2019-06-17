import os

from toll_booth.obj.gql.gql_client import GqlClient
from toll_booth.obj.incredible.html_parser import CredibleFormParser
from toll_booth.tasks import aws_tasks


def parse_documentation(internal_id):
    gql_endpoint = os.environ['GQL_ENDPOINT']
    gql_client = GqlClient.from_gql_endpoint(gql_endpoint)
    encounter_properties = gql_client.get_documentation_property(internal_id)
    documentation_property = encounter_properties.get('documentation')
    id_source_property = encounter_properties.get('id_source')
    encounter_type_property = encounter_properties.get('encounter_type')
    id_source = id_source_property['property_value']
    encounter_type = encounter_type_property['property_value']
    storage_uri = documentation_property['storage_uri']
    documentation = aws_tasks.retrieve_s3_property(storage_uri)
    parser = CredibleFormParser(id_source)
    parsed_entries = parser.parse(encounter_type, documentation)
    return parsed_entries


def work_client_documentation(internal_id):
    client_documentation = {}
    gql_endpoint = os.environ['GQL_ENDPOINT']
    gql_client = GqlClient.from_gql_endpoint(gql_endpoint)
    client_encounter_properties = gql_client.get_client_documentation_properties(internal_id)
    for encounter_internal_id, encounter_properties in client_encounter_properties.items():
        if not encounter_properties:
            print(f'client internal_id: {internal_id} '
                  f'has an empty vertex for encounter_internal_id: {encounter_internal_id}')
            continue
        documentation_property = encounter_properties.get('documentation')
        id_source_property = encounter_properties.get('id_source')
        encounter_type_property = encounter_properties.get('encounter_type')
        id_source = id_source_property['property_value']
        encounter_type = encounter_type_property['property_value']
        storage_uri = documentation_property['storage_uri']
        documentation = aws_tasks.retrieve_s3_property(storage_uri)
        parser = CredibleFormParser('DCDBH')
        parsed_entries, form_id, version_id = parser.parse(encounter_type, documentation)
        key = f'{form_id}.{version_id}'
        if key not in client_documentation:
            client_documentation[key] = {}
        client_documentation[key][encounter_internal_id] = parsed_entries
    return client_documentation


def work_comm_supt_documentation(identifier_stem, encounter_type):
    results = {}
    gql_endpoint = os.environ['GQL_ENDPOINT']
    gql_client = GqlClient.from_gql_endpoint(gql_endpoint)
    comm_supt_documentation, token = gql_client.paginate_documentation(identifier_stem, encounter_type)
    results.update(_process_documentation_batch(comm_supt_documentation))
    while token:
        comm_supt_documentation, token = gql_client.paginate_documentation(identifier_stem, encounter_type, token)
        results.update(_process_documentation_batch(comm_supt_documentation))
    return results


def _process_documentation_batch(comm_supt_documentation):
    processed = {}
    for encounter_internal_id, encounter_properties in comm_supt_documentation.items():
        key, parsed_entries = _process_documentation(encounter_properties)
        if key not in processed:
            processed[key] = {}
        processed[key][encounter_internal_id] = parsed_entries
    return processed


def _process_documentation(encounter_properties):
    documentation_property = encounter_properties.get('documentation')
    id_source_property = encounter_properties.get('id_source')
    encounter_type_property = encounter_properties.get('encounter_type')
    id_source = id_source_property['property_value']
    encounter_type = encounter_type_property['property_value']
    storage_uri = documentation_property['storage_uri']
    documentation = aws_tasks.retrieve_s3_property(storage_uri)
    parser = CredibleFormParser('DCDBH')
    parsed_entries, form_id, version_id = parser.parse(encounter_type, documentation)
    key = f'{form_id}.{version_id}'
    return key, parsed_entries
