import argparse
import os
import shutil
from pathlib import Path

try:
    from django.core.management.utils import get_random_secret_key
except Exception:
    # Fallback if Django import fails
    import secrets

    def get_random_secret_key() -> str:
        return secrets.token_urlsafe(50)


def generate_key() -> str:
    return get_random_secret_key()


def update_env_file(env_path: Path, secret_key: str) -> None:
    env_path = env_path.resolve()
    if env_path.exists():
        backup_path = env_path.with_suffix(env_path.suffix + ".bak")
        shutil.copyfile(env_path, backup_path)

        with env_path.open("r", encoding="utf-8") as f:
            lines = f.readlines()

        updated = False
        for i, line in enumerate(lines):
            if line.strip().startswith("SECRET_KEY="):
                lines[i] = f"SECRET_KEY={secret_key}\n"
                updated = True
                break

        if not updated:
            if lines and not lines[-1].endswith("\n"):
                lines[-1] += "\n"
            lines.append(f"SECRET_KEY={secret_key}\n")

        with env_path.open("w", encoding="utf-8") as f:
            f.writelines(lines)
    else:
        env_path.parent.mkdir(parents=True, exist_ok=True)
        with env_path.open("w", encoding="utf-8") as f:
            f.write(f"SECRET_KEY={secret_key}\n")


def main():
    parser = argparse.ArgumentParser(description="Generate a Django SECRET_KEY and optionally update an env file.")
    parser.add_argument("--print", action="store_true", help="Print the generated key to stdout.")
    parser.add_argument("--env", type=str, default=".env", help="Path to env file to update (default: .env).")
    parser.add_argument("--no-update", action="store_true", help="Do not update any env file; only generate/print.")
    args = parser.parse_args()

    key = generate_key()

    if args.print or args.no_update:
        print(key)

    if not args.no_update:
        env_file = Path(args.env)
        update_env_file(env_file, key)
        print(f"Updated SECRET_KEY in {env_file}")


if __name__ == "__main__":
    main()


