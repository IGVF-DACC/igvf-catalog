from schemas.registry import expand_ref_siblings, merge_allof_schema


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


def test_expand_ref_siblings_wraps_keywords_beside_ref():
    schema = {
        'properties': {
            'source': {
                '$ref': '../mixins.json#/source',
                'enum': ['GenCC'],
                'example': 'GenCC',
            }
        }
    }
    assert expand_ref_siblings(schema) == {
        'properties': {
            'source': {
                'allOf': [
                    {'$ref': '../mixins.json#/source'},
                    {'enum': ['GenCC'], 'example': 'GenCC'},
                ]
            }
        }
    }


def test_property_level_allof_from_ref_siblings_flattens():
    # After expand_ref_siblings + jsonref, a joined mixin looks like this.
    schema = {
        'properties': {
            'source': {
                'allOf': [
                    {
                        'description': 'Data source',
                        'type': 'string',
                        'example': 'IGVF',
                    },
                    {
                        'enum': ['GenCC'],
                        'example': 'GenCC',
                    },
                ]
            }
        }
    }
    resolved = merge_allof_schema(schema)
    assert resolved['properties']['source'] == {
        'description': 'Data source',
        'type': 'string',
        'enum': ['GenCC'],
        'example': 'GenCC',
    }
