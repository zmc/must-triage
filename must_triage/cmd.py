import argparse
import json
import os

from must_triage import inspectors


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('path', type=dir_or_file)
    return parser.parse_args()


def dir_or_file(path):
    result = os.path.expanduser(path)
    if os.path.isdir(result) or os.path.isfile(result):
        return result
    raise argparse.ArgumentTypeError(f"{path} is not a valid path!")


def main():
    args = parse_args()
    interests = dict()
    for inspector_cls in inspectors.all():
        inspector = inspector_cls(root=args.path)
        inspectors.merge_interests(interests, inspector.inspect())

    print(json.dumps(interests, indent=2))
