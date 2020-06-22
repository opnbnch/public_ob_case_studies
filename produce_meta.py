import argparse
import os

from utils.meta_utils import produce_article_meta, produce_dataset_meta
from utils.meta_utils import write_meta, add_meta

if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument('doi', type=str,
                        help="DOI url you want to parse for metadata")
    parser.add_argument('datapath', type=str,
                        help="path to data source for paper")
    args = parser.parse_args()

    outpath = os.path.dirname(args.datapath)

    print("Producing dataset metadata for:", args.doi)

    article_meta = produce_article_meta(args.doi)
    fullpath = write_meta(article_meta, outpath)

    dataset_meta = produce_dataset_meta(args.datapath)
    add_meta(fullpath, dataset_meta)
