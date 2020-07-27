import questionary


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


def get_class_map(df, class_col):
    """
    Assign class column to appropriate values
    :pd.DataFrame df: df with class to map
    :str class_col: name of column containing class of interest
    """

    class_values = get_class_values(df, class_col)
    class_len = len(class_values)
    options = [x for x in range(0, class_len)]

    first_text = "Your class values are non-standard for classification." \
        " In order for training and testing to run smoothly, let's" \
        " convert your classes to standard form."

    second_text = "The class column, {} currently contains {} unique values." \
        " Those class values are {}." \
        " Each class will be mapped into a standard value in {}."

    retry_text = "The value you specified is not among the values in {}." \
        " Let's try again."

    print(first_text)
    print(second_text
          .format(class_col, class_len, set(class_values), options))

    user_classes = dict()
    text = "Assign {} to one of the following values: {}:"

    for val in class_values:
        # Ask for assignment
        prompt = text.format(val, options).strip()
        std_val = questionary.text(prompt).ask()

        # If that fails, keep re-asking
        while std_val not in options:
            print(retry_text.format(options))
            std_val = questionary.text(prompt).ask()

        # Finally, assign to the map and remove that option.
        user_classes[val] = std_val
        options.remove(std_val)

    return {class_col: user_classes}
