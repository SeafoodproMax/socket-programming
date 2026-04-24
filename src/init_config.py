"""Upsert an entry into config/host.yaml's server_list.

The config file is a named-profile map shaped like:

    server_list:
      lab_server:
        host: "10.7.209.196"
        port: 9999
      localhost:
        host: "127.0.0.1"
        port: 8080
      self:
        host: "192.168.1.10"
        port: 12345

This script reads the file (if it exists), adds or updates ONE entry
whose name is given by --name (default: "self"), and writes it back.
Other entries are preserved.

Usage:
    python src/init_config.py                            # upsert 'self' with auto-detected IP
    python src/init_config.py --name self --port 12345
    python src/init_config.py --name lab_server --host 10.7.209.196 --port 9999
"""

import argparse
import pathlib
import socket
import sys

import yaml


DEFAULT_NAME = "self"
DEFAULT_PORT = 12345
CONFIG_PATH = pathlib.Path(__file__).resolve().parent.parent / "config" / "host.yaml"


def detect_lan_ip() -> str:
    """Return the LAN-facing IP used for the default outbound route.

    Opens a UDP socket and "connects" it to a public address. No packet is
    actually sent, but the OS picks the outbound interface, and getsockname()
    then reports that interface's address instead of 127.0.0.1 / 0.0.0.0.

    Raises:
        RuntimeError: if the detected address is a loopback address.
    """
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        sock.connect(("8.8.8.8", 80))
        ip = sock.getsockname()[0]
    finally:
        sock.close()

    if ip.startswith("127."):
        raise RuntimeError(
            f"Detected loopback IP {ip!r}. Connect to a real Wi-Fi / Ethernet "
            "interface and try again, or pass --host explicitly."
        )
    return ip


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Upsert an entry into config/host.yaml's server_list."
    )
    parser.add_argument(
        "--name",
        default=DEFAULT_NAME,
        help=f"Profile name to add/update under server_list (default: {DEFAULT_NAME!r}).",
    )
    parser.add_argument(
        "--host",
        default=None,
        help=(
            "IP for this profile. Defaults to this machine's auto-detected "
            "LAN IP. On a client machine, pass the SERVER's IP here."
        ),
    )
    parser.add_argument(
        "--port",
        type=int,
        default=DEFAULT_PORT,
        help=f"Port for this profile (default: {DEFAULT_PORT}).",
    )
    return parser.parse_args()


def _load_existing(path: pathlib.Path) -> dict:
    if not path.exists():
        return {"server_list": {}}
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(data, dict):
        raise SystemExit(f"[init_config] {path} is not a mapping at the top level.")
    data.setdefault("server_list", {})
    if not isinstance(data["server_list"], dict):
        raise SystemExit(f"[init_config] {path} has a non-mapping 'server_list'.")
    return data


def main() -> int:
    args = _parse_args()

    try:
        host = args.host or detect_lan_ip()
    except (OSError, RuntimeError) as exc:
        print(f"[init_config] Could not auto-detect LAN IP: {exc}", file=sys.stderr)
        return 1

    CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    data = _load_existing(CONFIG_PATH)

    existed = args.name in data["server_list"]
    data["server_list"][args.name] = {"host": host, "port": args.port}

    CONFIG_PATH.write_text(
        yaml.safe_dump(data, sort_keys=False, default_flow_style=False),
        encoding="utf-8",
    )

    verb = "Updated" if existed else "Added"
    print(f"[init_config] {verb} profile {args.name!r} in {CONFIG_PATH}")
    print(f"             host: {host}")
    print(f"             port: {args.port}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
