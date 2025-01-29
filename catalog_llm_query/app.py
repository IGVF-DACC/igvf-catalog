from flask import Flask, request, jsonify
import json
from arango import ArangoClient
from langchain_community.graphs import ArangoGraph
from langchain.chains import ArangoGraphQAChain
from langchain_openai import ChatOpenAI
import os
from select_collections import select_collections
from langchain_community.callbacks import get_openai_callback


# Initialize Flask app
app = Flask(__name__)


def get_config():
    with open('config/development.json') as f:
        config = json.load(f)
    return config


def initialize_arango_graph(config):
    # Configuration for ArangoDB
    connection_uri = config['connectionUri']
    dbName = config['dbName']
    username = config['auth']['username']
    password = config['auth']['password']

    # Connect to ArangoDB and initialize graph
    client = ArangoClient(hosts=connection_uri)
    db = client.db(dbName, username=username, password=password)

    # Initialize ArangoGraph
    graph = ArangoGraph(db)
    return graph


def initialize_collection_names(collection_schema):
    collection_names = [collection['collection_name']
                        for collection in collection_schema]
    return collection_names


def initialize_llm(config):
    api_key = config['openai_api_key']
    os.environ['OPENAI_API_KEY'] = api_key
    model = ChatOpenAI(temperature=0, model_name='gpt-4o')
    return model


def ask_llm(qeustion):
    selected_collection_names = select_collections(qeustion, collection_names)
    print('collection to use for query:', selected_collection_names)

    updated_graph = get_updated_graph(
        graph, collection_schema, selected_collection_names)
    chain = ArangoGraphQAChain.from_llm(
        model, graph=updated_graph, verbose=True, allow_dangerous_requests=True)
    # Set the maximum number of AQL Query Results to return to 5
    # This avoids burning the LLM token limit on JSON results
    chain.top_k = 5
    # Specify the maximum amount of AQL Generation attempts that should be made
    # before returning an error
    chain.max_aql_generation_attempts = 5

    # Specify whether or not to return the AQL Query in the output dictionary
    # Use `chain("...")` instead of `chain.invoke("...")` to see this change
    chain.return_aql_query = True

    # Specify whether or not to return the AQL JSON Result in the output dictionary
    # Use `chain("...")` instead of `chain.invoke("...")` to see this change
    chain.return_aql_result = True
    # The AQL Examples modifier instructs the LLM to adapt its AQL-completion style
    # to the user’s examples. These examples arepassed to the AQL Generation Prompt
    # Template to promote few-shot-learning.

    chain.aql_examples = """
    # show me all the vairants that is in chromosome 1, position at 10000000?
    WITH variants
    FOR v IN variants
    FILTER v.chr == "chr1" AND v.pos == 10000000
    RETURN v

    # Can you tell me the variant with SPDI of NC_000012.12:102855312:C:T is associated with what diseases?
    WITH variants, variants_diseases, ontology_terms
    FOR variant IN variants
    FILTER variant.spdi == 'NC_000012.12:102855312:C:T'
    FOR disease IN OUTBOUND variant variants_diseases
    RETURN disease

    # Show me all variants associated with cardiomyopathy
    FOR v in variants
    FILTER v._id IN (
        FOR d IN variants_diseases
        FILTER d._to IN (
        FOR o in ontology_terms
        FILTER o.name == 'cardiomyopathy'
        RETURN o._id
        )
    RETURN d._from)
    RETURN v

    # What are the transcripts from the protein PARI_HUMAN?
    FOR p IN proteins
        FILTER p.name == 'PARI_HUMAN'
        FOR t IN transcripts_proteins
            FILTER t._to == p._id
            RETURN t
    """

    with get_openai_callback() as cb:
        response = chain.invoke(qeustion)
        print(cb)
    return response


config = get_config()
graph = initialize_arango_graph(config['database'])
collection_schema = graph.schema['Collection Schema']
collection_names = initialize_collection_names(collection_schema)
model = initialize_llm(config)


def get_updated_graph(graph, collection_schema, selected_collection_names):
    collection_schema_updated = []
    for collection_name in selected_collection_names:
        for collection in collection_schema:
            if collection['collection_name'] == collection_name:
                collection_schema_updated.append(collection)
                break
    updated_graph = graph
    updated_graph.schema['Collection Schema'] = collection_schema_updated
    return updated_graph

# Create Flask endpoint


@app.route('/query', methods=['GET'])
def query():
    # Get the query from the request arguments
    user_query = request.args.get('query')
    if not user_query:
        return jsonify({'error': 'Query parameter is required'}), 400

    try:
        response = ask_llm(user_query)
        return jsonify({'response': response})

    except Exception as e:
        error = {
            'query': user_query,
            'error': str(e)
        }
        return jsonify(error), 500


# Run the Flask app
if __name__ == '__main__':
    app.run(debug=True)
