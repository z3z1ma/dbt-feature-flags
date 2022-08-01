import abc
from typing import Union


class BaseFeatureFlagsClient(abc.ABC):
    """A base client should satisfy these implementations
    and inform the user + README if otherwise. Implementation
    specific logic should go into the __init__ or in private methods"""

    @abc.abstractmethod
    def bool_variation(self, flag: str) -> bool:
        raise NotImplementedError(
            "Boolean feature flags are not implemented for this driver"
        )

    @abc.abstractmethod
    def string_variation(self, flag: str) -> str:
        raise NotImplementedError(
            "String feature flags are not implemented for this driver"
        )

    @abc.abstractmethod
    def number_variation(self, flag: str) -> Union[float, int]:
        raise NotImplementedError(
            "Number feature flags are not implemented for this driver"
        )

    @abc.abstractmethod
    def json_variation(self, flag: str) -> Union[dict, list]:
        raise NotImplementedError(
            "JSON feature flags are not implemented for this driver"
        )
