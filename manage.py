import argparse

from app import create_app


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run the local development server.")
    parser.add_argument("command", nargs="?", default="runserver", choices=["runserver"])
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=5000)
    parser.add_argument("--debug", action="store_true")
    args = parser.parse_args()
    create_app().run(host=args.host, port=args.port, debug=args.debug)
