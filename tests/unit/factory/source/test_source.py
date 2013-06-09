import unittest

from mock import patch, call
from apidoc.factory.source import Source as SourceFactory
from apidoc.object.config import Config as ConfigObject

from apidoc.object.source_raw import Root, Version, Category, Method
from apidoc.object.source_dto import Root as RootDto
from apidoc.object.source_dto import Category as CategoryDto

from apidoc.service.parser import Parser
from apidoc.service.merger import Merger
from apidoc.service.extender import Extender


class TestSource(unittest.TestCase):

    def setUp(self):
        self.source = SourceFactory()

    def test_parser(self):
        self.assertIsInstance(self.source.parser, Parser)

        self.source.parser = "foo"
        self.assertEqual("foo", self.source.parser)

        self.source.parser = None
        self.assertIsInstance(self.source.parser, Parser)

    def test_extender(self):
        self.assertIsInstance(self.source.extender, Extender)

        self.source.extender = "foo"
        self.assertEqual("foo", self.source.extender)

        self.source.extender = None
        self.assertIsInstance(self.source.extender, Extender)

    def test_merger(self):
        self.assertIsInstance(self.source.merger, Merger)

        self.source.merger = "foo"
        self.assertEqual("foo", self.source.merger)

        self.source.merger = None
        self.assertIsInstance(self.source.merger, Merger)

    @patch.object(Parser, "load_from_file", side_effect=[{"e": "f"}, {"g": "h"}])
    @patch.object(Parser, "load_all_from_directory", side_effect=[[{"a": "b"}, {"c": "d"}], [{"z": "y"}]])
    @patch.object(Merger, "merge_sources", return_value={"i": "j"})
    @patch.object(Extender, "extends", return_value={"k": "l"})
    def test_create_from_config(self, mock_extender, mock_merger, mock_parser_directory, mock_parser_file):
        config = ConfigObject()
        config["input"]["directories"] = ["directory1", "directory2"]
        config["input"]["files"] = ["file1", "file2"]
        config["input"]["arguments"] = {"var": "value"}

        response = self.source.create_from_config(config)

        self.assertIsInstance(response, RootDto)

        mock_extender.assert_called_once_with({"i": "j"}, paths=('categories/?', 'versions/?', 'versions/?/methods/?', 'versions/?/types/?', 'versions/?/references/?'))
        mock_merger.assert_called_once_with([{"a": "b"}, {"c": "d"}, {"z": "y"}, {"e": "f"}, {"g": "h"}])
        mock_parser_directory.assert_has_calls([call('directory1'), call('directory2')])
        mock_parser_file.assert_has_calls([call('file1'), call('file2')])

    def test_replace_argument(self):
        root = {
            "a": "${a1}",
            "b": [
                "c",
                "${a1}",
                {
                    "d": "${a1}",
                    "e": "f",
                    "g": 123,
                }
            ],
        }

        response = self.source.replace_argument(root, "a1", "v")
        self.assertEqual({
            "a": "v",
            "b": [
                "c",
                "v",
                {
                    "d": "v",
                    "e": "f",
                    "g": 123,
                }
            ],
        }, response)

    def test_hide_filtered_elements__version(self):
        root = Root()
        version1 = Version()
        version2 = Version()
        version3 = Version()
        version1.name = "v1"
        version2.name = "v2"
        version3.name = "v3"

        root.versions = {"v1": version1, "v2": version2, "v3": version3}

        config = ConfigObject()
        self.source.hide_filtered_elements(root, config["filter"])

        self.assertTrue(version1.display)
        self.assertTrue(version2.display)
        self.assertTrue(version3.display)

    def test_hide_filtered_elements__version_include(self):
        root = Root()
        version1 = Version()
        version2 = Version()
        version3 = Version()
        version1.name = "v1"
        version2.name = "v2"
        version3.name = "v3"

        root.versions = {"v1": version1, "v2": version2, "v3": version3}

        config = ConfigObject()
        config["filter"]["versions"]["includes"] = ["v1", "v3"]
        self.source.hide_filtered_elements(root, config["filter"])

        self.assertTrue(version1.display)
        self.assertFalse(version2.display)
        self.assertTrue(version3.display)

    def test_hide_filtered_elements__version_exclude(self):
        root = Root()
        version1 = Version()
        version2 = Version()
        version3 = Version()
        version1.name = "v1"
        version2.name = "v2"
        version3.name = "v3"

        root.versions = {"v1": version1, "v2": version2, "v3": version3}

        config = ConfigObject()
        config["filter"]["versions"]["excludes"] = ["v1", "v3"]
        self.source.hide_filtered_elements(root, config["filter"])

        self.assertFalse(version1.display)
        self.assertTrue(version2.display)
        self.assertFalse(version3.display)

    def test_hide_filtered_elements__category(self):
        root = Root()
        version1 = Version()

        category1 = Category("c")
        category2 = Category("c")
        category3 = Category("c")
        category1.name = "v1"
        category2.name = "v2"
        category3.name = "v3"

        root.versions = {"v1": version1}
        version1.categories = {"s1": category1, "s2": category2, "s3": category3}

        config = ConfigObject()
        self.source.hide_filtered_elements(root, config["filter"])

        self.assertTrue(category1.display)
        self.assertTrue(category2.display)
        self.assertTrue(category3.display)

    def test_hide_filtered_elements__category_include(self):
        root = Root()

        category1 = Category("c")
        category2 = Category("c")
        category3 = Category("c")
        category1.name = "v1"
        category2.name = "v2"
        category3.name = "v3"

        root.categories = {"s1": category1, "s2": category2, "s3": category3}

        config = ConfigObject()
        config["filter"]["categories"]["includes"] = ["v1", "v3"]
        self.source.hide_filtered_elements(root, config["filter"])

        self.assertTrue(category1.display)
        self.assertFalse(category2.display)
        self.assertTrue(category3.display)

    def test_hide_filtered_elements__category_exclude(self):
        root = Root()

        category1 = Category("c1")
        category2 = Category("c2")
        category3 = Category("c3")

        root.categories = {"c1": category1, "c2": category2, "c3": category3}

        config = ConfigObject()
        config["filter"]["categories"]["excludes"] = ["c1", "c3"]
        self.source.hide_filtered_elements(root, config["filter"])

        self.assertFalse(category1.display)
        self.assertTrue(category2.display)
        self.assertFalse(category3.display)

    def test_remove_hidden_elements(self):
        root = Root()
        version1 = Version()
        version2 = Version()
        category1 = Category("c1")
        category2 = Category("c2")
        method1 = Method()
        method2 = Method()

        root.versions = {"v1": version1, "v2": version2}
        root.categories = {"c1": category1, "c2": category2}

        version1.methods = {"m1": method1, "m2": method2}
        version2.methods = {"m1": method1, "m2": method2}

        method1.category = "c1"
        method2.category = "c2"

        version1.display = False
        category2.display = False

        self.source.remove_hidden_elements(root)

        self.assertEqual(1, len(root.versions))
        self.assertEqual(version2, root.versions["v2"])
        self.assertEqual(1, len(root.versions["v2"].methods))
        self.assertEqual(method1, root.versions["v2"].methods["m1"])

    def test_sort_category_equals(self):
        v1 = CategoryDto(Category("a"))
        v1.order = 1
        v2 = CategoryDto(Category("a"))
        v2.order = 1
        self.assertEqual(v1, v2)

    def test_sort_category_lt(self):
        v1 = CategoryDto(Category("a"))
        v2 = CategoryDto(Category("b"))
        self.assertLess(v1, v2)

    def test_sort_category_lt__on_order(self):
        v1 = CategoryDto(Category("a"))
        v1.order = 1
        v2 = CategoryDto(Category("a"))
        v2.order = 2
        self.assertLess(v1, v2)

    def test_sort_method_equals(self):
        v1 = Method()
        v1.name = "a"
        v2 = Method()
        v2.name = "a"
        self.assertEqual(v1, v2)

    def test_sort_method_lt(self):
        v1 = Method()
        v1.name = "a"
        v2 = Method()
        v2.name = "b"
        self.assertLess(v1, v2)
