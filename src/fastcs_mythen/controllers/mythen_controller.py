import enum

from bidict import bidict
from fastcs.attributes import AttrR, AttrRW, AttrW
from fastcs.controllers.controller import Controller
from fastcs.datatypes import Enum, Float, Int, String
from fastcs.methods import command, scan
from slsdet import Mythen3, defs

from fastcs_mythen.io.enum_attribute_io import EnumAttributeIO, EnumAttributeIORef
from fastcs_mythen.io.mythen_attribute_io import (
    MythenAttributeIO,
    MythenAttributeIORef,
)
from fastcs_mythen.io.temperature_attribute_io import (
    TemperatureAttributeIO,
    TemperatureAttributeIORef,
)

TimingMode: enum.IntEnum = defs.timingMode
RunStatus: enum.IntEnum = defs.runStatus


class DetectorStatus(enum.StrEnum):
    Idle = "Idle"
    Error = "Error"
    Waiting = "Waiting"
    RunFinished = "Run Finished"
    Transmitting = "Transmitting"
    Running = "Running"
    Stopped = "Stopped"


class TriggerMode(enum.StrEnum):
    Auto = "Auto Timing"
    Trigger = "Trigger Exposure"
    Gating = "Gating"
    Trigger_Gating = "Trigger Gating"


TRIGGER_MODE_ENUM_MAPPING: bidict[enum.StrEnum, enum.IntEnum] = bidict(
    {
        TriggerMode.Auto: TimingMode.AUTO_TIMING,  # type: ignore
        TriggerMode.Trigger: TimingMode.TRIGGER_EXPOSURE,  # type: ignore
        TriggerMode.Gating: TimingMode.GATED,  # type: ignore
        TriggerMode.Trigger_Gating: TimingMode.TRIGGER_GATED,  # type: ignore
    }
)

DETECTOR_STATUS_MAPPING: bidict[enum.StrEnum, enum.IntEnum] = bidict(
    {
        DetectorStatus.Idle: RunStatus.IDLE,  # type: ignore
        DetectorStatus.Error: RunStatus.ERROR,  # type: ignore
        DetectorStatus.Waiting: RunStatus.WAITING,  # type: ignore
        DetectorStatus.RunFinished: RunStatus.RUN_FINISHED,  # type: ignore
        DetectorStatus.Transmitting: RunStatus.TRANSMITTING,  # type: ignore
        DetectorStatus.Running: RunStatus.RUNNING,  # type: ignore
        DetectorStatus.Stopped: RunStatus.STOPPED,  # type: ignore
    }
)


class MythenController(Controller):
    HARDWARE_DETAILS = "HardwareDetails"
    SOFTWARE_DETAILS = "SoftwareDetails"
    ACQUISITION = "Acquisition"
    TEMPERATURE = "Temperature"
    STATUS = "Status"
    POWER = "Power"

    firmware_version = AttrR(
        String(),
        io_ref=MythenAttributeIORef("firmwareversion"),
        group=SOFTWARE_DETAILS,
    )

    detector_server_version = AttrR(
        String(),
        io_ref=MythenAttributeIORef("detectorserverversion"),
        group=SOFTWARE_DETAILS,
    )
    # Read Only Attributes
    hardware_version = AttrR(
        String(),
        io_ref=MythenAttributeIORef("hardwareversion"),
        group=HARDWARE_DETAILS,
    )
    # This gives a list really but string will do for now
    hostname = AttrR(
        String(1000),
        io_ref=MythenAttributeIORef("hostname"),
        group=HARDWARE_DETAILS,
    )
    kernel_version = AttrR(
        String(), io_ref=MythenAttributeIORef("kernelversion"), group=SOFTWARE_DETAILS
    )
    client_version = AttrR(
        String(), io_ref=MythenAttributeIORef("clientversion"), group=SOFTWARE_DETAILS
    )
    receiver_version = AttrR(
        String(), io_ref=MythenAttributeIORef("rx_version"), group=SOFTWARE_DETAILS
    )
    frames_left = AttrR(String(), io_ref=MythenAttributeIORef("framesl"), group=STATUS)

    module_geometry = AttrR(String(), group=HARDWARE_DETAILS)
    module_size = AttrR(String(), group=HARDWARE_DETAILS)
    detector_size = AttrR(String(), group=HARDWARE_DETAILS)

    detector_status = AttrR(
        Enum(DetectorStatus),
        io_ref=EnumAttributeIORef(DETECTOR_STATUS_MAPPING, DetectorStatus, "status"),
        group=STATUS,
    )

    frames_written = AttrR(
        Int(),
        io_ref=MythenAttributeIORef("rx_framescaught"),
        group=ACQUISITION,
    )

    # Read/Write Attributes
    # Failing as hardware returns `[7500, 7500, 7500]` not a float
    # threshold = AttrRW(
    #     Float(units="eV"),
    #     io_ref=MythenAttributeIORef("threshold"),
    #     group=ACQUISITION,
    # )
    exposure_time = AttrRW(
        Float(units="s", prec=3),
        io_ref=MythenAttributeIORef("exptime"),
        group=ACQUISITION,
    )
    period_between_frames = AttrRW(
        Float(units="s", prec=3),
        io_ref=MythenAttributeIORef("period"),
        group=ACQUISITION,
    )
    delay_after_trigger = AttrRW(
        Float(units="s", prec=3),
        io_ref=MythenAttributeIORef("delay"),
        group=ACQUISITION,
    )
    frames_per_acq = AttrRW(
        Int(), io_ref=MythenAttributeIORef("frames"), group=ACQUISITION
    )
    high_voltage = AttrRW(
        Int(units="V"),
        io_ref=MythenAttributeIORef("highvoltage"),
        group=POWER,
    )

    # Should be read/write but for some reason it occassionally returns a list of triggers when reading
    trigger_mode = AttrW(
        Enum(TriggerMode),
        io_ref=EnumAttributeIORef(TRIGGER_MODE_ENUM_MAPPING, TriggerMode, "timing"),
        group=ACQUISITION,
    )

    file_path = AttrRW(
        String(),
        io_ref=MythenAttributeIORef("fpath"),
        group=ACQUISITION,
    )

    file_name = AttrRW(
        String(),
        io_ref=MythenAttributeIORef("fname"),
        group=ACQUISITION,
    )

    def __init__(self, config_file_path) -> None:
        # Create a Mythen detector object
        # and initialise it with a config file
        self.detector = Mythen3()
        self.detector.config = config_file_path

        super().__init__(
            ios=[
                MythenAttributeIO(self.detector),
                EnumAttributeIO(self.detector),
                TemperatureAttributeIO(self.detector),
            ]
        )

    async def initialise(self):
        # Get the list of temperatures
        temperature_list = self.detector.getTemperatureList()

        # Determine the number of modules
        module_geometry = self.detector.module_geometry
        number_of_modules = module_geometry.x * module_geometry.y

        # Create a TemperatureHandler for each module temperature
        # sensor and group them under their list index
        for temperature_index in temperature_list:
            # Go from dacIndex.TEMPERATURE_ADC to ADC, for example
            prefix = str(temperature_index).split("_")[1].upper()
            for module_index in range(number_of_modules):
                group_name = f"{prefix}Temperatures"
                self.add_attribute(
                    f"{group_name}Module{module_index + 1}",
                    AttrR(
                        Int(units="\u00b0C"),
                        io_ref=TemperatureAttributeIORef(
                            module_index, temperature_index
                        ),
                        group=group_name,
                    ),
                )

    # Once initialisation is complete, fetch the module and detector geometry
    async def connect(self):
        detector_size = self.detector.detsize
        module_size = self.detector.module_size
        module_geometry = self.detector.module_geometry
        await self.detector_size.update(f"{detector_size.x} by {detector_size.y}")
        await self.module_geometry.update(
            f"{module_geometry.x} wide by {module_geometry.y} high"
        )
        await self.module_size.update(f"{module_size[0]} by {module_size[1]}")
        await super().connect()
        await self.file_name.put("test")

    @scan(0.2)
    async def update_temperatures(self):
        self.tempvalues = self.detector.tempvalues

    @command(group=ACQUISITION)
    async def acquisition_start(self) -> None:
        # Start receiver listener for detector data packets
        # and create a data file (if file write enabled)
        self.detector.rx_start()
        # Start detector acquisition. Automatically returns
        # to idle at the end of acquisition.
        self.detector.start()

        # We probably want to run an rx_stop when the detector goes idle so that it self
        # flushes the frames. As it stands DAQ has to hit stop

    @command(group=ACQUISITION)
    async def acquisition_stop(self) -> None:
        # Abort detector acquisition, stop server
        self.detector.stop()
        # Stop receiver listener for detector data packets
        # and close current data file (if file write enabled)
        self.detector.rx_stop()
        # If acquisition was aborted during the acquire
        # command, clear the acquiring flag in shared
        # memory ready for starting the next acquisition
        self.detector.clearbusy()

    @command(group=ACQUISITION)
    async def clear_busy_flag(self) -> None:
        self.detector.clearbusy()
