import argparse
import json
import os
import requests
import pandas as pd
import sys
import warnings

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
        soup = BeautifulSoup(request.text, "html.parser")
        for meta in soup.find_all("meta", {"name": meta_name}):
            content_list.append(meta.get("content"))

        # Notify if no content for a given meta
        if len(content_list) == 0:
            print("No data scraped for", str(meta_name))

        return content_list
    except:
        print("Scraping metadata failed on", str(meta_name))

def produce_acs_meta(acs_doi):
    """
    parse_acs_meta ingests a doi link and produces a json metadata file. Intended for
    'best practices' use in OpenBench data curation. Currently limited support for links that resolve to ACS.
    :param doi: a string containing the url for a DOI "Digital Object Signifier"
    """

    with requests.get(acs_doi) as r:

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

    return meta_dict

def produce_dataset_meta(data_path, smiles_col, activity_col=None, regression_col=None):

    df = pd.read_csv(data_path)
    raw_rows = df.shape[0]

    if smiles_col not in list(df.columns):
        warnings.warn("The smiles_col you provided (" + smiles_col + ")is not in the dataset")

    meta_dict = {'raw_rows': raw_rows,
                 'smiles_col': smiles_col,
                 'activity_col': activity_col,
                 'regression_col': regression_col}

    return(meta_dict)


def write_meta(meta_dict, outpath=None):

    #Compose filename from meta_dict
    first_author_last_name = str(meta_dict.get('authors')[0].split(' ')[-1])
    year = str(meta_dict.get('date').split(' ')[-1])

    filename = first_author_last_name + '_et_al_' + year + "_meta.json"

    if outpath:
        if not os.path.isdir(outpath):
            os.makedirs(outpath)

        fullpath = os.path.join(outpath, filename)
        print('Writing', filename, 'output to:', fullpath)

        with open(fullpath, "w") as outfile:
            json.dump(meta_dict, outfile, indent = 4)
        return fullpath
    else:
        print(meta_data)
        print('No outpath specified. Not writing', filename)

def add_meta_data(meta_path, new_data_dict):

    with open(meta_path, "r") as infile:

        meta = json.load(infile)
        new_meta = {**meta, **new_data_dict}

    with open(meta_path, "w") as outfile:
        json.dump(new_meta, outfile, indent = 4)

if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument('doi', type=str,
                        help="DOI url you want to parse for metadata")
    parser.add_argument('-o', '--outpath', type=str, default=None,
                        help="path to which metadata will be written")
    parser.add_argument('-d', '--datapath', type=str, default=None,
                        help="path to data source for paper")
    parser.add_argument('-s', '--smiles_col', type=str, default=None,
                        help="column name for smiles col")
    parser.add_argument('-a', '--activity_col', type=str, default=None,
                        help="column name for activity col")
    parser.add_argument('-r', '--regression_col', type=str, default=None,
                        help="column name for regression col")
    args = parser.parse_args()

    print("Producing dataset metadata for:", args.doi)

    if args.outpath:
        print("Metadata will be written to:", args.outpath)

    article_meta = produce_acs_meta(args.doi)
    fullpath = write_meta(article_meta, args.outpath)

    if args.datapath:
        dataset_meta = produce_dataset_meta(args.datapath, args.smiles_col, args.activity_col, args.regression_col)
        add_meta_data(fullpath, dataset_meta)
