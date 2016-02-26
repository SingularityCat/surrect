from sys import path

from .scroll import Node

runes = {}


def rune(runeid, registry=runes):
    def regrune(runefunc):
        registry[runeid] = runefunc
    return regrune


def load(fpath):
    with open(fpath, "r") as src:
        runescope = {
            "rune": rune
        }
        code = compile(src.read(), fpath, "exec",)
        exec(code, runescope)


def collect_nodes(first, gen):
    collected = [first]
    tail = None
    for node in gen:
        if node.kind is not first.kind:
            tail = node
            break
        else:
            collected.append(node)
    return collected, tail


default_collators = {
    Node.text:  (" ", lambda n: n.strip()),
    Node.raw:   ("\n", lambda n: n)
}


def collate(nodelist, collators=default_collators):
    """Node collator."""
    collated_nodes = []

    nodegen = iter(nodelist)

    try:
        node = next(nodegen)
        while True:
            if node is not None and node.kind in collators:
                adjns, next_node = collect_nodes(node, nodegen)
                jc, fn = collators[node.kind]
                node.value = jc.join(fn(n.value) for n in adjns)
            else:
                next_node = next(nodegen)
            collated_nodes.append(node)
            node = next_node
    except StopIteration:
        pass

    return collated_nodes
