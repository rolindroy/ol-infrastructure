import json
import tempfile
from typing import Any, Dict, Optional

from pyinfra import host
from pyinfra.api.deploy import deploy
from pyinfra.api.exceptions import DeployError
from pyinfra.facts.deb import DebPackages
from pyinfra.facts.server import Command, LinuxDistribution
from pyinfra.operations import apt, files


def _apt_install():

    apt.packages(
        name="Ensure Docker CE prerequisites are present",
        present=True,
        packages=[
            "curl",
            "gnupg-agent",
            "software-properties-common",
        ],
        update=True,
    )

    apt.packages(
        name="Install apt requirements to use HTTPS",
        present=True,
        packages=["apt-transport-https", "ca-certificates"],
        update=True,
        cache_time=3600,
    )
    lsb_release = host.get_fact(LinuxDistribution)
    lsb_id = lsb_release["name"].lower()

    apt.key(
        name="Download the Docker apt key",
        src=f"https://download.docker.com/linux/{lsb_id}/gpg",
    )

    dpkg_arch = host.get_fact(Command, command="dpkg --print-architecture")

    add_apt_repo = apt.repo(
        name="Add the Docker apt repo",
        src=(
            f"deb [arch={dpkg_arch}] https://download.docker.com/linux/{lsb_id}"
            f" {lsb_release['release_meta']['CODENAME']} stable"
        ),
        filename="docker-ce-stable",
    )

    apt.packages(
        name="Install Docker via apt",
        packages="docker-ce",
        update=add_apt_repo.changed,
    )


@deploy("Deploy Docker")
def deploy_docker(config: Optional[Dict[str, Any]] = None):

    if host.get_fact(DebPackages):
        _apt_install()
    else:
        raise DeployError(
            ("Apt not found, pyinfra-docker cannot provision this machine!"),
        )

    if config:
        with tempfile.NamedTemporaryFile("wt", delete=False) as daemon:
            daemon.write(json.dumps(config, indent=4))
            files.put(
                name="Upload the Docker daemon.json",
                src=daemon.name,
                dest="/etc/docker/daemon.json",
            )
