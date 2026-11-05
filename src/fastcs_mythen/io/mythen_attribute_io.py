from dataclasses import KW_ONLY, dataclass
from typing import Any

from fastcs.attributes import AttributeIO, AttributeIORef, AttrR, AttrW
from fastcs.datatypes import DType_T
from slsdet import Mythen3

# logger = bind_logger(__name__)


@dataclass
class MythenAttributeIORef(AttributeIORef):
    command_name: str
    _: KW_ONLY
    update_period: float | None = 0.2


class MythenAttributeIO(AttributeIO[DType_T, MythenAttributeIORef]):
    def __init__(self, detector: Mythen3):
        self.detector = detector
        super().__init__()

    async def update(self, attr: AttrR[DType_T, MythenAttributeIORef]):
        value = getattr(self.detector, attr.io_ref.command_name)
        # Messy that this is here, address later
        if attr.io_ref.command_name == "rx_framescaught" and isinstance(value, list):
            if len(value) == 1:
                value = int(value[0])
        await attr.update(value)

    async def send(self, attr: AttrW[DType_T, MythenAttributeIORef], value: Any):
        setattr(self.detector, attr.io_ref.command_name, value)
