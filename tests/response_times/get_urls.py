# This script extracts example URLs for GET endpoints from the OpenAPI spec, using parameter values mentioned in the endpoint descriptions.
# This can be used as a parameter for testing response times using response_times.py.

import urllib.request
import urllib.parse
import json
import re

OPENAPI_URL = 'http://api.catalogkg.igvf.org/openapi'
BASE_URL = 'http://api.catalog.igvf.org/api'

VALUE_EXPANSIONS = {
    'Homo': 'Homo sapiens',
    'Mus': 'Mus musculus',
}

DOT_ALLOWED_PARAMS = {'hgvsp', 'hgvs', 'spdi', 'variant_id', 'region'}
SKIP_PARAMS = {'verbose', 'page'}

with urllib.request.urlopen(OPENAPI_URL) as res:
    spec = json.load(res)

for path, methods in spec['paths'].items():
    for method, operation in methods.items():
        if method.lower() != 'get':
            continue

        parameters = operation.get('parameters', [])
        valid_params = [p['name'] for p in parameters]
        required_params = [p['name']
                           for p in parameters if p.get('required', False)]
        description = operation.get('description', '')

        # params marked with trailing * in description: e.g. "spdi* = ..."
        at_least_one_params = re.findall(r'(\w+)\*', description)
        at_least_one_params = [
            p for p in at_least_one_params if p in valid_params]

        extracted: dict[str, str] = {}
        # match both "param* = value" and "param = value"
        for match in re.finditer(r'(\w+)\*?\s*=\s*([^,<\n(]+)', description):
            key, raw_value = match.group(1), match.group(2).strip().rstrip(';')

            if key not in DOT_ALLOWED_PARAMS:
                raw_value = raw_value.split('.')[0].strip()

            value = VALUE_EXPANSIONS.get(raw_value, raw_value)
            if key not in valid_params:
                continue
            if key in SKIP_PARAMS:
                continue

            extracted[key] = value

        for param in parameters:
            name = param['name']
            if name in SKIP_PARAMS:
                continue
            if name not in extracted:
                fallback = (
                    param.get('example') or
                    param.get('schema', {}).get('example') or
                    param.get('schema', {}).get('default')
                )
                if fallback is not None:
                    extracted[name] = str(fallback)

        missing = [r for r in required_params if r not in extracted]
        if missing:
            print(
                f'# SKIP {method.upper()} {path} — missing required params: {missing}')
            continue

        if at_least_one_params and not any(p in extracted for p in at_least_one_params):
            print(
                f'# SKIP {method.upper()} {path} — need at least one of: {at_least_one_params}')
            continue

        required_qs = {k: extracted[k] for k in required_params}
        optional_extracted = {
            k: v for k, v in extracted.items() if k not in required_params}

        if not optional_extracted:
            qs = urllib.parse.urlencode(required_qs)
            print(f'{BASE_URL}{path}?{qs}')
        else:
            for key, value in optional_extracted.items():
                values = [v.strip() for v in re.split(r'\s+or\s+', value)]
                for v in values:
                    params = {**required_qs, key: v}
                    qs = urllib.parse.urlencode(params)
                    print(f'{BASE_URL}{path}?{qs}')
