import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import yaml
from loguru import logger
from pydantic import Field, ValidationError, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class AppConfig(BaseSettings):
    # 基础配置
    ENV: str = Field("dev")
    LOG_LEVEL: str = Field("DEBUG")
    DEBUG: bool = Field(True)

    # SQLite 数据库配置
    SQLITE_DB_PATH: str = Field("stock_data.db")
    SQLITE_ASYNC_DRIVER: str = Field("sqlite+aiosqlite")
    SQLITE_SYNC_DRIVER: str = Field("sqlite")

    # API配置
    # API_PREFIX: str = Field("/api")
    # API_VERSION: str = Field("v1")
    ALLOWED_ORIGINS: List[str] = ["*"]

    # 文件路径配置
    LOG_DIR: str = Field("logs")
    CONFIG_FILE: Optional[str] = Field("config.yaml")

    # 计算属性：完整的数据库URL
    @property
    def DATABASE_URL(self) -> str:
        return f"{self.SQLITE_ASYNC_DRIVER}:///{self.SQLITE_DB_PATH}"

    @field_validator("SQLITE_DB_PATH")
    @classmethod
    def validate_sqlite_path(cls, v: str) -> str:
        """确保SQLite数据库目录存在"""
        if v:
            db_path = Path(v)
            if db_path.suffix:  # 是文件路径
                db_path.parent.mkdir(parents=True, exist_ok=True)
            else:  # 是目录路径
                db_path.mkdir(parents=True, exist_ok=True)
        return v

    @field_validator("LOG_DIR")
    @classmethod
    def create_log_dir(cls, v: str) -> str:
        """确保日志目录存在"""
        if v:
            Path(v).mkdir(parents=True, exist_ok=True)
        return v

    # Pydantic V2 配置方式
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        env_prefix="",  # 不使用前缀
        extra="ignore",  # 忽略额外字段
    )


def load_config_from_file(file_path: Union[str, Path]) -> Dict[str, Any]:
    """从配置文件加载配置数据"""
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"配置文件不存在: {path}")

    suffix = path.suffix.lower()
    if suffix == ".json":
        return json.loads(path.read_text(encoding="utf-8"))
    elif suffix in (".yaml", ".yml"):
        return yaml.safe_load(path.read_text(encoding="utf-8"))
    elif suffix == ".env":
        # .env 文件由 Pydantic 直接处理
        return {}
    else:
        raise ValueError(f"不支持的配置文件格式: {suffix}")


def merge_configs(configs: List[Dict[str, Any]]) -> Dict[str, Any]:
    """深度合并多个配置字典"""
    merged = {}
    for config in configs:
        for key, value in config.items():
            # 如果值是字典且已存在，则递归合并
            if (
                isinstance(value, dict)
                and key in merged
                and isinstance(merged[key], dict)
            ):
                merged[key] = merge_configs([merged[key], value])
            else:
                merged[key] = value
    return merged


def get_config() -> AppConfig:
    """获取配置实例，支持从文件加载"""
    # 首先尝试从环境变量加载基本配置（包括 CONFIG_FILE 路径）
    try:
        base_config = AppConfig()
    except ValidationError as e:
        print(f"配置验证错误: {e}", file=sys.stderr)
        raise

    # 如果指定了外部配置文件
    if base_config.CONFIG_FILE:
        try:
            file_config = load_config_from_file(base_config.CONFIG_FILE)
            # 合并配置（文件配置优先于环境变量）
            merged_config = {**base_config.model_dump(), **file_config}
            return AppConfig(**merged_config)
        except Exception as e:
            logger.warning(
                f"加载配置文件 {base_config.CONFIG_FILE} 失败: {e} 回退到基本配置"
            )
            return base_config

    return base_config


# 全局配置实例
app_config = get_config()
