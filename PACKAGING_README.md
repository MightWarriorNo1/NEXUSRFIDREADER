# NexusRFID Reader Packaging Guide

This document describes how to build and install the production-ready Debian
package for the NexusRFID Reader kiosk application. The packaging flow reuses
the same service and runtime scripts that are used during development so the
installed system behaves identically to development mode (auto-start on boot,
same GUI entry point, networking pre-check, and storage under `~/.nexusrfid`).

> **Important:** The `Azure-IoT-Connection` utilities are not part of the
> production package by design. They remain available in the repository for
> development workflows.

## Prerequisites

- Debian/Ubuntu/Raspberry Pi OS environment with `python3.9+`
- `python3-venv`, `pip`, `dpkg-deb`, `rsync`, and `arp-scan`
- Repository cloned locally
- Run all commands from the project root unless stated otherwise

If this is a fresh system, execute the helper script once to install the global
tooling PyInstaller needs (Python headers, Qt dependencies, etc.):

```bash
sudo bash scripts/install_python.sh
```

## Build the Debian packages

```bash
bash scripts/create_pkg_rpi.sh
```

By default the script produces two artefacts in the project root:

- `NexusRFIDReader-1.0_x64.deb`
- `NexusRFIDReader-1.0_x86.deb`
- A convenience copy `NexusRFIDReader-1.0.deb` (points to the first build, typically x64)

> Use `--version <semver>` or `--arch amd64` to customise versions or target
> architectures. See `bash scripts/create_pkg_rpi.sh --help` for options.

The build pipeline performs the following:

1. Copies the project into a staging area, excluding development, test, and
   Azure IoT helper content.
2. Creates a self-contained Python `venv` inside the payload and installs all
   dependencies listed in `requirements.txt`.
3. Packages the repository assets (UI layouts, fonts, scripts, configs).
4. Bundles the `arp-scan` binary when available and produces a symlink at
   `/usr/local/bin/arp-scan` during installation.
5. Generates Debian control metadata plus maintainer scripts to provision and
   start the `nexusrfid` systemd service automatically.

## Install on production hardware

Transfer the `.deb` you intend to install to the target device and run:

```bash
sudo apt install ./NexusRFIDReader-1.0.deb
sudo reboot
```

After reboot the service launches automatically. All runtime files (database,
configuration, crash dumps, logs) remain in `~/.nexusrfid/`, matching the
development layout.

## Uninstall / Upgrade

To remove the package while preserving configuration data:

```bash
bash scripts/uninstall_pkg_rpi.sh
```

Pass `--purge` to also delete `~/.nexusrfid` and desktop entries.

For upgrades rerun `create_pkg_rpi.sh` and install the new `.deb` with `apt`.
APT applies maintainer scripts so it safely reloads the service with the new
payload.

## Troubleshooting

- **Service fails to start:** `sudo journalctl -u nexusrfid.service -n 200`
- **Check package contents:** `dpkg-deb -c NexusRFIDReader-1.0_x64.deb`
- **Rebuild clean:** Delete the `build/package/` directory or invoke
  `bash scripts/create_pkg_rpi.sh` (it cleans staging automatically unless
  `--keep-build` is set).

If packaging fails due to missing dependencies, rerun the prerequisites script
or install the reported packages manually.

