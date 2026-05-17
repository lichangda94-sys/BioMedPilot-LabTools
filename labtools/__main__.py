from __future__ import annotations

import argparse

from labtools import __version__, smoke_test


def main() -> int:
    parser = argparse.ArgumentParser(description="BioMedPilot LabTools package.")
    parser.add_argument("--smoke-test", action="store_true", help="Import the public package surface and print a short status summary.")
    args = parser.parse_args()

    if args.smoke_test:
        payload = smoke_test()
        print("labtools smoke test passed")
        print(f"version: {payload['version']}")
        print("modules:")
        for module_name in payload["modules"]:
            print(f"- {module_name}")
        return 0

    parser.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
