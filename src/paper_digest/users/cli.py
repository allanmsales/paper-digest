"""Creates a user from the command line, e.g. the first admin:

    uv run python -m paper_digest.users.cli admin@example.com --admin --password-stdin
"""

import argparse
import getpass
import sys

from paper_digest.core.db import init_db
from paper_digest.users.store import create_user


def main() -> None:
    parser = argparse.ArgumentParser(description="Create a Paper Digest user.")
    parser.add_argument("email")
    parser.add_argument("--admin", action="store_true")
    parser.add_argument("--password-stdin", action="store_true")
    args = parser.parse_args()

    password = sys.stdin.readline().rstrip("\n") if args.password_stdin else getpass.getpass()
    init_db()
    user = create_user(args.email, password, is_admin=args.admin)
    print(f"Created user {user.email} (admin={user.is_admin})")


if __name__ == "__main__":
    main()
