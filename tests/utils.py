from glob import glob


def load_file(filename):
    with open(filename) as f:
        return f.read().strip()


def load_fixtures(test_name):
    path = "tests/fixtures/{test_name}/*.{direction}.html"
    in_files = sorted(glob(path.format(test_name=test_name, direction="in")))
    out_files = sorted(glob(path.format(test_name=test_name, direction="out")))
    return zip(in_files, out_files)
