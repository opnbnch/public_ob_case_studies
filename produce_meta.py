import argparse
import os

from utils.meta_utils import produce_article_meta, produce_dataset_meta, write_meta, add_meta

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

    dataset_meta = produce_dataset_meta(args.datapath, args.smiles_col,
                                        args.class_col, args.value_col)
    add_meta(fullpath, dataset_meta)
