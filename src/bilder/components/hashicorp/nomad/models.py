from collections.abc import Iterable
from pathlib import Path
from typing import Optional

from bilder.components.hashicorp.models import FlexibleBaseModel, HashicorpProduct
from bilder.lib.model_helpers import OLBaseSettings


class NomadClientConfig(FlexibleBaseModel):
    enabled: bool = True


class NomadServerConfig(FlexibleBaseModel):
    enabled: bool = True


class NomadConfig(OLBaseSettings):
    client: Optional[NomadClientConfig]
    data_dir: Optional[Path] = Path("/var/lib/nomad/")
    server: Optional[NomadServerConfig]

    class Config:
        env_prefix = "nomad_"


class NomadJob(OLBaseSettings):
    class Config:
        env_prefix = "nomad_job_"


class Nomad(HashicorpProduct):
    _name: str = "nomad"
    version: str = "1.0.4"
    configuration: dict[Path, NomadConfig] = {
        Path("/etc/nomad.d/00-default.json"): NomadConfig(client=NomadClientConfig())
    }
    configuration_directory: Path = Path("/etc/nomad.d/")

    @property
    def systemd_template_context(self):
        return self

    def render_configuration_files(self) -> Iterable[tuple[Path, str]]:
        for fpath, config in self.configuration.items():
            yield fpath, config.json(exclude_none=True, indent=2)

    @property
    def data_directory(self) -> Path:
        for config in self.configuration.values():
            data_dir = config.data_dir
        return data_dir or Path("/var/lib/nomad/")
