import pytest
import yaml
from conftest import model

from disc_mirror.config import load_config


@pytest.mark.parametrize(
    "change",
    [
        {"extra": 1},
        {"samples": 0},
        {"samples": 1.5},
        {"temperature": "hot"},
        {"budget_usd": "lots"},
        {"judges": [model("a", 10)]},
        {"judges": [dict(model("j", 10), max_tokens="512")]},
    ],
)
def test_load_config_rejects_bad_values(make_config, change):
    path = make_config([model("a", 10)], [model("j", 10)])
    data = yaml.safe_load(path.read_text()) | change
    path.write_text(yaml.safe_dump(data))
    with pytest.raises(ValueError, match="models.yaml"):
        load_config(path)
