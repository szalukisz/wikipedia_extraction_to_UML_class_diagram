import requests
import spacy
import time
import re
from bs4 import BeautifulSoup

# Regular expressions for various patterns in the article content
BEFORE_LINK =  re.compile("((?:[a-zA-Z]+ ){1,3})<a")
AFTER_LINK = re.compile("a>((?: [a-zA-Z]+){1,3})")
LINK_A = re.compile("<a[^>]*[^>]*>[^~]*?</a>")
LINK_TEXT = re.compile("<a[^>]*[^>]*>([^~]*?)</a>")
LINK_TITLE = re.compile(' title="([^~]*?)">')
LINK_HREF = re.compile('href=\"(/.*)?\" ')
SPAN = re.compile("<span[^>]*[^>]*>[^~]*?</span>")
SUP = re.compile("<sup[^>]*[^>]*>[^~]*?</sup>")
P_TAG = re.compile("<p>(.*)")
SENTENCE_UNTIL_PERIOD = re.compile(".*?\.[ ]")

INFOBOX_BEGIN_PATTERN = '<table class="infobox"'
INFOBOX_END_PATTERN = '</table>'

HEADER_CONTENT_BEGIN_PATTERN = '<div id="mw-content-text"'
HEADER_CONTENT_END_PATTERN = '<div class="mw-heading mw-heading2'

ARTICLE_TITLE_PATTERN = re.compile('<span class="mw-page-title-main">([^~]*?)</span>')

# Phrases used to match specific relationships in sentences
PHRASES_TO_MATCH = [
    # inheritance
    " is a ", " is an "," is the ",
    " refer to ", " refers to ",

    # aggregations
    " consists of ",
    " include ", " includes ",
    " has a ",  " have a ",
    " is composed of ",
    " made up of ",
    " made of ",
    " is part of ",

    # associations
    " uses ",
]

# Links to be tested
TESTED_LINKS = [
    '/wiki/Polish_language',
    '/wiki/Computer',
    '/wiki/Airport',
    '/wiki/Islam',
    '/wiki/Car',
    '/wiki/Giraffe',
    '/wiki/Brain',
    '/wiki/Planet'
    ]

class WikipediaExtractor:
    """A class to extract triples from Wikipedia articles."""

    URL_BASE = "https://en.wikipedia.org"

    def __init__(self, max_depth_level=1, max_sentences_from_paragraph=7):
        """
        Initialize the WikipediaExtractor with parameters for depth level 
        and number of sentences to process.

        :param max_depth_level: Maximum depth level for recursion.
        :param max_sentences_from_paragraph: Maximum number of sentences 
                                              to extract from each paragraph.
        """
        self.triples = set()
        self.visited_articles = set()
        self.session = requests.Session()
        self.nlp = spacy.load("en_core_web_trf")
        self.max_depth_level = max_depth_level
        self.max_sentences_from_paragraph = max_sentences_from_paragraph

    def get_article(self, url):
        """Fetch the article text from Wikipedia given its URL."""
        return self.session.get(self.URL_BASE + url).text

    def trim_first_paragraph_and_extract_infobox(self, text):
        """
        Extract the first paragraph and infobox content from the article text.

        :param text: The HTML content of the article.
        :return: A tuple containing the first paragraph and the infobox content.
        """
        content = text[text.find(HEADER_CONTENT_BEGIN_PATTERN):text.find(HEADER_CONTENT_END_PATTERN)]
        content = " ".join(re.findall(P_TAG, content))
        content = re.sub(SPAN, '', content)
        content = re.sub(SUP, '', content)

        infobox = text[text.find(INFOBOX_BEGIN_PATTERN) : text.find(INFOBOX_END_PATTERN)]

        return content, infobox
        
    def get_links(self, text):
        """
        Extract links from the article text.

        :param text: The HTML content of the article.
        :return: A list of links found in the article.
        """
        links = re.findall(LINK_A, text)
        result = []
        for link in links:
            url = re.findall(LINK_HREF, link)
            if len(url) > 0:
                result.append(url[0].split('"')[0])
        return result

    def get_triples_from_infobox(self, infobox_content, article_name):
        """
        Extract triples from the infobox content of the article.

        :param infobox_content: The HTML content of the infobox.
        :param article_name: The title of the article for context.
        """
        infobox_content = re.sub(SUP, '', infobox_content)
        soup = BeautifulSoup(infobox_content, 'html.parser')
        infobox = soup.find('table', class_='infobox')

        for row in infobox.find_all('tr'):
            label_cell = row.find('th', class_='infobox-label')
            # skipping sub-properties with •, as they were raising exception
            if label_cell and not '•' in label_cell.get_text():
                self.triples.add(
                    (article_name.lower(), 'has properties', label_cell.get_text().strip()))

    def get_full_class_name(self, value, links_text, links_titles):
        """
        Determine the full class name based on dependency parsing.

        :param value: The SpaCy token representing a potential class.
        :param links_text: List of text from links found in the sentence.
        :param links_titles: List of titles corresponding to the links.
        :return: A list containing the full class name and any additional connections.
        """
        class_name = value.text
        context = []
        other_conenctions = []
        sentence_links = links_text        

        link_class_name = None
        children_deps = [child.dep_ for child in value.children]
        if 'compund' in children_deps or 'amod' in children_deps:
            if len(list(value.lefts)) > 0:
                class_name = list(value.lefts)[-1].text+" "+class_name
                match_ctr = 0
                for link in sentence_links:
                    if class_name in link:
                        if match_ctr == 0:
                            link_class_name = link
                        else:
                            link_class_name = None
                        match_ctr += 1
        if link_class_name is None:
            class_name = value.text
            if [t.text for t in value.doc].count(class_name)<2:
                match_ctr = 0                
                for link in sentence_links:
                    if class_name in link:
                        if match_ctr == 0:
                            link_class_name = link
                        else:
                            link_class_name = None
                        match_ctr += 1
            if link_class_name is None:
                if value.pos_ != 'NOUN':
                    return ['']
                
                for child in value.children:
                    if child.text == 'of':
                        return ['']
                    if (child.dep_ == 'compound' or child.dep_ == 'amod') \
                       and child in value.lefts:
                        class_name = child.text +' '+ class_name
                        context.append(child.text)

                if len(context) > 1:
                    context = sorted(context, key=lambda x: [v.text for v in value.lefts].index(x), reverse=True)
                    class_name = value.text
                    for v in context[:-1]:
                        if v[:-1] == '-':
                            class_name = v + class_name
                        else:
                            class_name = v + ' ' + class_name
        if link_class_name is not None:
            class_name = links_titles[links_text.index(link_class_name)]
        for child in value.children:
            if child.dep_ == 'conj':
                other_conenctions += self.get_full_class_name(
                    child, 
                    links_text, 
                    links_titles)

        return [class_name] + other_conenctions


    def get_triples(self, content, article_name):
        """
        Extract triples from the article content based on predefined phrases.

        :param content: The content of the article to analyze.
        :param article_name: The title of the article for context.
        """
        sentences = re.findall(SENTENCE_UNTIL_PERIOD, content)

        for sentence_raw in sentences[:self.max_sentences_from_paragraph]:
            try:
                soup = BeautifulSoup(sentence_raw, "html.parser")
                sentence_text = soup.get_text()
            except:
                print(sentence_raw)
                continue

            doc = self.nlp(sentence_text)
            tokens = [token.text for token in doc]

            links_texts = [a.get_text() for a in soup.find_all('a')]
            links_titles = [a.get('title') if a.get('title') else a.get_text() for a in soup.find_all('a')]


            for phrase in PHRASES_TO_MATCH:
                sentence_copy = sentence_text
                relation = ''
                first_noun = ''
                second_noun = []
                if phrase in sentence_copy:
                    try:
                        index_of_phrase_base = tokens.index(phrase.split(" ")[1])
                    except ValueError:
                        print(sentence_copy)
                        continue

                    match phrase:
                        case " is a " | " is an " | " is the " | " are the ":
                            if doc[index_of_phrase_base].pos_ == 'AUX':
                                relation = 'is a'
                                for child in doc[index_of_phrase_base].children:
                                    
                                    if child.dep_ == 'nsubj':
                                        if child.pos_ in ('NOUN', 'PROPN'):
                                            first_noun = self.get_full_class_name(child, links_texts, links_titles)[0]
                                    if child.dep_ == 'attr':                                        
                                        if child.pos_ in ('NOUN', 'PROPN'):
                                            second_noun = self.get_full_class_name(child, links_texts, links_titles)
                                    
                        case " refer to " | " refers to ":                            
                            relation = 'is a'
                            for child in doc[index_of_phrase_base].children:
                                if child.dep_ == 'nsubj':
                                    if child.pos_ in ('NOUN', 'PROPN'):
                                        first_noun = self.get_full_class_name(child, links_texts, links_titles)[0]
                                    if child.pos_ in 'PRON':
                                        first_noun = article_name
                            for child in doc[index_of_phrase_base+1].children:            
                                if child.dep_ == 'pobj':                                        
                                    if child.pos_ in ('NOUN', 'PROPN'):
                                        second_noun = self.get_full_class_name(child, links_texts, links_titles)

                        case " consists of ":
                            relation = 'consist of'
                            for child in doc[index_of_phrase_base].children:
                                if child.dep_ == 'nsubj':
                                    if child.pos_ in ('NOUN', 'PROPN'):
                                        first_noun = self.get_full_class_name(child, links_texts, links_titles)[0]
                                    if child.pos_ in 'PRON':
                                        first_noun = article_name
                            for child in doc[index_of_phrase_base+1].children:            
                                if child.dep_ == 'pobj':                                        
                                    if child.pos_ in ('NOUN', 'PROPN'):
                                        second_noun = self.get_full_class_name(child, links_texts, links_titles)

                        case " include " | " includes ":
                            relation = 'include'
                            for child in doc[index_of_phrase_base].children:
                                if child.dep_ == 'nsubj':
                                    if child.pos_ in ('NOUN', 'PROPN'):
                                        first_noun = self.get_full_class_name(child, links_texts, links_titles)[0]
                                    if child.pos_ in 'PRON':
                                        first_noun = article_name
                            for child in doc[index_of_phrase_base].children:            
                                if child.dep_ == 'dobj':                                        
                                    if child.pos_ in ('NOUN', 'PROPN'):
                                        second_noun = self.get_full_class_name(child, links_texts, links_titles)
                        case " has a " | " have a ":
                            relation = 'have'
                            for child in doc[index_of_phrase_base].children:
                                if child.dep_ == 'nsubj':
                                    if child.pos_ in ('NOUN', 'PROPN'):
                                        first_noun = self.get_full_class_name(child, links_texts, links_titles)[0]
                                    if child.pos_ in 'PRON':
                                        first_noun = article_name
                            for child in doc[index_of_phrase_base].children:            
                                if child.dep_ == 'dobj':                                        
                                    if child.pos_ in ('NOUN', 'PROPN'):
                                        second_noun = self.get_full_class_name(child, links_texts, links_titles)
                        case " is composed of ":                            
                            # SPECIAL CASE where 'composed' is better word to find index
                            try:
                                index_of_phrase_base = tokens.index(phrase.split(" ")[2])
                            except ValueError:
                                print(sentence_copy)
                                continue
                            relation = 'is composed of'
                            for child in doc[index_of_phrase_base].children:
                                if child.dep_ == 'nsubjpass':
                                    if child.pos_ in ('NOUN', 'PROPN'):
                                        first_noun = self.get_full_class_name(child, links_texts, links_titles)[0]
                                    if child.pos_ in 'PRON':
                                        first_noun = article_name
                            for child in doc[index_of_phrase_base+1].children:            
                                if child.dep_ == 'pobj':                                        
                                    if child.pos_ in ('NOUN', 'PROPN'):
                                        second_noun = self.get_full_class_name(child, links_texts, links_titles)
                        case " made up of ":
                            relation = 'made up of'
                            for child in doc[index_of_phrase_base].children:
                                if child.dep_ == 'nsubjpass':
                                    if child.pos_ in ('NOUN', 'PROPN'):
                                        first_noun = self.get_full_class_name(child, links_texts, links_titles)[0]
                                    if child.pos_ in 'PRON':
                                        first_noun = article_name
                            for child in doc[index_of_phrase_base+2].children:            
                                if child.dep_ == 'pobj':                                        
                                    if child.pos_ in ('NOUN', 'PROPN'):
                                        second_noun = self.get_full_class_name(child, links_texts, links_titles)
                        case " made of ":
                            relation = 'made of'
                            for child in doc[index_of_phrase_base].children:
                                if child.dep_ == 'nsubjpass':
                                    if child.pos_ in ('NOUN', 'PROPN'):
                                        first_noun = self.get_full_class_name(child, links_texts, links_titles)[0]
                                    if child.pos_ in 'PRON':
                                        first_noun = article_name
                            for child in doc[index_of_phrase_base+1].children:            
                                if child.dep_ == 'pobj':                                        
                                    if child.pos_ in ('NOUN', 'PROPN'):
                                        second_noun = self.get_full_class_name(child, links_texts, links_titles)
                        case " is part of ":
                            # SPECIAL CASE where 'part' is better word to find index
                            try:
                                index_of_phrase_base = tokens.index(phrase.split(" ")[2])
                            except ValueError:
                                print(sentence_copy)
                                continue

                            relation = 'part of'
                            for child in doc[index_of_phrase_base-1].children:
                                if child.dep_ == 'nsubj':
                                    if child.pos_ in ('NOUN', 'PROPN'):
                                        first_noun = self.get_full_class_name(child, links_texts, links_titles)[0]
                                    if child.pos_ in 'PRON':
                                        first_noun = article_name
                            for child in doc[index_of_phrase_base+1].children:            
                                if child.dep_ == 'pobj':                                        
                                    if child.pos_ in ('NOUN', 'PROPN'):
                                        second_noun = self.get_full_class_name(child, links_texts, links_titles)
                        case " uses ":
                            relation = 'use'
                            for child in doc[index_of_phrase_base].children:
                                if child.dep_ == 'nsubj':
                                    if child.pos_ in ('NOUN', 'PROPN'):
                                        first_noun = self.get_full_class_name(child, links_texts, links_titles)[0]
                                    if child.pos_ in 'PRON':
                                        first_noun = article_name
                            for child in doc[index_of_phrase_base].children:            
                                if child.dep_ == 'dobj':                                        
                                    if child.pos_ in ('NOUN', 'PROPN'):
                                        second_noun = self.get_full_class_name(child, links_texts, links_titles)
                        case default:
                            print('Phrase detected, but handler not implemented.')

                    if first_noun != '' and len(second_noun) > 0 :
                        for noun in second_noun:
                            if noun != '':
                                self.triples.add((first_noun.lower(), relation, noun.lower()))


    def extract(self, url, depth_level=0):
        """
        Recursively extract article content, triples from its first paragraph and infobox, 
        and links found in the first paragraph until reaching the maximum depth level.

        :param url: Link ending for Wikipedia article in format '/wiki/ARTICLE_NAME'
        :param depth_level: Current depth level of recursion (default is set to 0).
        :return: None; triples are saved to the class's triples set.
        """
        article_content = self.get_article(url)
        try:
            article_name = re.findall(ARTICLE_TITLE_PATTERN, article_content)[0]
        except IndexError:
            return

        first_paragraph, infobox = self.trim_first_paragraph_and_extract_infobox(article_content)

        if len(infobox) > 0:
            self.get_triples_from_infobox(infobox, article_name)

        self.get_triples(first_paragraph, article_name)

        if depth_level < self.max_depth_level:
            links = self.get_links(first_paragraph)

            for link in links:
                if link not in self.visited_articles:
                    self.visited_articles.add(link)
                    self.extract(link, depth_level + 1)


    def save_triples_to_file(self, filename):
        """
        Save all the extracted triples to a file in sorted order.

        :param filename: The filename to which the triples will be saved.
        :return: None
        """
        self.triples = sorted(self.triples, key=lambda x: (x[0], x[1]))
        lines = [str(i) + '\n' for i in self.triples]
        with open(filename, 'w', encoding='utf-8') as f:
            f.writelines(lines)

# Run extraction for tested links and measure execution time
for tested_link in TESTED_LINKS:
    start_time = time.time()
    we = WikipediaExtractor(max_depth_level=2)
    we.extract(tested_link)
    end_time = time.time()
    print(f'\rRun finished for {tested_link}, execution time: {end_time - start_time}')

    we.save_triples_to_file(tested_link.split('/')[2]+'_triples_from_wikipedia.txt')
