class _MISSING:
    """
    Database None, used for
    columns that can be set to
    None / NULL.
    """
    def __bool__(self):
        return False

    def __eq__(self, other):
        return False

    def __repr__(self):
        return 'MISSING'

MISSING = _MISSING()
