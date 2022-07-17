from __future__ import annotations

import json
import typing as t


class JSONValidator:
    pass

    @classmethod
    def validate(cls, schema, j):
        return schema == j


class AnyBase:
    def eq(self, other) -> bool:
        pass

    def __eq__(self, other):
        return self.eq(other)

    def __req__(self, other):
        return self.eq(other)


class AnyDict(AnyBase):
    def __init__(self, d) -> None:
        self.required_dict = d

    def eq(self, other) -> bool:
        if not isinstance(other, dict):
            return False
        for k, v in self.required_dict.items():
            if k not in other:
                return False
            if other[k] != v:
                return False
        return True


class AnyList(AnyBase):
    def __init__(self, d) -> None:
        self.required_list = d

    def eq(self, other) -> bool:
        if not isinstance(other, list):
            return False
        for x in self.required_list:
            if x not in other:
                return False
        return True


class AnyType(AnyBase):
    def __init__(self, d: t.Union[int, float, bool, str, dict, list]) -> None:
        self.type_ = d

    def eq(self, other) -> bool:
        if isinstance(other, bool) and self.type_ is int:
            return False
        return isinstance(other, self.type_)

    def __repr__(self):
        return "Any{}".format(self.type_.__name__.capitalize())


class AnyUnion(AnyBase):
    def __init__(self, objs):
        self.objs = []
        for obj in objs:
            if obj in [int, float, bool, str, dict, list]:
                self.objs.append(AnyType(obj))
            elif type(obj) is dict:
                self.objs.append(AnyDict(obj))
            elif type(obj) is list:
                self.objs.append(AnyList(obj))
            else:
                self.objs.append(obj)

    def __repr__(self):
        if len(self.objs) == 1:
            return repr(self.objs[0])
        objs_repr = map(repr, self.objs)
        return "<AnyUnion {}>".format(" | ".join(objs_repr))

    def eq(self, other):
        print(1, self, other)
        return any(obj == other for obj in self.objs)


class Any(AnyBase):
    def __init__(self, *objs):
        if len(objs) == 0:
            self.obj = None
        else:
            self.obj = AnyUnion(objs)

    def eq(self, other) -> bool:
        return True if self.obj is None else self.obj.eq(other)


