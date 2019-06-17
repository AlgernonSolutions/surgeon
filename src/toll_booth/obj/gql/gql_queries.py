GET_DOCUMENTATION = '''
    query getDocumentation($internal_id: ID!){
        vertex(internal_id: $internal_id){
            vertex_properties(property_names: ["documentation", "id_source", "encounter_type", "encounter_id"]){
                property_name
                property_value{
                    ... on StoredPropertyValue{
                        storage_class
                        storage_uri
                        stored_data_type: data_type
                    }
                    ... on LocalPropertyValue{
                        property_value
                        local_data_type: data_type
                    }
                }
            }
        }
    }
'''

GET_CLIENT_DOCUMENTATION = '''
    query getDocumentation($internal_id: ID!, $token: ID){
        vertex(internal_id: $internal_id){
            connected_edges(edge_labels:["_received_"], token: $token){
                page_info{
                    more
                    token
                }
                edges{
                    inbound{
                        edge_label
                        from_vertex{
                            internal_id
                            vertex_properties(property_names: ["documentation", "id_source", "encounter_type"]){
                                property_name
                                property_value{
                                    ... on StoredPropertyValue{
                                        storage_class
                                        storage_uri
                                        stored_data_type: data_type
                                    }
                                    ... on LocalPropertyValue{
                                        property_value
                                        local_data_type: data_type
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
    }
'''


GET_COMMUNITY_SUPPORT_DOCUMENTATION = """
query get_comm_supt($encounter_identifier_stem: String!, $object_type: String!, $object_properties: [InputLocalProperty]!, $token: ID){
  list_vertexes(identifier_stem: $encounter_identifier_stem, object_type: $object_type, object_properties: $object_properties, token: $token){
    token
    vertexes{
      internal_id
      vertex_properties(property_names: ["documentation", "id_source", "encounter_type", "encounter_id"]){
            property_name
            property_value{
                ... on StoredPropertyValue{
                    storage_class
                    storage_uri
                    stored_data_type: data_type
                }
                ... on LocalPropertyValue{
                    property_value
                    local_data_type: data_type
                }
            }
        }
    }
  }
}
"""
