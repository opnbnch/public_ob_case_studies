import argparse
import json
import os
import requests
import pandas as pd
import sys
import time
import warnings

from bs4 import BeautifulSoup

__version__ = 'v1.0.0 (06-18-2020)'

def scrape_article_meta(request, meta_name):
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

def produce_article_meta(doi):
    """
    parse_acs_meta ingests a doi link and produces a metadata dict. Intended for 'best practices'
    use in OpenBench data curation. Currently limited support for links that resolve to ACS.
    :param doi: a string containing the url for a DOI "Digital Object Signifier"
    """

    with requests.get(doi) as r:

        title = scrape_article_meta(r, 'dc.Title')
        authors = scrape_article_meta(r, 'dc.Creator')
        doi_link = "https://doi.org/" + str(scrape_article_meta(r, 'dc.Identifier')[0])
        publisher = scrape_article_meta(r, 'dc.Publisher')
        date = scrape_article_meta(r, 'dc.Date')

    meta_dict = {'title': title[0],
                 'authors': authors,
                 'doi': doi_link,
                 'publisher': publisher[0],
                 'date': date[0],
                 'meta_version': __version__,
                 'meta_utc_fix': int(time.time())}

    return meta_dict

def produce_dataset_meta(data_path, smiles_col, class_col=None, value_col=None):
    """
    produce_dataset_meta ingests a datapth and column names and produces a metadata dict.
    :param data_path: str - path to a csv to ingest
    :param smiles_col: str - column name for col containing SMILES strings
    :param class_col: str - column name for col containing experimental property classes
    :param value_col: str - column name for col containing experimental values
    """

    df = pd.read_csv(data_path)
    raw_rows = df.shape[0]

    for col in [x for x in [smiles_col, class_col, value_col] if x]:
        if col not in list(df.columns):
            warnings.warn(col + " is not a column in your dataset. You may have made a typo.", Warning)

    if class_col is None and value_col is None:
        warnings.warn('You have neither a value nor class column. This makes for poor training data!', Warning)

    meta_dict = {'data_path': data_path,
                 'raw_rows': raw_rows,
                 'smiles_col': smiles_col,
                 'class_col': class_col,
                 'value_col': value_col}

    return(meta_dict)


def write_meta(meta_dict, outpath=None, filename = None):
    """
    write_meta writes a metadata dictionary to json at a specified path
    :param meta_dict: dict - The metadata dict to write
    :param outpath: str - path to output directory
    :param filename: str - specific filename to write to
    """

    #Compose filename from meta_dict
    if filename is None:
        first_author_last_name = str(meta_dict.get('authors')[0].split(' ')[-1])
        year = str(meta_dict.get('date').split(' ')[-1])
        filename = first_author_last_name + '_et_al_' + year + "_metadata.json"

    if outpath is not None:
        if not os.path.isdir(outpath):
            os.makedirs(outpath)

        fullpath = os.path.join(outpath, filename)
        fp_meta = {'meta_path': fullpath}
        print('Writing', filename, 'output to:', fullpath)

        meta_dict = {**meta_dict, **fp_meta}

        with open(fullpath, "w") as outfile:
            json.dump(meta_dict, outfile, indent = 4)
    else:
        print(meta_data)
        print('No outpath specified. Not writing', filename)

    return fullpath

def add_meta(meta_path, new_data_dict):
    """
    add_meta merges new data into metadata file and writes
    :param meta_path: str - current metadata file
    :param new_data_dict: dict - data to be added to metadata json
    """

    with open(meta_path, "r") as infile:

        meta = json.load(infile)
        new_meta = {**meta, **new_data_dict}

    with open(meta_path, "w") as outfile:
        json.dump(new_meta, outfile, indent = 4)

def read_meta(path):
    """
    Read the metadata for a given path
    :param path: str - filepath to directory where metadata resides
    """

    files = os.listdir(path)
    metadata_file = [file for file in files if 'metadata.json' in file][0]
    metadata_full = os.path.join(path, metadata_file)

    with open(metadata_full, 'r') as f:
        meta = json.load(f)

    return meta

if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument('doi', type=str,
                        help="DOI url you want to parse for metadata")
    parser.add_argument('datapath', type=str,
                            help="path to data source for paper")
    parser.add_argument('-s', '--smiles_col', type=str, default=None,
                        help="column name for smiles col")
    parser.add_argument('-c', '--class_col', type=str, default=None,
                        help="column name for class col")
    parser.add_argument('-r', '--value_col', type=str, default=None,
                        help="column name for value col")
    args = parser.parse_args()

    outpath = os.path.dirname(args.datapath)

    print("Producing dataset metadata for:", args.doi)
    print("Metadata will be written to:", outpath)

    article_meta = produce_article_meta(args.doi)
    fullpath = write_meta(article_meta, outpath)

    dataset_meta = produce_dataset_meta(args.datapath, args.smiles_col, args.class_col, args.value_col)
    add_meta(fullpath, dataset_meta)
