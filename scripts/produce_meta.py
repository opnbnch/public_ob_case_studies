import argparse
import json
import os
import requests
import sys

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

def produce_doi_meta(doi, outpath=None):
    """
    parse_doi_meta ingests a doi link and an outpath and produces a formatted json metadata file. Intended for
    'best practices' use in OpenBench data curation. Currently limited support for links that resolve to ACS.
    :param doi: a string containing the url for a DOI "Digital Object Signifier"
    :param outpath: A filepath to the directory you want to store output in ... no write if outpath is None
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
        print('Writing', filename, 'output to:', fullpath)

        with open(full_path, "w") as outfile:
            json.dump(meta_dict, outfile, indent = 4)

    return meta_dict

if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument('doi', type=str,
                        help="DOI url you want to parse for metadata")
    parser.add_argument('-o', '--outpath', type=str, default=None,
                        help="path to which metadata will be written")
    args = parser.parse_args()

    print("Producing dataset metadata for:", args.doi)

    if args.outpath:
        print("Metadata will be written to:", args.outpath)

    produce_doi_meta(args.doi, args.outpath)
