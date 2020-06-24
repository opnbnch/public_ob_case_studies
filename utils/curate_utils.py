

__version__ = 'v1.0.0 (06-22-2020)'

filters = {'unanimous': unanimous_class_filter,
           'majority': majority_class_filter}

def process_filter_input(filter_arg, filters):


    if filter_arg in list(filters.keys()):
        filter_fn = filters[filter_arg]
    else:
        print('Filter unspecified or invalid.')
        filter_fn = ask_for_filter(filters)

    return filter_fn

def ask_for_filter(dispatcher):

    """
    Ask for user input on filter function
    """

    options = list(dispatcher.keys())

    text1 =  \
        """
        How do you want to resolve class for multiple replicates?
        """

    retry = \
        """
        The method you specified is not among the options in {}. Try again:
        """

    print(text1)

    try:
        fn_name = input('Please select one option:{}: '
                        .format(options)).strip()
    except Exception:
        fn_name = -1

    while fn_name not in options:
        try:
            fn_name = input(retry.format(options)).strip()
        except Exception:
            fn_name = -1

    return dispatcher[fn_name]


def df_filter_invalid_smi(df, smiles_col):
    """
    remove rows with invalid smiles from the dataframe
    :pd.DataFrame df: dataframe with invalid smiles
    :str smiles_col: string name for smiles column
    """

    return df.loc[lambda x:x[smiles_col] != 'invalid_smiles']


def unanimous_class_filter(group):
    """
    Only accept a replicate group if they all have the same clas
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
