#!/usr/bin/env bash

set -e

# Setup internet connection via usb0 FIRST, before anything else
# This must run before any network-dependent operations
sudo dhclient usb0 2>&1 || true

# Resolve project root as the parent of this script directory
SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd -- "${SCRIPT_DIR}/.." && pwd)"
# Get the actual user's home directory (not derived from project path)
SERVICE_USER="${SUDO_USER:-$(whoami)}"
HOME_DIR="$(eval echo ~${SERVICE_USER})"
cd "${PROJECT_ROOT}"

# Prefer project venv if present
if [ -f "${PROJECT_ROOT}/venv/bin/activate" ]; then
  . "${PROJECT_ROOT}/venv/bin/activate"
fi

# Ensure GUI env for systemd-launched session
export DISPLAY=${DISPLAY:-:0}
export XAUTHORITY=${XAUTHORITY:-${HOME_DIR}/.Xauthority}
export HOME=${HOME:-${HOME_DIR}}
export XDG_RUNTIME_DIR=${XDG_RUNTIME_DIR:-/run/user/1000}

exec sudo python3 "${PROJECT_ROOT}/main.py"