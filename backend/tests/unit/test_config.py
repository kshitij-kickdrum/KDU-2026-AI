from pathlib import Path

from src.utils.config import ConfigManager


def test_config_validate_and_reload(tmp_path: Path) -> None:
    cfg_file = tmp_path / "config.yaml"
    cfg_file.write_text(
        "chunking:\n  min_chunk_size: 100\n  max_chunk_size: 600\n  chunk_overlap: 50\nsearch:\n  semantic_weight: 0.6\n  keyword_weight: 0.4\n",
        encoding="utf-8",
    )
    cfg = ConfigManager(cfg_file)
    assert cfg.validate() == []
    cfg.update("search.semantic_weight", 0.0)
    cfg.update("search.keyword_weight", 0.0)
    assert cfg.validate()
