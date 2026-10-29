"""Interface for ``python -m fastcs_jungfrau``."""

from pathlib import Path
from typing import Optional

import typer
from fastcs.launch import FastCS
from fastcs.logging import LogLevel, configure_logging
from fastcs.transports.epics import EpicsGUIOptions
from fastcs.transports.epics.ca import EpicsCATransport

from fastcs_mythen import __version__

# from fastcs_mythen.controllers.jungfrau_odin_controller import MythenOdinController
from fastcs_mythen.controllers.mythen_controller import MythenController

__all__ = ["main"]

app = typer.Typer()

OPI_PATH = Path("/epics/opi")


def version_callback(value: bool):
    if value:
        typer.echo(__version__)
        raise typer.Exit()


@app.callback()
def main(
    # TODO: typer does not support `bool | None` yet
    # https://github.com/tiangolo/typer/issues/533
    version: Optional[bool] = typer.Option(  # noqa
        None,
        "--version",
        callback=version_callback,
        is_eager=True,
        help="Print the version and exit",
    ),
):
    pass


@app.command()
def ioc(
    pv_prefix: str = typer.Argument(),
    config: str = typer.Option(help="Path to the config file"),
):
    # Configure logging
    configure_logging(LogLevel.TRACE)

    ui_path = OPI_PATH if OPI_PATH.is_dir() else Path.cwd()

    controller = MythenController(config_file_path=config)

    # ...some IOC options...
    options = EpicsCATransport(
        gui=EpicsGUIOptions(
            output_dir=ui_path / "mythen.bob", title=f"Mythen - {pv_prefix}"
        ),
    )

    # ...and pass them both to FastCS
    launcher = FastCS(controller, [options])
    launcher.run()


# Run with 'python -m fastcs_mythen'
# (after activating the venv)
if __name__ == "__main__":
    app()
