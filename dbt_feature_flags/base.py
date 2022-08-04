import abc
import logging
from functools import wraps
from typing import Any, Union, final


class BaseFeatureFlagsClient(abc.ABC):
    """A base client should satisfy these implementations
    and inform the user + README if otherwise. Implementation
    specific logic should go into the __init__ or in private methods"""

    logger = logging.getLogger("dbt_feature_flags")

    def __init__(self) -> None:
        self._add_validators()

    @final
    def _add_validators(self):
        self.bool_variation = validate(types=(bool,))(self.bool_variation)
        self.string_variation = validate(types=(str,))(self.string_variation)
        self.number_variation = validate(types=(float, int))(self.number_variation)
        self.json_variation = validate(types=(dict, list, None))(self.json_variation)

    @abc.abstractmethod
    def bool_variation(self, flag: str, default: Any) -> bool:
        raise NotImplementedError(
            "Boolean feature flags are not implemented for this driver"
        )

    @abc.abstractmethod
    def string_variation(self, flag: str, default: Any) -> str:
        raise NotImplementedError(
            "String feature flags are not implemented for this driver"
        )

    @abc.abstractmethod
    def number_variation(self, flag: str, default: Any) -> Union[float, int]:
        raise NotImplementedError(
            "Number feature flags are not implemented for this driver"
        )

    @abc.abstractmethod
    def json_variation(self, flag: str, default: Any) -> Union[dict, list]:
        raise NotImplementedError(
            "JSON feature flags are not implemented for this driver"
        )


def validate(types: Union[list, tuple]):
    def _validate(v, flag_name, func_name):
        if not isinstance(v, types):
            raise ValueError(
                f"Invalid return value for {func_name}({flag_name}...) feature flag call. Found type {type(v).__name__}."
            )
        return v

    def _main(func):
        @wraps(func)
        def _injected_validator(flag: str, default: Any = func.__defaults__[0]):
            if not isinstance(default, types):
                raise ValueError(
                    f"Invalid default value: {default} for {func.__name__}({flag}...) feature flag call. Found type {type(default).__name__}."
                )
            try:
                return _validate(func(flag, default), flag, func.__name__)
            except ValueError as exc:
                raise ValueError(
                    f"Invalid feature flag evaluation {func.__name__}({flag}...). Ensure the correct feature_flag_* function was used. Err: {exc}"
                ) from exc

        return _injected_validator

    return _main
