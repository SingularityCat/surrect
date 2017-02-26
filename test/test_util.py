from unittest import TestCase

from surrect.util import *


class TestPathAttributes(TestCase):
    def test_no_dict(self):
        path = "foo/bar/baz.quux"
        d = path_attributes(path)

        self.assertEqual(d["path"], path, "path wrong")
        self.assertEqual(d["dir"], "foo/bar/", "dir wrong")
        self.assertEqual(d["filename"], "baz.quux", "filename wrong")
        self.assertEqual(d["filebase"], "baz", "filebase wrong")
        self.assertEqual(d["fileext"], ".quux", "fileext wrong")

    def test_with_dict(self):
        path = "/a/b/c/d/e.f"
        d = {"alpha": 1, "beta": 2, "path": "should_be_overwritten"}
        path_attributes(path, d)

        self.assertEqual(d["alpha"], 1)
        self.assertEqual(d["beta"], 2)
        self.assertEqual(d["path"], path, "path wrong")
        self.assertEqual(d["dir"], "/a/b/c/d/", "dir wrong")
        self.assertEqual(d["filename"], "e.f", "filename wrong")
        self.assertEqual(d["filebase"], "e", "filebase wrong")
        self.assertEqual(d["fileext"], ".f", "fileext wrong")


class TestBraceExpand(TestCase):
    def test_simple_expansion(self):
        compact = "foo-{1,2,3}"
        expanded = brace_expand(compact)
        self.assertEqual(len(expanded), 3)
        self.assertEqual(expanded[0], "foo-1")
        self.assertEqual(expanded[1], "foo-2")
        self.assertEqual(expanded[2], "foo-3")
