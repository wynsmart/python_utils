"""
A simple JSON validator by schema
"""

from __future__ import annotations

import json
import typing as t
from abc import ABC, abstractmethod

DEBUG = False  # enable debug to raise errors for non-match

JsonValueType = t.Union[int, float, bool, str, dict, list]


class JsonValidator:
    def __init__(self, schema: t.Any) -> None:

        self.schema = schema

    @staticmethod
    def debug(enable: bool) -> None:
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
    def eq(self, other: object) -> bool:
        pass

    def __eq_impl(self, other: object) -> bool:
        is_equal = self.eq(other)
        if DEBUG and not is_equal:
            raise TypeError(
                "Schema does not match:\n{!r}\n---\n{!r}".format(self, other)
            )
        return is_equal

    def __eq__(self, other: object) -> bool:
        return self.__eq_impl(other)

    def __req__(self, other: object) -> bool:
        return self.__eq_impl(other)

    def __hash__(self) -> int:
        return super().__hash__()


class AnyDict(AnyBase):
    """
    Schema representing a JSON dict

    Params:
    `schema`: dict object defining required key-values
    """

    def __init__(self, schema: t.Dict[str, t.Any]) -> None:
        self.required_dict = schema

    def eq(self, other: object) -> bool:
        if not isinstance(other, dict):
            return False
        return all(other.get(k, None) == v for k, v in self.required_dict.items())

    def __repr__(self) -> str:
        return "<AnyDict {}>".format(self.required_dict)


class AnyList(AnyBase):
    """
    Schema representing a JSON list

    Params:
    `items`: a list object defining required values
    """

    def __init__(self, items: t.List[t.Any]) -> None:
        self.required_items = items

    def eq(self, other: object) -> bool:
        if not isinstance(other, list):
            return False
        return all(a == b for a, b in zip(self.required_items, other))

    def __repr__(self) -> str:
        return "<AnyList {}>".format(self.required_items)


class AnySet(AnyBase):
    """
    Schema representing a JSON list (unordered)

    Params:
    `items`: a set object defining required values
    """

    def __init__(self, items: t.List[t.Any]) -> None:
        self.required_items = items

    def eq(self, other: object) -> bool:
        if not isinstance(other, list):
            return False
        return all(x in other for x in self.required_items)

    def __repr__(self) -> str:
        return "<AnySet {}>".format(self.required_items)


class AnyType(AnyBase):
    """
    Schema representing any JSON value type

    Params:
    `type_`: the value type to match
    """

    def __init__(self, type_: JsonValueType) -> None:
        self.type_ = type_

    def eq(self, other: object) -> bool:
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
        self.objs = objs

    def __repr__(self) -> str:
        objs_repr = map(repr, self.objs)
        return "<AnyUnion {}>".format("|".join(objs_repr))

    def eq(self, other: object) -> bool:
        return any(obj == other for obj in self.objs)


class Anything(AnyBase):
    """
    Schema representing literally anything
    """

    def eq(self, other: object) -> bool:
        return True

    def __repr__(self) -> str:
        return "<Anything>"


def Any(*objs: t.Any) -> t.Union[AnyType, AnyDict, AnyList, AnySet, Anything]:
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
            raise ValueError(
                f"Invalid schema: {obj}."
                " Consider using it as a schema without wrapping as Any."
            )
    else:
        return AnyUnion(Any(obj) for obj in objs)
