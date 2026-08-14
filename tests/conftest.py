from pathlib import Path

import pytest

from umi.config import ProjectConfig, load_project_config
from umi.loading import Dataset, load_dataset

ROOT = Path(__file__).parents[1]


@pytest.fixture(scope="session")
def config() -> ProjectConfig:
    return load_project_config(ROOT / "config")


@pytest.fixture(scope="session")
def synthetic_dataset() -> Dataset:
    return load_dataset(ROOT / "tests" / "fixtures")
