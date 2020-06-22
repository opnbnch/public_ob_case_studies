
import os

import utils.meta_utils as meta_utils

__version__ = 'v1.0.0 (06-22-2020)'


def df_add_std_class(df, class_map):

    class_col = list(class_map.keys())[0]

    std_df = df \
        .replace(to_replace=class_map) \
        .rename(columns={class_col: 'std_class'})

    std_df[class_col] = df[class_col]

    return std_df


def class_mapping_dict(df, class_col):
    """
    Assign class column to appropriate values
    :str path: path to dir where data lives
    """

    class_values = list(set(df[class_col].values))

    assert len(class_values) == 2

    first_text = \
        """
        Your class values are non-standard for binary classification.
        In order for training and testing to run smoothly, let's convert your
        classes to standard form. One class will be the positive class (1)
        and the other will be the negative class (0).
        """

    second_text = \
        """
        Your class column currently contains {} unique values.
        Those values are '{}' and '{}'.
        We will now transform one class to (1) and the other class to (0).
        """

    retry_text = \
        """
        The value you specified is not among the values in {}.
        As a reminder, your options are '{}' and '{}'. Let's try again.
        """

    print(first_text)
    print(second_text
          .format(len(class_values), class_values[0], class_values[1]))

    pos_val = input("Which value is the positive class? ").strip()

    while pos_val not in class_values:
        print(retry_text.format(class_col, class_values[0], class_values[1]))
        pos_val = input("Please input whichever of those two columns" +
                        "is positive: ").strip()

    neg_val = [x for x in class_values if x != pos_val][0]

    print("Thank you. '{}' has been mapped to 1. '{}' has been mapped to 0."
          .format(pos_val, neg_val))

    return {class_col: {pos_val: 1,
                        neg_val: 0}}


def write_san(df, outpath, filename=None):
    """
    write_san writes a sanitized csv at a specified path
    :pd.DataFrame df: The dataframe to write
    :str outpath: path to output directory
    :str filename: specific filename to write to
    """

    # Compose filename from meta_dict
    if filename is None:
        meta = meta_utils.read_meta(outpath)
        old_name = os.path.basename(meta.get('data_path'))
        filename = 'san_' + old_name

    if not os.path.isdir(outpath):
        os.makedirs(outpath)

    fullpath = os.path.join(outpath, filename)

    df.to_csv(fullpath, index=False)

    return fullpath
