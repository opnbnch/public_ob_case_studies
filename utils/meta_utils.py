import json
import os
import requests
import pandas as pd
import time

from bs4 import BeautifulSoup

__version__ = 'v1.0.0 (06-18-2020)'


def read_meta(path):
    """
    Read the metadata for a given path
    :str path: filepath to directory where metadata resides
    """

    files = os.listdir(path)
    metadata_file = [file for file in files if 'metadata.json' in file][0]
    metadata_path = os.path.join(path, metadata_file)

    with open(metadata_path, 'r') as f:
        meta = json.load(f)

    return meta


def write_meta(meta_dict, outpath=None, filename=None):
    """
    write_meta writes a metadata dictionary to json at a specified path
    :dict meta_dict: The metadata dict to write
    :str outpath: path to output directory
    :str filename: specific filename to write to
    """

    # Compose filename from meta_dict if none provided
    if filename is None:
        first_author_last_name = str(meta_dict.get('authors')[0]
                                              .split(' ')[-1])
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
            json.dump(meta_dict, outfile, indent=4)
    else:
        print(meta_dict)
        print('No outpath specified. Not writing', filename)

    return fullpath


def scrape_article_meta(request, meta_name):
    """
    scrape_meta is a worker function for scraping metadata from DOI links
    :param request: a requests request
    :str meta_name: the name attribute for the field of interest
    :return: list of scraped strings
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
    except Exception:
        print("Scraping metadata failed on", str(meta_name))


def produce_article_meta(doi):
    """
    Ingest a doi link and produces a metadata dict.
    Currently limited support for links that resolve to ACS.
    :str doi: The url for a DOI "Digital Object Signifier"
    """

    with requests.get(doi) as r:

        title = scrape_article_meta(r, 'dc.Title')
        authors = scrape_article_meta(r, 'dc.Creator')
        doi_link = "https://doi.org/" + \
            str(scrape_article_meta(r, 'dc.Identifier')[0])
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


def produce_dataset_meta(data_path):
    """
    Ingest a datapth and column names and produces a metadata dict.
    :str data_path: path to a csv to ingest
    :str smiles_col: col name for col containing SMILES strings
    :str class_col: col name for col containing experimental property classes
    :str value_col: col name for col containing experimental values
    """

    df = pd.read_csv(data_path)
    raw_rows = df.shape[0]

    meta_dict = {'data_path': data_path,
                 'raw_rows': raw_rows,
                 'smiles_col': None,
                 'value_col': None,
                 'class_col': None}

    return(meta_dict)


def add_meta(meta_path, new_data_dict):
    """
    add_meta merges new data into metadata file and writes
    :str meta_path: current metadata file
    :dict new_data_dict: data to be added to metadata json
    """

    with open(meta_path, "r") as infile:

        meta = json.load(infile)
        new_meta = {**meta, **new_data_dict}

    with open(meta_path, "w") as outfile:
        json.dump(new_meta, outfile, indent=4)
