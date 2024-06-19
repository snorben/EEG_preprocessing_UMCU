"""Documentation about the eeg_preprocessing_umcu module."""


# FIXME: put actual code here
def hello(name):
    """Say hello.

    Function docstring using Google docstring style.

    Args:
        name (str): Name to say hello to

    Returns:
        str: Hello message

    Raises:
        ValueError: If `name` is equal to `nobody`

    Example:
        This function can be called with `Jane Smith` as argument using

        >>> from eeg_preprocessing_umcu.my_module import hello
        >>> hello('Jane Smith')
        'Hello Jane Smith!'

    """
    if name == 'nobody':
        raise ValueError('Can not say hello to nobody')
    return f'Hello {name}!'
