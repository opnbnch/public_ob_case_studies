
import os

import utils.meta_utils as meta_utils

__version__ = 'v1.0.0 (06-22-2020)'


def df_add_std_class(df, class_map):
    """
    df_add_std_class adds standardized binary class to a df
    :pd.DataFrame df: df of interest
    :dict class_map: mapping of old class to new class
    """

    class_col = list(class_map.keys())[0]

    std_df = df \
        .replace(to_replace=class_map) \
        .rename(columns={class_col: 'std_class'})

    std_df[class_col] = df[class_col]

    return std_df

def get_class_values(df, class_col):
    """
    return unique class values for the class_col
    :pd.DataFrame df: df of interest
    :str class_col: name of the class column
    """

    return list(set(df[class_col].values))

def get_user_classes(classes, options):
    """
    Gets the user input for how classes should be standardized.
    Resricted by options, and creates a dict for easy lookup later.
    :set classes: set of unique classes
    :set options: set of possible options for renaming
    """
    s = list(options)
    options_str = ', '.join(str(i) for i in s)

    user_classes = dict()
    for cur in classes:
        name = input('Assign class ' + str(cur) +
                     ' one of the following values: ' + options_str + ': ')
        while name not in options:
            print('Assignment must be on of ' + options_str)
            name = input('Assign class ' + str(cur) + ''
                         ' one of the following values: ' + options_str + ': ')
        options.remove(name)
        s = list(options)
        options_str = ', '.join(str(i) for i in s)
        user_classes[cur] = name
    return user_classes

def _ask_for_assignment(value, options):
    """
    ask the user for an assignment to the option in question
    :str value: The value that needs to be assigned
    :list options: list of options for assignment 
    """

    try:
        text = 'Assign {} to one of the following values: {}:'
        return int(input(text.format(value, options)).strip())
    except Exception:
        return 'error_val'


def get_class_map(df, class_col):
    """
    Assign class column to appropriate values
    :str path: path to dir where data lives
    """

    class_values = get_class_values(df, class_col)
    class_len = len(class_values)
    options = [x for x in range(0, class_len)]

    first_text = \
        """
        Your class values are non-standard for classification.
        In order for training and testing to run smoothly, let's
        convert your classes to standard form.
        """

    second_text = \
        """
        Your class column, {} currently contains {} unique values.
        Those class values are {}.
        Each class will be mapped into a standard value in {}.
        """

    retry_text = \
        """
        The value you specified is not among the values in {}. Let's try again.
        """

    print(first_text)
    print(second_text
          .format(class_col, class_len, set(class_values), options))

    user_classes = dict()
    for val in class_values:
        # Ask for assignment
        std_val = _ask_for_assignment(val, options)

        # If that fails, keep re-asking
        while std_val not in options:
            print(retry_text.format(options))
            std_val = _ask_for_assignment(val, options)

        # Finally, assign to the map and remove that option.
        user_classes[val] = std_val
        options.remove(std_val)

    return {class_col: user_classes}


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
