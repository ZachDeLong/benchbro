# src/benchbro/config.py
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class Config:
    data_dir: Path = field(default_factory=lambda: Path.home() / ".benchbro")
    db_path: Path = field(default=None)
    host: str = "127.0.0.1"
    port: int = 7853
    datasets_dir: Path = field(default=None)

    def __post_init__(self):
        if self.db_path is None:
            self.db_path = self.data_dir / "data.db"
        if self.datasets_dir is None:
            self.datasets_dir = self.data_dir / "datasets"
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.datasets_dir.mkdir(parents=True, exist_ok=True)
