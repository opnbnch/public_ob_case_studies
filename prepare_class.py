import argparse
import time

from utils.meta_utils import read_meta, add_meta
from utils.std_utils import read_std_data
from utils.class_utils import class_mapping_dict, df_add_std_class
from utils.class_utils import write_san, __version__

if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument('path', type=str,
                        help="path to directory with data of interest")
    args = parser.parse_args()

    meta = read_meta(args.path)
    smiles_col = meta.get('smiles_col')
    class_col = meta.get('class_col')
    meta_path = meta.get('meta_path')

    df = read_std_data(args.path)

    class_map = class_mapping_dict(df, class_col)
    san_df = df_add_std_class(df, class_map)

    san_data_path = write_san(san_df, args.path)

    class_meta = {'san_data_path': san_data_path,
                  'std_class_col': 'std_class',
                  'class_version': __version__,
                  'class_map': class_map,
                  'san_utc_fix': int(time.time())}

    add_meta(meta_path, class_meta)

    print('Sanitized df will be written to:', san_data_path)
    print('Updated metadata at:', meta_path)
