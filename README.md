# Wikipedia Data Extraction Scripts

This repository contains a collection of Python scripts designed for extracting structured data from Wikipedia articles and Wikidata portal. The primary goal is to gather triples that represent relationships and properties related to various entities found on Wikipedia pages, including their infoboxes. Additionally, the scripts aim to generate UML diagrams using PlantUML, providing a visual representation of the extracted relationships.

## Table of Contents

- [Requirements](#requirements)
- [Script Descriptions](#script-descriptions)
  - [wikipedia_words_test.py](#wikipedia_words_testpy)
  - [wikipedia_triples_extract.py](#wikipedia_triples_extractpy)
  - [wikidata_triples_extract.py](#wikidata_triples_extractpy)
  - [triples_parse_and_verify.py](#triples_parse_and_verifypy)
  - [find_common_wikipedia_wikidata.py](#find_common_wikipedia_wikidatapy)
  - [convert_from_triples_to_UML.py](#convert_from_triples_to_umlpy)

## Requirements

- Python 3.x
- `requests`
- `beautifulsoup4`
- `spacy`
- `re`
- `time`

You can install the required packages using pip, example:

```bash
pip install requests beautifulsoup4 spacy
python -m spacy download en_core_web_trf
```

## Script Descriptions

### wikipedia_words_test.py

#### Purpose:
This script explores Wikipedia articles to extract and count words surrounding hyperlinks. It recursively follows internal article links up to a specified depth and generates a histogram of word frequencies, which is saved as a JSON file.

#### Key Features:
- **Recursive Article Exploration**: Follows links in Wikipedia articles up to a set depth.
- **Word Extraction**: Identifies and counts words around hyperlinks in the HTML content.
- **Histogram Generation**: Records the frequency of words and saves the result as `global_test.json`.
- **Link Tracking**: Ensures each article is processed only once.

#### Configuration:
- `DEPTH_LEVEL`: Defines how deep the recursion goes (default is 2).
- `TESTED_LINKS`: A list of starting Wikipedia articles (e.g., Polish language, Computer, Airport).

#### Output:
A word frequency histogram is saved in `global_test.json`.

### wikipedia_triples_extract.py

#### Purpose:
This script extracts subject-predicate-object triples (relations) from Wikipedia articles by analyzing content in paragraphs and infoboxes. It follows links within articles up to a specified depth and outputs the relations as triples.

#### Key Features:
- **Recursive Article Exploration**: Extracts triples from the first paragraph and infobox of an article, and recursively follows links up to a specified depth.
- **Triple Extraction**: Identifies subject-predicate-object triples using predefined phrases like "is a", "consists of", and others.
- **Infobox Processing**: Extracts properties from infoboxes as triples.
- **Link Handling**: Processes links within the article and follows them recursively for further exploration.

#### Configuration:
- `max_depth_level`: Controls the depth of recursive exploration (default is 2).
- `max_sentences_from_paragraph`: Limits the number of sentences analyzed from each paragraph.

#### Output:
Extracted triples are saved in files named as `<article_name>_triples_from_wikipedia.txt`, sorted in order.

### wikidata_triples_extract.py

#### Purpose:
This script extracts subject-predicate-object triples (relations) from Wikidata entities using the Wikidata API. It retrieves entity relationships such as "has parts", "subclass of", "uses", and others, recursively exploring up to a defined depth level.

#### Key Features:
- **Entity Exploration**: Extracts triples from Wikidata entities by querying their properties (e.g., "subclass of", "uses").
- **Recursive Relation Extraction**: Recursively explores relationships between entities, avoiding cycles.
- **Entity Name Conversion**: Converts entity IDs to human-readable names via the Wikidata API.
- **Triple Output**: Saves the extracted triples in a sorted format for each entity.
  
#### Configuration:
- `MAX_LEVEL_DEEP`: Controls the depth level of recursive relation extraction (default is 0).
- `ENTITIES_TO_TEST`: List of Wikidata entities (e.g., Polish language, computer) for which relations are extracted.
  
#### Output:
Extracted triples are saved in files named `<entity_id>_triples.txt`, sorted by subject and relation.

### triples_parse_and_verify.py

#### Purpose:
This script processes triples extracted from various sources (Wikipedia, Wikidata), filters and classifies the relations and entities, and reassigns relation types (e.g., inheritance, aggregation, composition). It identifies whether subjects and objects are classes, objects, or attributes and saves the processed triples in a readable format.

#### Key Features:
- **Triple Processing**: Parses raw triples from input files and assigns entity and relation types.
- **Entity Classification**: Identifies whether a subject or object is a class, object, or attribute.
- **Relation Type Assignment**: Assigns a relation type (e.g., aggregation, inheritance, composition) based on the extracted relation.
- **Aggregation Reprocessing**: Detects reverse composition relationships and adjusts relation types accordingly.
- **Output Writing**: Saves the processed triples in an output file for further analysis.

#### Configuration:
- `OUTPUT_FORMAT`: Prefix for the output file paths.
- `FILES`: List of input files containing triples extracted from Wikipedia and Wikidata.

#### Output:
Processed triples are saved in files prefixed with `verified_files/output_` and include the relation type and whether each subject/object is classified as a class or object.

### find_common_wikipedia_wikidata.py

#### Purpose:
This script compares extracted triples from Wikipedia and Wikidata to identify and save common relationships between entities. It reads triples from specified input files, checks for overlaps, and outputs the common triples to new files.

#### Key Features:
- **Triple Reading**: Reads triples from both Wikipedia and Wikidata files and converts them into structured tuples.
- **Common Triple Comparison**: Compares the extracted triples from both sources to find commonalities.
- **Output of Common Triples**: Saves the common triples in a new file for each pair of input files.

#### Configuration:
- `FILES`: A list of tuples, each containing the filenames for the Wikipedia and Wikidata triples to be compared.
- `FOLDER`: The directory where the input files are located.

#### Output:
The script generates output files named based on the subject entity, containing the common triples found between the two sources, formatted for easy readability.

### convert_from_triples_to_UML.py

#### Purpose:
This script converts extracted triples and their associated attributes into a UML representation. It processes input files containing triples, structures the data into classes and relationships, and generates a PlantUML file for visualization.

#### Key Features:
- **Triple and Attribute Reading**: Reads triples and their corresponding attributes from a specified input file.
- **Class Definition Writing**: Generates class definitions with attributes for the UML diagram.
- **Relationship Writing**: Defines and writes relationships between classes based on the extracted triples.
- **UML File Generation**: Combines class and relationship data into a formatted PlantUML output file.

#### Configuration:
- `RELATIONS_DICT`: A dictionary mapping relation types to UML symbols.
- `filename`: The input file containing extracted triples for processing.

#### Output:
The generated UML output file is saved with a naming convention based on the input file, allowing for easy identification and further analysis of the relationships and classes extracted from the triples.
