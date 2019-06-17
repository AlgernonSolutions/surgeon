from algernon.aws.gql import GqlNotary
from algernon import ajson

from toll_booth.obj.gql import gql_queries


def _standardize_gql_endpoint(gql_endpoint: str):
    variable_fields = ('https://', 'http://', '/graphql')
    for field_name in variable_fields:
        gql_endpoint = gql_endpoint.replace(field_name, '')
    return gql_endpoint


class GqlClient:
    def __init__(self, gql_connection: GqlNotary):
        self._gql_connection = gql_connection

    @classmethod
    def from_gql_endpoint(cls, gql_endpoint: str):
        gql_endpoint = _standardize_gql_endpoint(gql_endpoint)
        gql_connection = GqlNotary(gql_endpoint)
        return cls(gql_connection)

    def _send(self, query, variables=None):
        if not variables:
            variables = {}
        response = self._gql_connection.send(query, variables)
        return ajson.loads(response)

    def get_documentation(self, identifier_stem, encounter_type):
        results = {}
        query_results, token = self.paginate_documentation(identifier_stem, encounter_type)
        results.update(query_results)
        while token:
            query_results, token = self.paginate_documentation(identifier_stem, encounter_type, token)
            results.update(query_results)
        return results

    def paginate_documentation(self, identifier_stem, encounter_type, token=None):
        results = {}
        variables = {
            'encounter_identifier_stem': identifier_stem,
            'object_type': 'Encounter',
            'object_properties': [
                {
                    'property_name': 'encounter_type',
                    'data_type': 'S',
                    'property_value': encounter_type
                }
            ]
        }
        if token:
            variables['token'] = token
        response = self._send(gql_queries.GET_COMMUNITY_SUPPORT_DOCUMENTATION, variables)
        fn_response = response['data']['list_vertexes']
        for vertex in fn_response['vertexes']:
            vertex_properties = {}
            encounter_internal_id = vertex['internal_id']
            for vertex_property in vertex['vertex_properties']:
                property_name = vertex_property['property_name']
                if property_name in ['documentation', 'id_source', 'encounter_type']:
                    vertex_properties[property_name] = vertex_property['property_value']
            results[encounter_internal_id] = vertex_properties
        return results, fn_response.get('token')

    def get_client_documentation_properties(self, internal_id):
        results = {}
        query_results, token = self._paginate_client_documentation(internal_id)
        results.update(query_results)
        while token:
            query_results, token = self._paginate_client_documentation(internal_id, token)
            results.update(query_results)
        return results

    def _paginate_client_documentation(self, internal_id, token=None):
        results = {}
        variables = {'internal_id': internal_id}
        if token:
            variables['token'] = token
        response = self._send(gql_queries.GET_CLIENT_DOCUMENTATION, variables)
        connected_edges = response['data']['vertex']['connected_edges']
        page_info = connected_edges['page_info']
        edges = connected_edges.get('edges', {})
        for entry in edges.get('inbound', []):
            vertex_properties = {}
            vertex = entry['from_vertex']
            encounter_internal_id = vertex['internal_id']
            for vertex_property in vertex['vertex_properties']:
                property_name = vertex_property['property_name']
                if property_name in ['documentation', 'id_source', 'encounter_type']:
                    vertex_properties[property_name] = vertex_property['property_value']
            results[encounter_internal_id] = vertex_properties
        if page_info.get('more'):
            return results, page_info.get('token')
        return results, None

    def get_documentation_property(self, internal_id: str):
        results = {}
        response = self._send(gql_queries.GET_DOCUMENTATION, {'internal_id': internal_id})
        vertex_properties = response['data']['vertex']['vertex_properties']
        for entry in vertex_properties:
            property_name = entry['property_name']
            results[property_name] = entry['property_value']
        return results
