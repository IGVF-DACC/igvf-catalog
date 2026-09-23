from schemas.registry import merge_allof_schema


def test_base_mixin_descriptions_survive_child_overrides():
    schema = {
        'allOf': [
            {'allOf': [
                {'properties': {'source': {'description': 'Data source'}}},
                {'properties': {'source': {'type': 'string'}},
                 'required': ['source']},
            ]},
            {'properties': {'source': {'enum': ['IGVF']}},
             'required': ['source']},
        ]
    }
    resolved = merge_allof_schema(schema)
    assert resolved['properties']['source'] == {
        'description': 'Data source', 'type': 'string', 'enum': ['IGVF']
    }
    assert resolved['required'] == ['source']
