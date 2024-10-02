import requests
import re
import json

# Base Wikipedia URL
URL_BASE = "https://en.wikipedia.org"

# Regex patterns
P_1_BEGIN_PATTERN = '<div id="mw-content-text"'
P_1_END_PATTERN = '<h2>'
BEFORE_LINK = "((?:[a-zA-Z]+ ){1,3})<a"
AFTER_LINK = "a>((?: [a-zA-Z]+){1,3})"
LINK_A ="<a[^>]*[^>]*>[^~]*?</a>"
LINK_HREF = 'href=\"(/.*)?\" '
SPAN="<span[^>]*[^>]*>[^~]*?</span>"
SUP="<sup[^>]*[^>]*>[^~]*?</sup>"
P_TAG = "<p>(.*)"

# Configuration
DEPTH_LEVEL = 2

# Global variables
session = requests.Session()
visited_links = set()
histogram = {}

def get_words(text):
    """
    Extract words that occur around HTML <a> tags (hyperlinks) from the text.
    :param text: HTML content as a string
    :return: List of words surrounding hyperlinks in the content
    """
    result = []
    words = re.findall(BEFORE_LINK, text)
    words.extend(re.findall(AFTER_LINK, text))
    for match in words:
        result.extend(match.split())
    return result

def get_links(text):
    """
    Extract all internal Wikipedia article links from the HTML content.
    :param text: HTML content as a string
    :return: List of Wikipedia article links (relative URLs)
    """
    links = re.findall(LINK_A, text)
    result = []
    for link in links:
        url = re.findall(LINK_HREF, link)
        if len(url) > 0:
            result.append(url[0].split('"')[0])
    return result

def trim_content(text):
    """
    Trim the HTML content of main article body by removing unnecessary parts.
    :param text: HTML content as a string
    :return: Cleaned and trimmed article content
    """
    content = text[text.find(P_1_BEGIN_PATTERN):text.find(P_1_END_PATTERN)]
    content = " ".join(re.findall(P_TAG, content))
    content = re.sub(SPAN, '', content)
    content = re.sub(SUP, '', content)
    return content

def search_in_depth(url, level=0):
    """
    Recursively explore articles by fetching links and extracting words.
    :param url: Wikipedia article URL (relative path)
    :param level: Current depth level of recursive exploration
    """
    r = session.get(URL_BASE + url)
    content = trim_content(r.text)
    
    words = get_words(content)
    for word in words:
        word = word.lower()
        if word in histogram:
            histogram[word] += 1
        else:
            histogram.update({word: 1})

    if level < DEPTH_LEVEL:
        links = get_links(content)
        for link in links:
            if level == 0:
                print(f"\r{int(links.index(link) / len(links) * 100)}%",end="")
            if link not in visited_links:
                visited_links.add(link)
                search_in_depth(link, level + 1)

def main():
    """
    Main function to initialize the process, search articles, and save result.
    """
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

    for tested_link in TESTED_LINKS:
        search_in_depth(tested_link)

    print("\r"+len(visited_links))
    sorted_histogram =sorted(histogram.items(),key=lambda x: x[1],reverse=True)
    with open("global_test.json", 'w') as f:
        json.dump(dict(sorted_histogram), f, ensure_ascii=False, indent=4)

if __name__ == "__main__":
    main()
