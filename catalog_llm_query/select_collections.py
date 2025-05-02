import openai
import ast


def create_prompt(input_text, categories):
    category_list = '\n'.join([f'- {cat}' for cat in categories])
    return f"""
    Please categorize the following input into one or more of the predefined categories. Only return the category names and return the answer in json format. for example: {{"category_names": ["category1", "category2"]}}.

    Input: {input_text}

    Categories:
    {category_list}

    Here is the examples you can learn from:
    ###
    input: what diseases are associated with gene PAH?
    answer: ["genes", "diseases_genes"]
    ###
    input: Tell me about gene PAH?
    answer: ["genes"]
    ###
    input: The variant with SPDI of NC_000001.11:981168:A:G affects the expression of several genes. What are the genes that are affected?
    answer: ["genes", 'variants_genes', 'variants]
    ###
    input: Can you tell me the variant with SPDI of NC_000012.12:102855312:C:T is associated with what diseases?
    answer: ["variants", "variants_diseases", "ontology_terms"]
    ###
    input: What does NEK5 interact with?
    answer: ["proteins", "proteins_proteins"]
    ###


    """


def select_collections(query, collection_names):
    RESPONSE_FORMAT = {'type': 'json_object'}

    content = create_prompt(query, collection_names)
    response = openai.chat.completions.create(
        response_format=RESPONSE_FORMAT,
        model='gpt-4o',
        temperature=0,
        messages=[
            {'role': 'user', 'content': content},
        ]
    )
    output = response.choices[0].message.content
    try:
        json_obj = ast.literal_eval(output)
        return json_obj['category_names']
    except:
        return output
