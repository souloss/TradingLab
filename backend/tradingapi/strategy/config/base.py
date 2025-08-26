"""
配置系统基础定义
包含基础配置类和通用方法
"""

from dataclasses import asdict, dataclass, fields
from typing import Any, Dict, Type, TypeVar, Union, get_args, get_origin, get_type_hints

from ..exceptions import ConfigurationError

T = TypeVar("T", bound="BaseConfig")


def is_type_compatible(value: Any, expected_type: Type) -> bool:
    """检查值是否与期望的类型兼容"""
    # 处理 Optional 类型
    if get_origin(expected_type) is Union:
        # 如果是 Optional[T]，检查值是否为 None 或与 T 兼容
        type_args = get_args(expected_type)
        if value is None and type(None) in type_args:
            return True
        # 检查值是否与任何类型参数兼容
        return any(
            is_type_compatible(value, arg) for arg in type_args if arg is not type(None)
        )

    # 处理 List 类型
    if get_origin(expected_type) is list:
        if not isinstance(value, list):
            return False
        type_args = get_args(expected_type)
        if type_args:
            # 检查列表中的每个元素是否与类型参数兼容
            return all(is_type_compatible(item, type_args[0]) for item in value)
        return True

    # 处理 Dict 类型
    if get_origin(expected_type) is dict:
        if not isinstance(value, dict):
            return False
        type_args = get_args(expected_type)
        if len(type_args) == 2:
            # 检查字典中的每个键值对是否与类型参数兼容
            key_type, value_type = type_args
            return all(
                is_type_compatible(k, key_type) and is_type_compatible(v, value_type)
                for k, v in value.items()
            )
        return True

    # 基本类型检查
    try:
        if isinstance(value, expected_type):
            return True

        # 尝试类型转换
        if expected_type is int and isinstance(value, float) and value.is_integer():
            return True
        if expected_type is float and isinstance(value, (int, float)):
            return True

        return False
    except:
        return False


@dataclass
class BaseConfig:
    """所有配置类的基类"""

    def validate(self) -> None:
        """验证配置参数的有效性"""

    @classmethod
    def from_dict(cls: Type[T], config_dict: Dict[str, Any]) -> T:
        """从字典创建配置对象，过滤未知字段并检查类型"""
        if not config_dict:
            return cls()

        type_hints = get_type_hints(cls)
        valid_fields = {f.name for f in fields(cls)}

        filtered_dict = {}
        type_errors = []

        for field_name, field_value in config_dict.items():
            if field_name in valid_fields:
                expected_type = type_hints.get(field_name, Any)

                # === fixed：如果字段是 BaseConfig 子类，且传入的是 dict，就递归构造 ===
                if isinstance(expected_type, type) and issubclass(
                    expected_type, BaseConfig
                ):
                    if isinstance(field_value, dict):
                        filtered_dict[field_name] = expected_type.from_dict(field_value)
                        continue
                    elif isinstance(field_value, expected_type):
                        filtered_dict[field_name] = field_value
                        continue
                    else:
                        type_errors.append(
                            f"Field '{field_name}': expected {expected_type}, got {type(field_value)}"
                        )
                        continue

                # 普通类型检查
                if not is_type_compatible(field_value, expected_type):
                    type_errors.append(
                        f"Field '{field_name}': expected {expected_type}, got {type(field_value)}"
                    )
                filtered_dict[field_name] = field_value

        if type_errors:
            error_msg = "; ".join(type_errors)
            raise ConfigurationError(
                f"Invalid configuration for {cls.__name__}: {error_msg}"
            )

        try:
            return cls(**filtered_dict)
        except TypeError as e:
            raise ConfigurationError(f"Invalid configuration for {cls.__name__}: {e}")

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return asdict(self)

    def update(self, config_dict: Dict[str, Any]) -> None:
        """更新配置参数"""
        current_dict = self.to_dict()
        current_dict.update(config_dict)
        updated_config = self.from_dict(current_dict)
        for field_name, field_value in updated_config.__dict__.items():
            setattr(self, field_name, field_value)
        self.validate()
