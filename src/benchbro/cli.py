# src/benchbro/cli.py
import webbrowser
import uvicorn
from benchbro.config import Config


def main():
    config = Config()
    url = f"http://{config.host}:{config.port}"
    print(f"\n  BenchBro v0.1.0")
    print(f"  Running at {url}")
    print(f"  Data directory: {config.data_dir}\n")
    webbrowser.open(url)
    uvicorn.run("benchbro.app:create_app", factory=True, host=config.host, port=config.port, log_level="warning")


if __name__ == "__main__":
    main()
