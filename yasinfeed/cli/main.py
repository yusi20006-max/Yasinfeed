import argparse

def main():
    parser = argparse.ArgumentParser(prog="yasinfeed")

    parser.add_argument(
        "command",
        nargs="?",
        default="status",
        choices=["status", "version"],
    )

    args = parser.parse_args()

    if args.command == "status":
        print("YasinFeed status: OK")
    elif args.command == "version":
        print("YasinFeed v0.1")

if __name__ == "__main__":
    main()
