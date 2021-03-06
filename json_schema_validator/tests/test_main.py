import unittest

from json_schema_validator.main import Any, JsonValidator


class JsonSchemaValidatorTest(unittest.TestCase):
    def test_common_usage(self) -> None:
        schema = Any(
            {
                "a_string": Any(str),
                "a_list": Any(list),
                "exact_str": "xxx",
                "some_dict": Any({1: 1}),
                "a_union": Any(int, list),
            }
        )
        self.assertTrue(
            JsonValidator(schema).validate(
                {
                    "a_string": "abc",
                    "a_list": [1, 2],
                    "exact_str": "xxx",
                    "some_dict": {1: 1},
                    "a_union": 0,
                }
            )
        )
        self.assertTrue(
            JsonValidator(schema).validate(
                {
                    "a_string": "abc",
                    "a_list": [1, 2, 3],
                    "exact_str": "xxx",
                    "some_dict": {1: 1, 2: 2},
                    "a_union": [0],
                }
            )
        )
        # missing field
        self.assertFalse(
            JsonValidator(schema).validate(
                {
                    "a_string": "abc",
                }
            )
        )
        # union not match
        self.assertFalse(
            JsonValidator(schema).validate(
                {
                    "a_string": "abc",
                    "a_list": [1, 2, 3],
                    "exact_str": "xxx",
                    "some_dict": {1: 1, 2: 2},
                    "a_union": "zzz",
                }
            )
        )

    def test_common_usage_2(self) -> None:
        schema_1 = Any({...: Any({"a": Any(int)})})
        self.assertTrue(
            JsonValidator(schema_1).validate(
                {"l1": {"a": 1}, "l2": {"a": 2, "b": 22}, "l3": {"a": 3}}
            )
        )
        self.assertFalse(
            JsonValidator(schema_1).validate({"l1": {"a": "1"}, "l2": {"a": 11}})
        )

        schema_2 = Any([Any(int), ...])
        self.assertTrue(JsonValidator(schema_2).validate([1, 2, 3]))
        self.assertFalse(JsonValidator(schema_2).validate([1, 2, "3"]))

    def test_without_any(self) -> None:
        self.assertTrue(JsonValidator([1, 2, 3]).validate([1, 2, 3]))

    def test_any(self) -> None:
        self.assertTrue(JsonValidator(Any()).validate(""))
        self.assertTrue(JsonValidator(Any()).validate(1))
        self.assertTrue(JsonValidator(Any()).validate({"foo": "bar", "xyz": 123}))
        self.assertIs(Any(3), 3)

    def test_any_dict(self) -> None:
        self.assertTrue(JsonValidator(Any({})).validate({}))
        self.assertTrue(JsonValidator(Any({})).validate({"a": 1, "b": 2}))
        self.assertFalse(JsonValidator(Any({"a": Any(str)})).validate({"a": 1, "b": 2}))

        self.assertFalse(JsonValidator(Any({})).validate(""))
        self.assertTrue(JsonValidator(Any({})).validate({"a": 1, "b": 2}))

        self.assertTrue(
            JsonValidator(Any({...: Any(str)})).validate({"a": "aaa", "b": "bbb"})
        )
        self.assertFalse(
            JsonValidator(Any({...: Any(str)})).validate({"a": "aaa", "b": 333})
        )

    def test_any_list(self) -> None:
        self.assertTrue(JsonValidator(Any([1, 2])).validate([1, 2]))
        self.assertTrue(JsonValidator(Any([1, 2])).validate([1, 2, 3]))
        self.assertFalse(JsonValidator(Any([1, 2])).validate([2, 1]))
        self.assertTrue(JsonValidator(Any([1, 2, Any(str)])).validate([1, 2, "d"]))

        self.assertTrue(JsonValidator(Any([Any(int), ...])).validate([1, 2, 3]))
        self.assertFalse(JsonValidator(Any([Any(int), ...])).validate([1, "2", 3]))

    def test_any_set(self) -> None:
        self.assertTrue(JsonValidator(Any({1, 2, Any(str)})).validate([1, 2, 3, "4"]))

    def test_any_union(self) -> None:
        self.assertTrue(JsonValidator(Any(bool, "success", "fail")).validate(True))
        self.assertTrue(JsonValidator(Any(bool, "success", "fail")).validate("success"))
        self.assertFalse(JsonValidator(Any(bool, "success", "fail")).validate(1))

        self.assertTrue(JsonValidator(Any(bool) | "success" | "fail").validate(True))

    def test_xx(self) -> None:
        a = Any({"results": Any(bool, "success")})
        repr(a)
        print()
