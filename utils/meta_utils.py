import json
import os
import pandas as pd
import time

from crossref.restful import Works
from datetime import datetime

__version__ = 'v1.1.0 (07-01-2020)'


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


def init_meta(meta_dict, outpath=None, filename=None):
    """
    write_meta writes a metadata dictionary to json at a specified path
    :dict meta_dict: The metadata dict to write
    :str outpath: path to output directory
    :str filename: specific filename to write to
    """

    # Compose filename from meta_dict if none provided
    if filename is None:
        prefixes = []
        try:
            first_author_last_name = str(meta_dict.get('authors')[0]
                                         .split(' ')[-1])
            ts = meta_dict.get('published_timestamp')
            year = str(datetime.utcfromtimestamp(ts).year)
            prefixes.extend([first_author_last_name, '_et_al_', year, '_'])

        except Exception:
            if outpath:
                prefixes = [os.path.basename(outpath), '_']

        filename = "".join(prefixes) + "metadata.json"

    if outpath:
        if not os.path.isdir(outpath):
            os.makedirs(outpath)

        fullpath = os.path.join(outpath, filename)
        fp_meta = {'meta_path': fullpath}
        print('Writing metadata output to:', fullpath)

        meta_dict = {**meta_dict, **fp_meta}

        with open(fullpath, "w") as outfile:
            json.dump(meta_dict, outfile, indent=4)
    else:
        print(meta_dict)
        print('No outpath specified. Not writing', filename)

    return fullpath


def scrape_article_meta(record, meta_name):
    """
    scrape_meta is a worker function for scraping metadata from DOI links
    :param request: a requests request
    :str meta_name: the name attribute for the field of interest
    :return: list of scraped strings
    """

    try:
        content = record[meta_name]
        return content
    except Exception:
        print("Scraping metadata failed on", str(meta_name))


def produce_article_meta(doi):
    """
    Ingest a doi link and produces a metadata dict.
    :str doi: The url for a DOI "Digital Object Signifier"
    """

    works = Works() # Initialize crossref API
    record = works.doi(doi) # Grab record for our paper

    # Scrape all relevant info and store in the meta_dict
    title = scrape_article_meta(record, 'title')
    doi_link = scrape_article_meta(record, 'URL')
    publisher = scrape_article_meta(record, 'publisher')
    container = scrape_article_meta(record, 'container-title')
    issue = scrape_article_meta(record, 'issue')
    created = scrape_article_meta(record, 'created')
    timestamp = int(created['timestamp']) / 1000.0
    authors = scrape_article_meta(record, 'author')
    formatted_authors = [x['given'] + ' ' + x['family'] for x in authors]

    meta_dict = {'title': title[0],
                 'authors': formatted_authors,
                 'doi': doi_link,
                 'publisher': publisher,
                 'container': container[0],
                 'issue': issue,
                 'published_timestamp': int(timestamp),
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
    column_names = list(df.columns)

    meta_dict = {'data_path': data_path,
                 'data_row_num': raw_rows,
                 'data_columns': column_names,
                 'smiles_col': None,
                 'value_col': None,
                 'class_col': None}

    return(meta_dict)


def ask_for_doi():
    """
    Ask for the DOI source and format if full URL is given
    """

    doi_prompt = \
        """
        Please input the DOI for this data source. Enter 'none' if there is no
        DOI source:
        """

    doi = input(doi_prompt)

    if 'doi.org/' in doi:
        doi = doi.split('doi.org/')[1]
    elif doi == 'none':
        doi = None

    return doi


def get_doi():
    """
    Get the DOI by looping through asks if necessary
    """

    doi = ask_for_doi()

    while doi and not check_doi_validity(doi):
        print("Sorry, the DOI you input is not valid or not in our system.")
        doi = ask_for_doi()

    return doi


def check_doi_validity(doi):
    """
    Check if a DOI is valid and accessible through CrossRef
    :str doi: A DOI string
    """

    works = Works()

    if works.doi(doi):
        return True
    else:
        return False


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
