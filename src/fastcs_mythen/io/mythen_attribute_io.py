from dataclasses import KW_ONLY, dataclass
from typing import Any

from fastcs.attributes import AttributeIO, AttributeIORef, AttrR, AttrW
from fastcs.datatypes import DType_T
from fastcs.logging import bind_logger
from slsdet import Mythen

logger = bind_logger(__name__)


@dataclass
class MythenAttributeIORef(AttributeIORef):
    command_name: str
    _: KW_ONLY
    update_period: float | None = 0.2


class MythenAttributeIO(AttributeIO[DType_T, MythenAttributeIORef]):
    def __init__(self, detector: Mythen):
        self.detector = detector
        super().__init__()

    async def update(self, attr: AttrR[DType_T, MythenAttributeIORef]):
        await attr.update(getattr(self.detector, attr.io_ref.command_name))

    async def send(self, attr: AttrW[DType_T, MythenAttributeIORef], value: Any):
        setattr(self.detector, attr.io_ref.command_name, value)
