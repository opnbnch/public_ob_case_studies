import pandas as pd
import numpy as np
import warnings
import questionary
import tqdm

from scipy.stats import norm
from scipy.optimize import minimize_scalar
pd.options.mode.chained_assignment = None

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

    text1 = "How do you want to resolve class for multiple replicates?"
    print(text1)

    prompt = "Please select one option:"
    fn_name = questionary.select(prompt, choices=options).ask()

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

    print('Searching for replicates.')
    for key in tqdm.tqdm(unique_keys):

        group = df.loc[lambda x:x[key_col] == key]
        idx = filter_fn(group)

        idx_keep_dict[key] = idx

    return idx_keep_dict


def replicate_rmsd(df, key_col, value_col, relation_col):
    """
    This function has been adapted with few changes from ATOM Consortium's
    AMPL. Check it out here:
    github.com/ATOMconsortium/AMPL/blob/master/atomsci/ddm/utils/curate_data.py
    Compute RMSD of all uncesored replicate measurements in df from their means
    :pd.DataFrame df: A pandas df of SMILES and assay data
    :str key_col: name of the column representing compound keys
    :str value_col: name of column containing assay values
    :str relation_col: name of column containing relations
    """

    uncensored_df = df[~df[relation_col].isin(['<', '<=', '>', '>='])]

    replicate_keys = pd.DataFrame(uncensored_df[key_col].value_counts()) \
        .loc[lambda x:x[key_col] > 1] \
        .index.to_list()

    unique_devs = []
    for key in replicate_keys:
        values = uncensored_df \
            .loc[lambda x:x[key_col] == key, value_col].values
        unique_devs.extend(values - values.mean())

    with warnings.catch_warnings():
        warnings.simplefilter("ignore", category=RuntimeWarning)
        rmsd = np.sqrt(np.nanmean([dev ** 2 for dev in unique_devs]))

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
    nreps = cmpd_df.shape[0]
    values = cmpd_df[value_col].values

    # If all the replicate values are left- or right-censored,
    # return the smallest or largest reported (threshold) value accordingly.
    if sum(left_censored) == nreps:
        mle_value = min(values)
    elif sum(right_censored) == nreps:
        mle_value = max(values)
    elif sum(left_censored) + sum(right_censored) == 0:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", category=RuntimeWarning)
            mle_value = np.nanmean(values)
    else:
        # Some, but not all observations are censored.
        # First, define the negative log likelihood function
        def loglik(mu):

            ll = -sum(norm.logpdf(values[not_censored], loc=mu, scale=std_est))

            if sum(left_censored) > 0:
                ll -= sum(norm.logcdf(values[left_censored],
                                      loc=mu,
                                      scale=std_est))
            if sum(right_censored) > 0:
                ll -= sum(norm.logsf(values[right_censored],
                                     loc=mu,
                                     scale=std_est))
            return ll

        # Then minimize it
        opt_res = minimize_scalar(loglik, method='brent')
        if not opt_res.success:
            print('Likelihood maximization failed, message is: "%s"'
                  % opt_res.message)
            mle_value = np.nan
        else:
            mle_value = opt_res.x

    return mle_value


def get_val_idx(group, value_col, mle, rmsd):
    """
    Handle replicate groups for value column if we have relations too.
    :pdf.DataFrame group: group of replicates
    :str value_col: name of column containing regression values
    :float mle: maximum likelihood estimate of mean value
    :float rmsd: rmsd for the dataset
    """
    if group.shape[0] == 1:
        return int(group.index[0])
    else:
        val_list = list(group[value_col])
        val_list = [x for x in val_list if str(x) != 'nan']

        if len(val_list) == 0:
            return None
        elif len(val_list) == 1:
            return int(group.loc[lambda x:x[value_col] ==
                       val_list[0]].index[0])
        elif len(val_list) == 2:
            if np.absolute(val_list[1] - val_list[0]) <= 0.25 * rmsd:
                return int(group.loc[lambda x:x[value_col] ==
                                     np.random.choice(
                                         val_list)].index[0])
            else:
                return None
        else:
            nearest = min(val_list, key=lambda x: np.absolute(x-mle))
            return int(group.loc[lambda x:x[value_col] == nearest].index[0])


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

    print('Searching for replicates.')
    for key in tqdm.tqdm(unique_keys):
        group = df.loc[lambda x:x[key_col] == key]
        mle = mle_censored_mean(group, std_est, value_col, relation_col)
        idx = get_val_idx(group, value_col, mle, std_est)

        idx_keep_dict[key] = idx

    return idx_keep_dict


def resolve_type(df, value_col):
    """
    Change the value_col values to be floats
    in case they are of a different type
    :pd.DataFrame df: dataframe of interest
    :str value_col: value column to resolve
    """
    df.loc[::, value_col] = pd.to_numeric(df[value_col], errors='coerce')

    return df


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
