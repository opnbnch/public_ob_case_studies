import argparse

if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument('path', type=str,
                        help="path to directory with data of interest")
    args = parser.parse_args()

    meta = read_meta(args.path)
    smiles_col = meta.get('smiles_col')
    meta_path = meta.get('meta_path')
