from __future__ import annotations

import json
import typing as t
from abc import ABC, abstractmethod

DEBUG = False  # enable debug to raise errors for non-match

JsonValueType = t.Union[int, float, bool, str, dict, list]
TAny = t.TypeVar("TAny", bound="AnyBase")


class JsonValidator:
    """
    A simple JSON validator by schema
    """

    def __init__(self, schema: t.Any) -> None:
        self.schema = schema

    @staticmethod
    def debug(enable: bool) -> None:
        """
        Set debug mode
        """
        global DEBUG
        DEBUG = enable

    def validate_str(self, json_str: str) -> bool:
        """
        Validate a JSON string with the schema
        """
        json_obj = json.loads(json_str)
        return self.validate(json_obj)

    def validate(self, json_obj: t.Any) -> bool:
        """
        Validate a Python object with the schema
        """
        return self.schema == json_obj


class AnyBase(ABC):
    """
    Base Any class to redefine `eq`
    """

    @abstractmethod
    def eq(self, other: t.Any) -> bool:
        """Overload `==` operator"""
        pass

    def union(self: TAny, other: t.Any) -> TAny:
        """Overload `|` operator"""
        return Any(self, other)

    def __eq_impl(self, other: t.Any) -> bool:
        is_equal = self.eq(other)
        if DEBUG and not is_equal:
            raise TypeError(
                "Schema does not match:\n{!r}\n---\n{!r}".format(self, other)
            )
        return is_equal

    def __eq__(self, other: t.Any) -> bool:
        return self.__eq_impl(other)

    def __req__(self, other: t.Any) -> bool:
        return self.__eq_impl(other)

    def __hash__(self) -> int:
        return super().__hash__()

    def __or__(self: TAny, other: t.Any) -> TAny:
        return self.union(other)

    def __ror__(self: TAny, other: t.Any) -> TAny:
        return self.union(other)


class AnyDict(AnyBase):
    """
    Schema representing a JSON dict

    Params:
    `schema`: dict object defining required key-values
    """

    def __init__(self, schema: t.Dict[str, t.Any]) -> None:
        self.has_ellipsis = ... in schema
        self.required_dict = schema

    def eq(self, other: t.Any) -> bool:
        """Override"""
        if not isinstance(other, dict):
            return False
        required_dict = {k: v for k, v in self.required_dict.items() if k != ...}
        if self.has_ellipsis:
            item_to_repeat = self.required_dict[...]
            required_dict.update(
                {k: item_to_repeat for k in other if k not in required_dict}
            )
        return all(other.get(k, None) == v for k, v in required_dict.items())

    def __repr__(self) -> str:
        return "<AnyDict {!r}>".format(self.required_dict)


class AnyList(AnyBase):
    """
    Schema representing a JSON list

    Params:
    `items`: a list object defining required values
    """

    def __init__(self, items: t.List[t.Any]) -> None:
        # validate the Ellipsis
        assert ... not in items[:-1], "Ellipsis `...` can only be the last item"
        assert items != [...], "Ellipsis `...` cannot be the only item"
        self.has_ellipsis = items[-1] == ...
        self.required_items = items[:-1] if self.has_ellipsis else items

    def eq(self, other: t.Any) -> bool:
        """Override"""
        if not isinstance(other, list):
            return False
        required_items = self.required_items
        if self.has_ellipsis:
            item_to_repeat = self.required_items[-1]
            required_items += [item_to_repeat] * (len(other) - len(self.required_items))
        return all(a == b for a, b in zip(required_items, other))

    def __repr__(self) -> str:
        return "<AnyList {!r}>".format(self.required_items)


class AnySet(AnyBase):
    """
    Schema representing a JSON list (unordered)

    Params:
    `items`: a set object defining required values
    """

    def __init__(self, items: t.Set[t.Any]) -> None:
        self.required_items = items

    def eq(self, other: t.Any) -> bool:
        """Override"""
        if not isinstance(other, list):
            return False
        return all(x in other for x in self.required_items)

    def __repr__(self) -> str:
        return "<AnySet {!r}>".format(self.required_items)


class AnyType(AnyBase):
    """
    Schema representing any JSON value type

    Params:
    `type_`: the value type to match
    """

    def __init__(self, type_: t.Type[JsonValueType]) -> None:
        self.type_ = type_

    def eq(self, other: t.Any) -> bool:
        """Override"""
        # distinguish `bool` and `int` cos Python tell True about `isinstance(True, int)`
        if isinstance(other, bool) and self.type_ is int:
            return False
        return isinstance(other, self.type_)

    def __repr__(self) -> str:
        return "<Any{}>".format(self.type_.__name__.capitalize())


class AnyUnion(AnyBase):
    """
    Schema representing an union of any schema

    Params:
    `schema`: a list of schema objects
    """

    def __init__(self, objs: t.Iterable[t.Any]) -> None:
        self.objs = list(objs)

    def __repr__(self) -> str:
        objs_repr = map(repr, self.objs)
        return "<AnyUnion {}>".format("|".join(objs_repr))

    def eq(self, other: t.Any) -> bool:
        """Override"""
        return any(obj == other for obj in self.objs)


class Anything(AnyBase):
    """
    Schema representing literally anything
    """

    def eq(self, other: t.Any) -> bool:
        """Override"""
        return True

    def __repr__(self) -> str:
        return "<Anything>"


def Any(*objs: t.Any) -> t.Any:
    """
    Unified API to define a schema of JSON

    Params:
    `objs`: any schema object to match;
    - if nothing is given, it matches anything;
    - if multiple is given, it matches an union;
    - if one schema is given, for:
      : a JSON value type, it matches any value of that type
      : a dict, it matches JSON dict with AnyDict
      : a list, it matches JSON list with AnyList
      : a set, it matches JSON list (unordered) AnySet
      : anything else, it matches exactly the given object
    """
    if len(objs) == 0:
        return Anything()
    elif len(objs) == 1:
        obj = objs[0]
        if obj in t.get_args(JsonValueType):
            return AnyType(obj)
        elif type(obj) is dict:
            return AnyDict(obj)
        elif type(obj) is list:
            return AnyList(obj)
        elif type(obj) is set:
            return AnySet(obj)
        else:
            return obj
    else:
        return AnyUnion(Any(obj) for obj in objs)
