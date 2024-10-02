import spacy

# Configuration
OUTPUT_FORMAT = 'verified_files/output_'
FILES = [
    'Airport_triples_from_wikipedia.txt',
    'Brain_triples_from_wikipedia.txt',
    'Car_triples_from_wikipedia.txt',
    'Computer_triples_from_wikipedia.txt',
    'Giraffe_triples_from_wikipedia.txt',
    'Islam_triples_from_wikipedia.txt',
    'Planet_triples_from_wikipedia.txt',
    'Polish_language_triples_from_wikipedia.txt',
    'Q68_triples.txt',
    'Q432_triples.txt',
    'Q634_triples.txt',
    'Q809_triples.txt',
    'Q1073_triples.txt',
    'Q1420_triples.txt',
    'Q15083_triples.txt',
    'Q1248784_triples.txt',
]

# Global variables
nlp = spacy.load("en_core_web_trf")
identified_classes = set()

def has_numbers(inputString):
    """
    Check if a string contains any digit.
    :param input_string: String to check
    :return: True if any character is a digit, else False
    """
    return any(char.isdigit() for char in inputString)

def reprocess_aggregation_relations(triples):
    """
    Reprocess aggregation relations in triples to detect reverse compositions.
    :param triples: List of triples to check
    :return: Updated list of triples with corrected relation types
    """
    final_triples = []
    for triple in triples:
        sub, rel, obj, rel_t, sub_t, obj_t = triple 
        if rel_t == 'aggregation':
            if any(sub == obj_rev and obj == sub_rev \
            for (sub_rev, _, obj_rev,_,_,_) in triples):
                triple = (sub, rel, obj, 'composition', sub_t, obj_t)
        final_triples.append(triple)
    return final_triples

def process_triples_file(filename):
    """
    Process the triples file by filtering and extracting triples, identifying 
    class-object distinctions, and assigning relation types.
    :param filename: The path to the input file with triples.
    :return: A list of processed triples with classification and relation type.
    """
    processed_triples = []
    
    with open(filename, 'r', encoding='utf-8') as f:
        lines = f.readlines()
        for line in lines:
            line = line.replace('\\xa0', ' ').lower()

            if any(term in line for term in 
                   ['list of', 'wikidata property', 'wikidata qualifier']) \
               or has_numbers(line):
                continue

            line = line[2:-3]
            triples = line.split(", ")
            if len(triples) != 3:
                continue

            sub = triples[0][:-1].replace('"',"'")
            rel = triples[1][1:-1]
            obj = triples[2][1:].replace('"',"'")

            doc_subject = nlp(sub)
            doc_object = nlp(obj)

            subject_is_entity = any(ent.label_ in ['ORG', 'GPE']
                                    for ent in doc_subject.ents)
            obj_is_entity = any(ent.label_ in ['ORG', 'GPE']
                                   for ent in doc_object.ents)

            obj_t = 'object' if obj_is_entity else 'class'
            sub_t = 'object' if subject_is_entity else 'class'

            if rel in ['is a', 'instance of', 'part of'] and not obj_is_entity:
                obj_t = 'class'
                identified_classes.add(obj)
            if rel in ['subclass of']:
                obj_t = 'class'
                identified_classes.add(obj)
                sub_t = 'class'
                identified_classes.add(sub)
            if rel in ['properties for this type', 'has characteristic', 
                       'has properties']:
                obj_t = 'attribute name' 
            
            if rel in ('made from material', 'made up of',):
                rel_t = 'composition'
            elif rel in ('have', 'include','part of', 'has parts', 
                         'made of', 'is composed of', 'consist of'):
                rel_t = 'aggregation'
            elif rel in ('is a', 'instance of', 'subclass of'):
                rel_t = 'inheritance'
            elif rel in ('properties for this type', 'has characteristic', 
                         'has properties'):
                rel_t = 'attributes'
            else:
                rel_t = 'association'
            
            rel_t = 'composition' if rel in ['made from material', 
                                            'made up of'] else \
                    'aggregation' if rel in ['have', 'is composed of', 
                                            'part of', 'has parts', 
                                            'made of', 'include', 
                                            'consist of'] else \
                    'inheritance' if rel in ['is a', 'instance of', 
                                            'subclass of'] else \
                    'attributes' if rel in ['properties for this type', 
                                            'has characteristic', 
                                            'has properties'] else \
                    'association'

            processed_triples.append((sub, rel, obj, rel_t, sub_t, obj_t))

    processed_triples = reprocess_aggregation_relations(processed_triples)

    return processed_triples

def write_processed_triples(triples, output_filename):
    """
    Write the processed triples into a new file with subjects, relation
    and object types.
    :param triples: List of processed triples.
    :param output_filename: Path to the output file.
    """
    with open(output_filename, 'w', encoding='utf-8') as f:
        for triple in triples:
            sub, rel, obj, rel_t, sub_t, obj_t = triple
            if obj in identified_classes:
                obj_t = 'class'
            if sub in identified_classes:
                sub_t = 'class'
            f.write(f"'{sub}' ({sub_t}), '{rel}', '{obj}' ({obj_t}) : {rel_t}\n")

for file in FILES:
    """
    Process each file in the FILES list, transform triples, and save the output 
    to a corresponding output file.
    """
    input_filename = file
    output_filename = OUTPUT_FORMAT + file

    processed_triples = process_triples_file(input_filename)
    write_processed_triples(processed_triples, output_filename)
