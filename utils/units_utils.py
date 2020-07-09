def get_valid_unit(prompt, units_list):
    """
    General helper function to get a single value
    from a list of values.
    :str prompt: Prompt to give to the user
    :list units_list: units the user can choose from
    """

    std_unit = input(prompt.format('[' + ', '.join(units_list) + ']'))
    while std_unit not in units_list:
        print('\tEnter a valid unit.')
        std_unit = input(prompt.format('[' + ', '.join(units_list) + ']'))
    return std_unit


def get_unit_values(df, unit_col):
    """
    return unique unit values for the unit_col
    :pd.DataFrame df: df of interest
    :str unit_col: name of the unit column
    """

    return list(set(df[unit_col].values))


def df_add_std_unit(df, unit_map):
    # TODO: replace (multiply) matching df vals in map
    # to CREATE new std_unit col
    return df


def get_relationship(prompt, cur_unit, std_unit):
    while True:
        relation = input(prompt.format(cur_unit, std_unit))
        try:
            val = float(relation)
            return val
        except ValueError:
            print('\tPlease enter a valid number')


def get_unit_map(df, unit_col):
    unit_map = {}
    unit_values = get_unit_values(df, unit_col)
    unit_values = [str(x) for x in unit_values]
    num_units = len(unit_values)

    # Everything is already the same unit
    if num_units == 1:
        return unit_map, unit_values[0]

    text1 = \
        """
        You have {} different unit types. Let's standardize them.
        """
    print(text1.format(num_units))

    prompt = \
        """
        Enter which of the units in this column we should standardize to {}:
        """
    std_unit = get_valid_unit(prompt, unit_values)

    unit_values.remove(std_unit)

    prompt = \
        """
        What is the multiplication factor to convert {} to {}?
        """
    for cur_unit in unit_values:
        mult_factor = get_relationship(prompt, cur_unit, std_unit)  # get float
        unit_map[cur_unit] = mult_factor

    return unit_map, std_unit
