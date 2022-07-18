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

    def test_without_any(self) -> None:
        self.assertTrue(JsonValidator([1, 2, 3]).validate([1, 2, 3]))

    def test_any(self) -> None:
        self.assertTrue(JsonValidator(Any()).validate(""))
        self.assertTrue(JsonValidator(Any()).validate(1))
        self.assertTrue(JsonValidator(Any()).validate({"foo": "bar", "xyz": 123}))

    def test_any_dict(self) -> None:
        self.assertTrue(JsonValidator(Any({})).validate({}))
        self.assertTrue(JsonValidator(Any({})).validate({"a": 1, "b": 2}))
        self.assertFalse(JsonValidator(Any({"a": Any(str)})).validate({"a": 1, "b": 2}))

        self.assertFalse(JsonValidator(Any({})).validate(""))
        self.assertTrue(JsonValidator(Any({})).validate({"a": 1, "b": 2}))

        # invalid schema object for Any
        with self.assertRaises(ValueError):
            JsonValidator(Any(3)).validate({})

    def test_any_list(self) -> None:
        self.assertTrue(JsonValidator(Any([1, 2])).validate([1, 2]))
        self.assertTrue(JsonValidator(Any([1, 2])).validate([1, 2, 3]))
        self.assertFalse(JsonValidator(Any([1, 2])).validate([2, 1]))
        self.assertTrue(JsonValidator(Any([1, 2, Any(str)])).validate([1, 2, "d"]))

    def test_any_set(self) -> None:
        self.assertTrue(JsonValidator(Any({1, 2, Any(str)})).validate([1, 2, 3, "4"]))
