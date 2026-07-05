# Copyright 2022 Alex Butler
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from __future__ import annotations

import abc
import logging
import typing as t
from functools import wraps

JSONValue = dict[str, t.Any] | list[t.Any]


class BaseFeatureFlagsClient(abc.ABC):
    """A base client should satisfy these implementations
    and inform the user + README if otherwise. Implementation
    specific logic should go into the __init__ or in private methods"""

    logger = logging.getLogger("dbt_feature_flags")

    def __init__(self) -> None:
        self._add_validators()

    @t.final
    def _add_validators(self) -> None:
        object.__setattr__(
            self, "bool_variation", validate(types=(bool,))(self.bool_variation)
        )
        object.__setattr__(
            self, "string_variation", validate(types=(str,))(self.string_variation)
        )
        object.__setattr__(
            self,
            "number_variation",
            validate(types=(float, int))(self.number_variation),
        )
        object.__setattr__(
            self,
            "json_variation",
            validate(types=(dict, list), default_types=(dict, list, type(None)))(
                self.json_variation
            ),
        )

    @abc.abstractmethod
    def bool_variation(self, flag: str, default: bool = False) -> bool:
        raise NotImplementedError(
            "Boolean feature flags are not implemented for this driver"
        )

    @abc.abstractmethod
    def string_variation(self, flag: str, default: str = "") -> str:
        raise NotImplementedError(
            "String feature flags are not implemented for this driver"
        )

    @abc.abstractmethod
    def number_variation(self, flag: str, default: float | int = 0) -> float | int:
        raise NotImplementedError(
            "Number feature flags are not implemented for this driver"
        )

    @abc.abstractmethod
    def json_variation(self, flag: str, default: JSONValue | None = None) -> JSONValue:
        raise NotImplementedError(
            "JSON feature flags are not implemented for this driver"
        )

    def shutdown(self) -> None:
        """Release provider resources after one-shot callers finish."""


def validate(
    types: tuple[type[t.Any], ...],
    default_types: tuple[type[t.Any], ...] | None = None,
) -> t.Callable[[t.Any], t.Any]:
    valid_default_types = default_types or types

    def _validate(v: t.Any, flag_name: str, func_name: str) -> t.Any:
        if not isinstance(v, tuple(types)):
            raise ValueError(
                f"Invalid return value for {func_name}({flag_name}...) feature flag call. Found type {type(v).__name__}."
            )
        return v

    def _main(func: t.Any) -> t.Any:
        default_value = func.__defaults__[0] if func.__defaults__ else None

        @wraps(func)
        def _injected_validator(flag: str, default: t.Any = default_value) -> t.Any:
            if not isinstance(default, valid_default_types):
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
