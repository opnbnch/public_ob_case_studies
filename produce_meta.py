import argparse
import os

from utils.meta_utils import produce_article_meta, produce_dataset_meta
from utils.meta_utils import init_meta, add_meta, get_doi


def produce_meta(data_path):
    """
    Produces initial meta data for a database to be cleaned and curated
    :str data_path: filepath to dataset to be cleaned and curated
    """

    print("Producing dataset metadata for:", data_path)

    # Extract outpath from data path provided
    outpath = os.path.dirname(data_path)

    # Ask for DOI
    doi = get_doi()

    # If a valid DOI exists, scrape article meta and initate meta
    if doi:
        article_meta = produce_article_meta(doi)
        fullpath = init_meta(article_meta, outpath)
        dataset_meta = produce_dataset_meta(data_path)
        add_meta(fullpath, dataset_meta)
    else:  # If not, just initialize with dataset_meta
        dataset_meta = produce_dataset_meta(data_path)
        fullpath = init_meta(dataset_meta, outpath)


if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument('data_path', type=str,
                        help="path to dataset we will be cleaning")
    args = parser.parse_args()

    produce_meta(args.data_path)
