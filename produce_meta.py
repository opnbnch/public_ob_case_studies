import argparse
import os

from utils.meta_utils import produce_article_meta, produce_dataset_meta
from utils.meta_utils import init_meta, add_meta

def produce_meta(doi, data_path):
    """
    Produces initial meta data for a database to be cleaned and curated
    :str doi: ACS doi URL
    :str data_path: filepath to dataset to be cleaned and curated 
    """

    print("Producing dataset metadata for:", doi)

    # Extract outpath from data path provided
    outpath = os.path.dirname(data_path)

    article_meta = produce_article_meta(doi)
    fullpath = init_meta(article_meta, outpath)

    dataset_meta = produce_dataset_meta(data_path)
    add_meta(fullpath, dataset_meta)

if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument('doi', type=str,
                        help="DOI url you want to parse for metadata")
    parser.add_argument('data_path', type=str,
                        help="path to data source for paper")
    args = parser.parse_args()

    produce_meta(args.doi, args.data_path)
