import shlex
import sys

import yaml


def main(path):
    with open(path) as f:
        data = yaml.safe_load(f)
    if not isinstance(data, dict):
        raise SystemExit("{} must be a flat mapping of KEY: value".format(path))
    for key, value in data.items():
        if value is None:
            value = ""
        print("export {}={}".format(key, shlex.quote(str(value))))


if __name__ == "__main__":
    main(sys.argv[1])
