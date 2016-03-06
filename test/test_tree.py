import unittest
from unittest import TestCase
from summon.tree import *


class TestNodeMethods(TestCase):
    def test_init(self):
        v = object()
        n = Node(NODE_ROOT, v)
        self.assertEqual(n.kind, NODE_ROOT)
        self.assertIs(n.value, v)
        self.assertRaises(NodeError, Node, "random", "foo")

    def test_eq(self):
        a = Node(NODE_TEXT, "hello!")
        b = Node(NODE_TEXT, "hello!")
        self.assertTrue(a == b)

    def test_copy(self):
        a = Node(NODE_TEXT, "hello!")
        a.nodes.append(Node(NODE_TEXT, "I'm a node!"))
        a.nodes.append(Node(NODE_BLANK, None))
        b = a.copy()
        self.assertIsNot(a, b)
        self.assertIs(a.kind, b.kind)
        self.assertIs(a.value, b.value)
        self.assertIsNot(a.nodes, b.nodes)
        self.assertEqual(a.nodes, b.nodes)
        for n in range(0, len(a.nodes)):
            self.assertIs(a.nodes[n], b.nodes[n])

    def test_deepcopy(self):
        a = Node(NODE_TEXT, "hello!")
        a.nodes.append(Node(NODE_TEXT, "I'm a node!"))
        a.nodes.append(Node(NODE_BLANK, None))
        b = a.deepcopy()
        self.assertIsNot(a, b)
        self.assertIs(a.kind, b.kind)
        self.assertIs(a.value, b.value)
        self.assertIsNot(a.nodes, b.nodes)
        self.assertEqual(a.nodes, b.nodes)
        for n in range(0, len(a.nodes)):
            self.assertIsNot(a.nodes[n], b.nodes[n])
            self.assertEqual(a.nodes[n], b.nodes[n])
