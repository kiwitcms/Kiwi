# -*- coding: utf-8 -*-


__all__ = ('GroupByResult')


# TODO: redesign GroupByResult, major goal is to distiguish level node and
# value node.
class GroupByResult:
    """Group By result

    This object can be used as a normal dict object with less support of stock
    dictionary methods. Consumers can do

        - get a subtotal associated with a name
        - get a subtotal's percentage
        - know whether it's empty. Empty means no data from database of the
          GROUP BY query
        - how many subtotals there

    The main purpose of GroupByResult is to get specific subtotal(s) and the
    percentage of each of them. Rules to get such values

        - each subtotal is associated with a name. If name you give does not
          exist, 0 is returned, otherwise proper value is returned.
        - percentage of each subtotal has a special name with format of
          subtotal name plus '_percent'.

    Examples:

    Suppose, a GroupByResult object named gbr is {'A': 100, 'B': 200}

    To get subtotal of A, `gbr.A`

    To get percentage of B, `gbr.B_percent`
    """

    def __init__(self, data=None, total_name=None):
        self._total_name = total_name
        self._data = {} if data is None else dict(data)
        self._total_result = self._get_total()

        self._meta = {}

    # ## proxy method ###

    def __contains__(self, item):
        return self._data.__contains__(item)

    def __getitem__(self, key):
        return self._data.__getitem__(key)

    def __setitem__(self, key, value):
        # TODO: calculate total immediately would be more efficient
        return self._data.__setitem__(key, value)

    def __delitem__(self, key):
        return self._data.__delitem__(key)

    def __len__(self):
        return self._data.__len__()

    def __str__(self):
        return self._data.__str__()

    def __repr__(self):
        return self._data.__repr__()

    def get(self, key, default=None):
        return self._data.get(key, default)

    def items(self):
        return self._data.items()

    def setdefault(self, key, default=None):
        return self._data.setdefault(key, default)

    def keys(self):
        return self._data.keys()

    # ## end of proxy methods ###

    @property
    def empty(self):
        return len(self._data) == 0

    def _get_total(self):
        """Get the total value of this GROUP BY result

        Total value comes from two situations. One is that there is no total
        value computed in database side by issuing GROUP BY with ROLLUP. In
        this case, total value will be calculated from all subtotal values.
        Inversely, the total value will be returned directly.
        """
        if self.empty:
            return 0

        if self._total_name is not None:
            # Hey, GROUP BY ... WITH ROLLUP is already used to get the total
            # result.
            total = self[self._total_name]
        else:
            total = 0
            for _, subtotal in self._data.items():
                # NOTE: is it possible do such judgement in advance when adding
                # element
                if isinstance(subtotal, int):
                    total += subtotal
                elif isinstance(subtotal, GroupByResult):
                    total += subtotal.total

        return total

    total = property(_get_total)

    def _get_percent(self, key):
        """Percentage of a subtotal

        @param key: name of subtotal whose percentage will be calculated
        @type key: str
        @return: a float number representing the percentage
        @rtype: float
        """
        total = self._total_result
        subtotal = self[key]
        if total == 0:
            return .0
        return subtotal * 100.0 / total

    def __getattr__(self, name):
        if name.endswith('_percent'):
            key, _ = name.split('_')
            if key in self._data:
                return self._get_percent(key)
        return 0

    def leaf_values_count(self, value_in_row=False, refresh=False):
        """Calculate the total number of leaf values under this level

        After the first time this method gets call, the result will be cached
        as meta data of this level node. So, any number of subsequent
        invocations of this method will return result by reading self._meta
        directly without repeating calculation. Unless, pass True to argument
        refresh.

        @param value_in_row: whether leaf value should be treated as a row, in
            such way, leaf value will be displayed in one row.
        @type value_in_row: bool
        @param refresh: whether force to recalculate
        @type refresh: bool
        @return: the total number of leaf values under this level
        @rtype: int
        """
        if refresh:
            necessary_to_count = True
        else:
            necessary_to_count = 'value_leaf_count' not in self._meta
        if not necessary_to_count:
            return self._meta['value_leaf_count']

        count = 0
        for _, value in self.items():
            if isinstance(value, GroupByResult):
                count += value.leaf_values_count(value_in_row)
            else:
                count = 1 if value_in_row else count + 1
        self._meta['value_leaf_count'] = count
        return count
