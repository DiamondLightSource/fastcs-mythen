import enum
from dataclasses import KW_ONLY, dataclass

from bidict import bidict
from fastcs.attributes import AttributeIO, AttributeIORef, AttrR, AttrW
from fastcs.logging import bind_logger
from slsdet import Mythen

logger = bind_logger(__name__)

"""Handler for AttrRW using enums, to allow us to map slsdet enums to our own enums.

Args:
enum_mapping: A two-way mapping from a user-friendly StrEnum to the slsdet private
enum.

mapped_enum_type: The enum class which we are using for this attribute.

command_name: Name of the relevant slsdet detector property.

update_period: How often, in seconds, we update the attribute by reading from the
detector

"""


@dataclass
class EnumAttributeIORef(AttributeIORef):
    enum_mapping: bidict[enum.StrEnum, enum.IntEnum]
    mapped_enum_type: type[enum.StrEnum]
    command_name: str
    _: KW_ONLY
    update_period: float | None = 0.2


class EnumAttributeIO(AttributeIO[enum.StrEnum, EnumAttributeIORef]):
    def __init__(self, detector: Mythen):
        self.detector = detector
        super().__init__()

    async def update(self, attr: AttrR[enum.StrEnum, EnumAttributeIORef]):
        raw_enum: enum.IntEnum = getattr(self.detector, attr.io_ref.command_name)
        mapped_enum = attr.io_ref.enum_mapping.inverse[raw_enum]
        await attr.update(mapped_enum)

    async def send(self, attr: AttrW[enum.StrEnum, EnumAttributeIORef], value: str):
        mapped_enum = attr.io_ref.mapped_enum_type(value)
        raw_enum = attr.io_ref.enum_mapping[mapped_enum]
        setattr(self.detector, attr.io_ref.command_name, raw_enum)
