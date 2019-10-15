import argparse
import json
import os
import yaml

from must_triage import formatters
from must_triage import inspectors
from must_triage.progress import ProgressBar


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('path', type=dir_or_file)
    parser.add_argument('-q', '--quiet', action='store_true')
    parser.add_argument(
            '-o', '--out', choices=['json', 'yaml'], default='json')
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
        inspector_args = dict(root=args.path)
        if not args.quiet:
            inspector_args['progress_class'] = ProgressBar
        inspector = inspector_cls(**inspector_args)
        inspectors.merge_interests(interests, inspector.inspect())

    if args.out == 'json':
        print(json.dumps(
            interests, indent=2, default=formatters.json_serialize))
    elif args.out == 'yaml':
        print(yaml.safe_dump(interests, default_flow_style=False))
