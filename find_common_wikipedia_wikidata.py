FILES = [
    ('output_Airport_triples_from_wikipedia.txt','output_Q1248784_triples.txt'),
    ('output_Brain_triples_from_wikipedia.txt','output_Q1073_triples.txt'),
    ('output_Car_triples_from_wikipedia.txt','output_Q1420_triples.txt'),
    ('output_Islam_triples_from_wikipedia.txt','output_Q432_triples.txt'),
    ('output_Computer_triples_from_wikipedia.txt','output_Q68_triples.txt'),
    ('output_Planet_triples_from_wikipedia.txt','output_Q634_triples.txt'),
    ('output_Giraffe_triples_from_wikipedia.txt','output_Q15083_triples.txt'),
    ('output_Polish_language_triples_from_wikipedia.txt','output_Q809_triples.txt'),
]
FOLDER = 'verified_files/'

def read_triples(filename):
    """
    Reads triples from a given file and returns them as a list of tuples.
    
    :param filename: The name of the file to read the triples from.
    :return: A list of tuples representing triples (subject, relation, object).
    """
    triples = []
    with open(filename, 'r', encoding='utf-8') as f:
        lines = f.readlines()
        for line in lines:
            line = line.lower().split(", ")
            if len(line) == 3:
                subject = line[0].split(" (")[0][1:-1]
                subject_2 = line[2].split(" (")[0][1:-1]
                relation = line[2].split(" : ")[1][0:-1]
                triples.append((subject, relation, subject_2))
    return triples

def compare_triples(triples_wikipedia, triples_wikidata):
    """
    Compares two lists of triples and returns common triples.

    :param triples_wikipedia: A list of triples from Wikipedia.
    :param triples_wikidata: A list of triples from Wikidata.
    :return: A list of common triples found in both input lists.
    """
    common_triples = []
    for wiki_triple in triples_wikipedia:
        if wiki_triple in triples_wikidata:
            common_triples.append(wiki_triple)
    return common_triples

def save_common_triples(common_triples, output_filename):
    """
    Saves common triples to a specified output file.

    :param common_triples: A list of common triples to save.
    :param output_filename: The name of the file to save the triples to.
    """
    with open(output_filename, 'w', encoding='utf-8') as f:
        for triple in common_triples:
            f.write(f"'{triple[0]}'  '{triple[1]}', '{triple[2]}' \n")

for file1, file2 in FILES:
    triples_wikipedia = read_triples(FOLDER+file1)
    triples_wikidata = read_triples(FOLDER+file2)

    common_triples = compare_triples(triples_wikipedia, triples_wikidata)

    save_common_triples(common_triples, file1.split('_')[1]+'_common_triples.txt')

    print(f"Found {len(common_triples)} common triples for {file1.split('_')[1]}.")