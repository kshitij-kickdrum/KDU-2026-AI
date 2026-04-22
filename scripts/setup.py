from pathlib import Path
import shutil


ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    env_target = ROOT / ".env"
    env_example = ROOT / "config" / ".env.example"
    if not env_target.exists():
        shutil.copy(env_example, env_target)
        print("Created .env from config/.env.example")
    else:
        print(".env already exists")

    (ROOT / "data").mkdir(exist_ok=True)
    print("Ensured data directory exists")


if __name__ == "__main__":
    main()

