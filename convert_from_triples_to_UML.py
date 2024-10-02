# CONSTANTS
RELATIONS_DICT = {
    'association': '-->',
    'inheritance': '<|--',
    'composition': '*--',
    'aggregation': 'o--'
}

def read_file(filename):
    """
    Reads triples and attributes from a specified file.

    :param filename: The name of the file to read.
    :return: A tuple containing a list of triples and a dictionary of attributes.
    """
    triples = []
    attributes = {}

    with open(filename, 'r', encoding='utf-8') as f:
        lines = f.readlines()
        for line in lines:
            splitted_line = line.split(", ")
            if len(splitted_line) == 3:
                subject = splitted_line[0].split(" (")[0][1:-1]
                subject_type = splitted_line[0].split(" (")[1][:-1]

                subject_2 = splitted_line[2].split(" (")[0][1:-1]
                subject_2_type = splitted_line[2].split(" (")[1].split(')')[0]

                relation = splitted_line[2].split(" : ")[1][0:-1]
                relation_name = splitted_line[1][1:-1]
            else:
                continue

            if subject_type == 'object' or subject_2_type == 'object':
                continue

            if ('has characteristic' in line or 
                'properties for this type' in line or 
                'has properties' in line) and relation == 'attributes':
                if subject in attributes:
                    attributes[subject].append(subject_2)
                else:
                    attributes[subject] = [subject_2]
                continue
            # else treat as class relation class
            triples.append((subject, relation_name, relation, subject_2))
    return triples, attributes


def write_classes_to_file(classes, filename):
    """
    Writes class definitions with their attributes to a specified file.

    :param classes: A dictionary of classes and their associated attributes.
    :param filename: The name of the file to write to.
    """
    with open(filename, 'a', encoding='utf-8') as f:
        for single_class, attributes in classes.items():
            f.write(f'class "{single_class}" {{\n')            
            for attr in attributes:
                f.write(f'  +"{attr}" : String\n')
            f.write("}\n")


def write_relations_to_file(triples, filename):
    """
    Writes relationships between classes to a specified file.

    :param triples: A list of triples representing relationships.
    :param filename: The name of the file to write to.
    """
    with open(filename, 'a', encoding='utf-8') as f:
        f.write("\n")
        for triple in triples:
            f.write(f'"{triple[0]}" {RELATIONS_DICT[triple[2]]} "{triple[3]}" : {triple[1]}\n')


def write_file(classes, relations, filename):
    """
    Writes the complete UML representation to a specified file.

    :param classes: A dictionary of classes and their attributes.
    :param relations: A list of relations between classes.
    :param filename: The name of the file to write to.
    """
    with open(filename, 'w', encoding='utf-8') as f:
        starting_text = '@startuml '+filename+'\n'
        f.write(starting_text)
        f.write('hide empty methods\n')
    write_classes_to_file(classes, filename)
    write_relations_to_file(relations, filename)
    with open(filename, 'a', encoding='utf-8') as f:
        f.write('@endtuml')

# Example usage
filename = 'verified_files/output_Polish_language_triples_from_wikipedia.txt'
relations, classes = read_file(filename)
write_file(classes, relations, filename.split('/')[1] + '_output_test.iuml')
