import pandas as pd
import numpy as np

from scipy.stats import norm
from scipy.optimize import minimize_scalar

__version__ = 'v1.0.0 (07-01-2020)'


def process_filter_input(filters):
    """
    Process filter input from the command line
    :dict filters: dict holding all availabe filter methods
    """

    filter_fn = ask_for_filter(filters)

    return filter_fn


def ask_for_filter(dispatcher):
    """
    Ask for user input on filter function
    :dict filters: dict holding all availabe filter methods
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


def _unanimous_class_filter(group):
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


def _simple_majority_filter(group):
    """
    Only accept a replicate group with a clear majority in one class
    :pd.DataFrame group: group of replicates
    """

    if group.shape[0] == 1:
        return int(group.index[0])
    else:
        votes = pd.DataFrame(group.std_class.value_counts())

        max_vote = np.max(votes.std_class)
        vote_num = votes.shape[0]

        if max_vote / vote_num <= .5:
            return None
        else:
            maj_class = votes.loc[lambda x:x.std_class == max_vote].index[0]
            return int(group.loc[lambda x:x.std_class == maj_class].index[0])


def class_keep_indices(df, key_col, filter_fn):
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


def replicate_rmsd(df, smiles_col, value_col, relation_col):
    """
    This function has been adapted with few changes from ATOM Consortium's
    AMPL. Check it out here:
    github.com/ATOMconsortium/AMPL/blob/master/atomsci/ddm/utils/curate_data.py
    Compute RMSD of all uncesored replicate measurements in df from their means.
    :pd.DataFrame df: A pandas df of SMILES and assay data
    :str smiles_col: name of the column of smiles representations
    :str value_col: name of column containing assay values
    :str relation_col: name of column containing relations
    """
    dset_df = df[~(df[relation_col].isin(['<', '<=', '>', '>=']))]
    uniq_smiles, uniq_counts = np.unique(dset_df[smiles_col].values,
                                         return_counts=True)
    smiles_with_reps = uniq_smiles[uniq_counts > 1]
    uniq_devs = []
    for smiles in smiles_with_reps:
        values = dset_df[dset_df[smiles_col] == smiles][value_col].values
        uniq_devs.extend(values - values.mean())
    uniq_devs = np.array(uniq_devs)
    rmsd = np.sqrt(np.mean(uniq_devs ** 2))
    return rmsd


def mle_censored_mean(cmpd_df, std_est, value_col, relation_col):
    """
    This function has been adapted with few changes from ATOM Consortium's
    AMPL. Check it out here:
    github.com/ATOMconsortium/AMPL/blob/master/atomsci/ddm/utils/curate_data.py
    Compute a maximum likelihood estimate of the true mean value underlying
    the distribution of replicate assay measurements for a single compound.
    The data may be a mix of censored and uncensored measurements,
    as indicated by the 'relation' column in the input data frame cmpd_df.
    :pd.DataFrame cmpd_df: data for a single compound.
    :float std_est: An estimate for the standard deviation of the distribution.
    :str value_col: name of column containing assay values.
    :str relation_col: name of column containing relations.
    """
    left_censored = np.array(cmpd_df[relation_col].isin(['<', '<=']),
                             dtype=bool)
    right_censored = np.array(cmpd_df[relation_col].isin(['>', '>=']),
                              dtype=bool)
    not_censored = ~(left_censored | right_censored)
    n_left_cens = sum(left_censored)
    n_right_cens = sum(right_censored)
    nreps = cmpd_df.shape[0]
    values = cmpd_df[value_col].values
    nan = float('nan')

    # If all the replicate values are left- or right-censored,
    # return the smallest or largest reported (threshold) value accordingly.
    if n_left_cens == nreps:
        mle_value = min(values)
    elif n_right_cens == nreps:
        mle_value = max(values)
    elif n_left_cens + n_right_cens == 0:
        # If no values are censored, the MLE is the actual mean.
        mle_value = np.mean(values)
    else:
        # Some, but not all observations are censored.
        # First, define the negative log likelihood function
        def loglik(mu):
            ll = -sum(norm.logpdf(values[not_censored], loc=mu, scale=std_est))
            if n_left_cens > 0:
                ll -= sum(norm.logcdf(values[left_censored], loc=mu,
                                      scale=std_est))
            if n_right_cens > 0:
                ll -= sum(norm.logsf(values[right_censored], loc=mu,
                                     scale=std_est))
            return ll

        # Then minimize it
        opt_res = minimize_scalar(loglik, method='brent')
        if not opt_res.success:
            print('Likelihood maximization failed, message is: "%s"'
                  % opt_res.message)
            mle_value = nan
        else:
            mle_value = opt_res.x
    return mle_value


def get_val_idx(group, threshold):
    """
    Handle replicate groups for value column.
    :pdf.DataFrame group: group of replicates
    :float threshold: maximum distance between two replicates
    """
    if group.shape[0] == 1:
        return int(group.index[0])
    else:
        val_list = list(group.value_col)
        if len(val_list) == 2:
            if np.absolute(val_list[1] - val_list[0]) <= threshold:
                return int(group.loc[lambda x:x.value_col ==
                                     np.random.choice(
                                         group.value_col)].index[0])
            else:
                return None
        else:
            avg = np.mean(val_list)
            nearest = min(val_list, key=lambda x: np.absolute(x-avg))
            return int(group.loc[lambda x:x.value_col == nearest].index[0])


def get_rel_val_idx(group, threshold, mle, RMSD):
    """
    Handle replicate groups for value column if we have relations too.
    :pdf.DataFrame group: group of replicates
    :float threshold: maximum distance between two replicates
    :float mle: mle_censored_mean for >2 replicates
    :float RMSD: rmsd for the dataset
    """
    if group.shape[0] == 1:
        return int(group.index[0])
    else:
        val_list = list(group.value_col)
        if len(val_list) == 2:
            if np.absolute(val_list[1] - val_list[0]) <= 0.25 * RMSD:
                return int(group.loc[lambda x:x.value_col ==
                                     np.random.choice(
                                         group.value_col)].index[0])
            else:
                return None
        else:
            nearest = min(val_list, key=lambda x: np.absolute(x-mle))
            return int(group.loc[lambda x:x.value_col == nearest].index[0])


def value_keep_indices(df, key_col, relation_col, smiles_col, value_col,
                       threshold):
    """
    For a a value column, grab indices to keep.
    :pd.DataFrame df: DataFrame to curate
    :str key_col: name of column holding group keys
    :str relation_col: name of column holding relations
    :str smiles_col: name of column holding std_smiles
    :str value_col: name of column holding our values
    :float threshold: maximum distance between two replicates
    """

    unique_keys = list(set(df[key_col]))
    std_est = replicate_rmsd(df, smiles_col, value_col, relation_col)
    idx_keep_dict = {}

    for key in unique_keys:
        group = df.loc[lambda x:x[key_col] == key]
        if relation_col is None:
            idx = get_val_idx(group, threshold)
        else:
            mle = mle_censored_mean(group, std_est, value_col, relation_col)
            idx = get_rel_val_idx(group, threshold, mle, std_est)

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


filters = {'unanimous': _unanimous_class_filter,
           'majority': _simple_majority_filter}
