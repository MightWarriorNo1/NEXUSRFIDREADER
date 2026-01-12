import json
import os
import sys
from pathlib import Path
from typing import List, Optional, Set, Tuple
import re

try:
    from azure.storage.blob import ContainerClient
except Exception as exc:  # pragma: no cover
    print("ERROR: Missing dependency 'azure-storage-blob'. Install with: pip install azure-storage-blob", file=sys.stderr)
    raise


PROVISIONING_CONFIG_PATH = "/etc/azureiotpnp/provisioning_config.json"
RASPBERRY_PI_EXECUTABLE_RELATIVE_PATH = "RaspberryPi/NexusRFIDReader"
DESTINATION_PATH = "/home/NexusRFIDReader"


def load_provisioning_config(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def normalize_base_path(base_path: str) -> str:
    # Ensure no leading slash and no trailing slash
    return base_path.strip("/")


def get_container_client(account: str, container: str, sas_token: str) -> ContainerClient:
    account_url = f"https://{account}.blob.core.windows.net"
    # sas_token may or may not start with '?'; ContainerClient accepts raw SAS string
    sas = sas_token[1:] if sas_token.startswith("?") else sas_token
    return ContainerClient(account_url=account_url, container_name=container, credential=sas)


def extract_build_number_from_blob_name(blob_name: str, blob_base_path: str) -> Optional[str]:
    # Expect names like: builds/<Build.BuildNumber>/RaspberryPi/NexusRFIDReader
    parts = blob_name.split("/")
    base_parts = blob_base_path.split("/") if blob_base_path else []
    if len(parts) < len(base_parts) + 1:
        return None
    # The build number should be the segment immediately after the base path
    # Find index of the last base path segment in the blob path
    idx_after_base = len(base_parts)
    if base_parts and parts[:len(base_parts)] != base_parts:
        return None
    if len(parts) <= idx_after_base:
        return None
    return parts[idx_after_base]


_VERSION_RE = re.compile(r"^(\d{8})\.(\d+)$")


def parse_build_version(version: str) -> Tuple[int, int]:
    # Strictly parse format YYYYMMDD.N to support correct ordering
    try:
        m = _VERSION_RE.match(version.strip())
        if not m:
            raise ValueError("invalid version format")
        date_part, seq_part = m.groups()
        return int(date_part), int(seq_part)
    except Exception:
        # Fallback: treat entire version as 0 to push invalid versions to the bottom
        return 0, 0


def is_version_newer(candidate: str, baseline: str) -> bool:
    return parse_build_version(candidate) > parse_build_version(baseline)


def find_newer_build(available_builds: Set[str], current_version: str) -> Optional[str]:
    newer_builds = [b for b in available_builds if is_version_newer(b, current_version)]
    if not newer_builds:
        return None
    # Pick the newest available
    return max(newer_builds, key=parse_build_version)


def list_available_builds(container: ContainerClient, blob_base_path: str) -> Set[str]:
    prefix = f"{blob_base_path}/" if blob_base_path else ""
    builds: Set[str] = set()
    for blob in container.list_blobs(name_starts_with=prefix):
        build = extract_build_number_from_blob_name(blob.name, blob_base_path)
        if build:
            builds.add(build)
    return builds


def find_raspberrypi_blob_path(container: ContainerClient, blob_base_path: str, build: str) -> Optional[str]:
    # Search under <base>/<build>/ for RaspberryPi folder and NexusRFIDReader (with or without .exe)
    prefix = f"{blob_base_path}/{build}/"
    candidates: List[str] = []
    try:
        for blob in container.list_blobs(name_starts_with=prefix):
            name_lower = blob.name.lower()
            if "/raspberrypi/" not in name_lower:
                continue
            # Accept common names
            if name_lower.endswith("/nexusrfidreader") or name_lower.endswith("/nexusrfidreader.exe"):
                candidates.append(blob.name)
            elif name_lower.endswith("/nexusrfidpoc") or name_lower.endswith("/nexusrfidpoc.exe"):
                candidates.append(blob.name)
            else:
                # As a fallback, accept any file (exclude directory placeholders)
                if not name_lower.endswith("/") and not name_lower.endswith(".md5") and not name_lower.endswith(".sha256"):
                    candidates.append(blob.name)
    except Exception:
        return None
    # Prefer non-.exe if both exist
    if not candidates:
        return None
    candidates_sorted = sorted(candidates, key=lambda n: (n.lower().endswith(".exe"), n))
    return candidates_sorted[0]


def download_blob_to_path(container: ContainerClient, blob_path: str, destination_path: str) -> None:
    blob_client = container.get_blob_client(blob_path)
    # Ensure destination directory exists
    Path(destination_path).parent.mkdir(parents=True, exist_ok=True)
    with open(destination_path, "wb") as f:
        stream = blob_client.download_blob()
        stream.readinto(f)


def blob_exists(container: ContainerClient, blob_path: str) -> bool:
    try:
        blob_client = container.get_blob_client(blob_path)
        return bool(blob_client.exists())
    except Exception:
        return False


def ensure_executable(path: str) -> None:
    try:
        st = os.stat(path)
        os.chmod(path, st.st_mode | 0o111)
    except Exception:
        # If chmod fails (e.g., on non-POSIX FS), ignore
        pass


def main(argv: List[str]) -> int:
    try:
        config = load_provisioning_config(PROVISIONING_CONFIG_PATH)
    except FileNotFoundError:
        print(f"ERROR: Provisioning config not found at {PROVISIONING_CONFIG_PATH}", file=sys.stderr)
        return 2
    except json.JSONDecodeError as exc:
        print(f"ERROR: Failed to parse provisioning config: {exc}", file=sys.stderr)
        return 2

    device_update = config.get("deviceUpdate", {})
    storage_account = device_update.get("storageAccount")
    container_name = device_update.get("containerName")
    blob_base_path = normalize_base_path(device_update.get("blobBasePath", ""))
    current_version = device_update.get("currentVersion")
    sas_token = device_update.get("sasToken")

    missing_fields = [
        name for name, value in [
            ("storageAccount", storage_account),
            ("containerName", container_name),
            ("blobBasePath", blob_base_path),
            ("currentVersion", current_version),
            ("sasToken", sas_token),
        ]
        if not value
    ]
    if missing_fields:
        print(f"ERROR: Missing required deviceUpdate fields in provisioning config: {', '.join(missing_fields)}", file=sys.stderr)
        return 2

    try:
        container = get_container_client(storage_account, container_name, sas_token)
    except Exception as exc:
        print(f"ERROR: Failed to create container client: {exc}", file=sys.stderr)
        return 3

    try:
        available_builds = list_available_builds(container, blob_base_path)
    except Exception as exc:
        print(f"ERROR: Failed to list builds: {exc}", file=sys.stderr)
        return 4

    if not available_builds:
        print("No builds found in storage.")
        return 0

    # STEP 2: Find latest build in container and compare
    print("Step 2: Retrieving latest build from blob storage ...")
    latest_in_blob = None
    if available_builds:
        latest_in_blob = max(available_builds, key=parse_build_version)
    if not latest_in_blob:
        print("No builds found in storage.")
        return 0
    print(f"  Latest blob version: {latest_in_blob}")

    # STEP 3: Compare versions
    print(f"Step 3: Comparing local {current_version} vs blob {latest_in_blob} ...")
    if not is_version_newer(latest_in_blob, current_version):
        print(f"Already up to date at version {current_version}.")
        return 0

    # STEP 4: Download latest blob version and place into /home
    print(f"Step 4: Downloading RaspberryPi artifact for {latest_in_blob} ...")
    selected_build: Optional[str] = latest_in_blob
    # Discover artifact path for selected build
    selected_blob_path = find_raspberrypi_blob_path(container, blob_base_path, selected_build)
    if not selected_blob_path:
        # Fallback to fixed expected path
        fallback_path = f"{blob_base_path}/{selected_build}/{RASPBERRY_PI_EXECUTABLE_RELATIVE_PATH}"
        if blob_exists(container, fallback_path):
            selected_blob_path = fallback_path

    if not selected_build or not selected_blob_path:
        print(
            f"No downloadable RaspberryPi artifact found for builds newer than {current_version}.",
            file=sys.stderr,
        )
        return 0

    try:
        print(f"  Downloading '{selected_blob_path}' -> '{DESTINATION_PATH}' ...")
        download_blob_to_path(container, selected_blob_path, DESTINATION_PATH)
        ensure_executable(DESTINATION_PATH)
    except Exception as exc:
        print(
            f"ERROR: Failed to download '{selected_blob_path}' -> '{DESTINATION_PATH}': {exc}",
            file=sys.stderr,
        )
        return 5

    # Update provisioning config currentVersion upon successful download
    try:
        config["deviceUpdate"]["currentVersion"] = selected_build
        with open(PROVISIONING_CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=2)
            f.write("\n")
    except Exception as exc:
        print(
            f"WARNING: Downloaded {selected_build} but failed to update provisioning config: {exc}",
            file=sys.stderr,
        )

    print(f"Done. Installed version {selected_build} at {DESTINATION_PATH}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))


