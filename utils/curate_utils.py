from collections import Counter

__version__ = 'v1.0.0 (06-22-2020)'


def df_filter_invalid_smi(df, smiles_col):
    """
    remove rows with invalid smiles from the dataframe
    :pd.DataFrame df: dataframe with invalid smiles
    :str smiles_col: string name for smiles column
    """

    return df.loc[lambda x:x[smiles_col] != 'invalid_smiles']


def majority_class_filter(group):
    """
    Only accept a replicate group if there is a strict majority
    for the same class.
    :pd.DataFrame group: group of replicates
    """

    if group.shape[0] == 1:
        return int(group.index[0])
    else:
        class_vals = group.std_class.values
        counts = Counter(class_vals)
        top_two = counts.most_common(2)
        if len(top_two) == 1 or (top_two[0][1] > top_two[1][1]):
            return int(top_two[0][0])
        else:
            return None


def unanimous_class_filter(group):
    """
    Only accept a replicate group if they all have the same class
    :pd.DataFrame group: group of replicates
    """

    if group.shape[0] == 1:
        return int(group.index[0])
    else:
        class_vals = group.std_class.values
        if len(set(class_vals)) > 1:
            return None
        else:
            return int(group.index[0])


def get_keep_indices(df, key_col, filter_fn):
    """
    For a given filter function, grab the indices to keep
    :pd.DataFrame df: DataFrame to curate
    :str key_col: name of column holding group keys
    :fn filter_fn: function to filter on
    """

    unique_keys = list(set(df[key_col]))
    idx_keep_dict = {}

    for key in unique_keys:

        group = df.loc[lambda x:x[key_col] == key]
        idx = filter_fn(group)

        idx_keep_dict[key] = idx

    return idx_keep_dict


def df_filter_replicates(df, idx_keep_dict):
    """
    Filter out replicates in a data frame
    :pd.DataFrame df: dataframe with replicates
    :str key_col: Column with key on which to judge replicates
    :fn filter_fn: method for filtering the replicate df
    """

    # Remove keys that retain no replicates
    non_none_dict = {}
    for elem in idx_keep_dict.items():
        if elem[1] is not None:
            non_none_dict.update({elem[0]: elem[1]})

    return df.loc[list(non_none_dict.values()), ::]
