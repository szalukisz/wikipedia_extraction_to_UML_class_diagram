import requests

# CONSTANTS
API_ENDPOINT = "https://www.wikidata.org/w/api.php"
PARAMS = {
    'action': 'wbgetentities',
    'format': 'json',
    'languages': 'en'
}

RELATION_PROPERTIES = [
    ('P527','has parts'),                      # aggregation/composition
    ('P361', 'part of'),                       # aggregation/composition
    ('P186', 'made from material'),            # composition   
    ('P1963', 'properties for this type'),     # attributes
    ('P1552', 'has characteristic'),           # attributes
    ('P279', 'subclass of'),                   # is_a
    ('P31', 'instance of'),                    # is_a
    ('P2283', 'uses'),                         # association
    ('P2789', 'connects with')                 # association
]

# Configuration
ENTITIES_TO_TEST = [
    'Q809',     # Polish language
    'Q68',      # computer
    'Q1248784', # airport
    'Q432',     # islam
    'Q1420',    # motor car
    'Q15083',   # giraffe
    'Q1073',    # brain
    'Q634',     # planet
    ]

MAX_LEVEL_DEEP = 0

# Global variables
triples_global = []
visited_entities = set()
entity_name_cache = {}
session = requests.Session()

def recursive_find(data, match):
    """
    Recursively searches for a key in nested dictionary and returns its value.

    :param data: The dictionary to search through.
    :param match: The key to search for.
    :return: The value associated with the key.
    """
    for k,v in data.items():
        if k == match:
            return v
        elif isinstance(v, dict):
            return recursive_find(v, match)

def convert_id_to_name(entity_id):
    """
    Converts an entity ID to its corresponding name using the Wikidata API.

    :param entity_id: The ID of the entity to convert.
    :return: The name of the entity.
    """
    if entity_id in entity_name_cache:
        return entity_name_cache[entity_id]
    
    parameters = PARAMS
    parameters['props'] = 'labels'
    parameters['ids'] =  entity_id

    response = session.get(url=API_ENDPOINT, params=parameters)
    name = recursive_find(response.json(), 'value')

    if name:
        entity_name_cache[entity_id] = name
    return name


def get_entities_of_property(claims, property_id, parent):
    """
    Retrieves entities associated with a given property from the claims.

    :param claims: The claims data for the entity.
    :param property_id: The property ID to search for.
    :param parent: The ID of the parent entity to avoid recursion.
    :return: A list of tuples containing entity IDs and their labels.
    """
    if property_id in claims:
        items = claims[property_id]
        table_of_entities = []

        for item in items:
            try:
                sub_entity_id = item['mainsnak']['datavalue']['value']['id']
            except:
                continue

            if sub_entity_id == parent:
                continue

            label = convert_id_to_name(sub_entity_id)
            if label is not None:
                table_of_entities.append((sub_entity_id, label))

        return table_of_entities
    else:
        return []


def search_structure_from_top(entity_id, level, parent=''):
    """
    Recursively searches the structure of an entity and extracts relations.

    :param entity_id: The ID of the entity to search.
    :param level: Current depth level in the recursion.
    :param parent: ID of the parent entity to avoid cycles.
    """
    parameters = PARAMS
    parameters['props'] = 'claims'
    parameters['ids'] =  entity_id
    
    result = session.get(url= API_ENDPOINT, params=parameters)
    claims = result.json()['entities'][entity_id]['claims']
    name = convert_id_to_name(entity_id)

    for property_id, relation_label in RELATION_PROPERTIES:
        tbl_of_entities = get_entities_of_property(claims, property_id, parent)
        for item in tbl_of_entities:
            triples_global.append((name, relation_label, item[1]))

            if level < MAX_LEVEL_DEEP and item[1] not in visited_entities:
                visited_entities.add(item[1])
                search_structure_from_top(item[0], level+1, entity_id)


for entity_id in ENTITIES_TO_TEST:
    triples_global.clear()
    visited_entities.clear()
    
    print("Tested entity: " + entity_id)
    search_structure_from_top(entity_id, 0)
    print("Found triples: " + str(len(triples_global)))

    triples = sorted(triples_global, key=lambda x: (x[0], x[1]))
    lines = [str(i) + '\n' for i in triples]
    with open(entity_id + '_triples.txt', 'w', encoding='utf-8') as f:
        f.writelines(lines)