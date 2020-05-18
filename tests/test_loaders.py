import pytest

from feeds.loaders import build_tree, flatten_tree, serialize_tree
from .utils import load_file, load_fixtures


@pytest.mark.parametrize("in_html_file,out_html_file", load_fixtures("flatten_tree"))
def test_flatten_tree(in_html_file, out_html_file):
    tree = build_tree(load_file(in_html_file))[0]
    flatten_tree(tree)
    assert serialize_tree(tree) == load_file(out_html_file)
