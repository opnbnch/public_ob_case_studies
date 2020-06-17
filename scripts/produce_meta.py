import sys
import os
import json
import requests

from bs4 import BeautifulSoup

def scrape_meta(request, meta_name):
    """
    scrape_meta is a worker function for scraping metadata from DOI links
    :param request: a requests request
    :param meta_name: the name attribute for the field of interest
    :return: a list of strings associated with the meta_name for the given request
    """

    content_list = []

    try:
        soup = BeautifulSoup(r.text, "html.parser")
        for meta in soup.find_all("meta", {"name": meta_name}):
            content_list.append(meta.get("content"))

        # Notify if no content for a given meta
        if len(content_list) == 0:
            print("No data scraped for", str(meta_name))

        return content_list
    except:
        print("Scraping metadata failed on", str(meta_name))

def parse_doi_meta(doi, outpath=None):
    """
    parse_doi_meta ingests a doi link and an outpath and produces a formatted json metadata file. Intended for
    'best practices' use in OpenBench data curation. Currently limited support for links that resolve to ACS.
    :param doi: a string containing the url for a DOI "Digital Object Signifier"
    :param outpath: A filepath to the directory you want to store output in ... local dir if not otherwise specified
    """

    with requests.get(doi) as r:

        title = scrape_meta(r, 'dc.Title')
        authors = scrape_meta(r, 'dc.Creator')
        doi_link = "https://doi.org/" + str(scrape_meta(r, 'dc.Identifier')[0])
        publisher = scrape_meta(r, 'dc.Publisher')
        date = scrape_meta(r, 'dc.Date')

    meta_dict = {'title': title[0],
                 'authors': authors,
                 'doi': doi_link,
                 'publisher': publisher[0],
                 'date': date[0]}

    if outpath:
        os.makedirs(outpath)
        filename = str(authors[0].split(' ')[-1]) + '_et_al_' + str(date[0].split(' ')[-1]) + "_meta.json"
        fullpath = os.path.join(outpath, filename)
    else:
        fullpath = os.path.join('./', filename)

        print('Writing', filename, 'output to:', fullpath)

        with open(full_path, "w") as outfile:
            json.dump(meta_dict, outfile, indent = 4)

    return meta_dict
