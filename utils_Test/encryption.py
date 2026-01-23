import os
import sys
import base64


def _ensure_repo_root_on_path():
    this_dir = os.path.dirname(os.path.abspath(__file__))
    repo_root = os.path.abspath(os.path.join(this_dir, os.pardir))
    if repo_root not in sys.path:
        sys.path.insert(0, repo_root)


_ensure_repo_root_on_path()

from utils.api_client import ApiClient  # noqa: E402


def encrypt(plaintext: str) -> str:
    """
    Companion to ApiClient._decrypt_config_value static scheme.
    Produces a value like: "enc:" + base64-url of transformed bytes.
    """
    a = 1664525
    c = 1013904223
    mod = 2 ** 32
    state = 0xA3C59AC3

    def next_key_byte() -> int:
        nonlocal state
        state = (a * state + c) % mod
        return (state >> 24) & 0xFF

    p = plaintext.encode("utf-8")
    out = bytearray(len(p))
    for i, b in enumerate(p):
        k = next_key_byte()
        out[i] = ((b ^ k) + (i % 256)) & 0xFF
    return "enc:" + base64.urlsafe_b64encode(bytes(out)).decode("utf-8")


def run_checks():
    client = ApiClient()

    cases = [
        "",  # empty
        "abc",
        "NEXUS-1234-SECRET",
        "unicode ✓",
        "long-" + ("x" * 200),
    ]

    # 1) Encrypted round-trip
    for idx, plain in enumerate(cases):
        enc = encrypt(plain)
        dec = client._decrypt_config_value(enc)
        if dec != plain:
            raise AssertionError(f"Round-trip failed for case {idx}: {plain!r} -> {enc!r} -> {dec!r}")

    # 2) Plain inputs pass through unchanged
    passthrough_cases = [
        "not_encrypted",
        "enc is not a prefix here",
    ]
    for s in passthrough_cases:
        dec = client._decrypt_config_value(s)
        if dec != s:
            raise AssertionError(f"Passthrough failed: {s!r} -> {dec!r}")

    print("All encryption/decryption checks passed.")

    # 3) Detailed step-by-step for provided credentials
    # provided_values = {
    #     "client_id": "dC1zM4ghLvr8eipSOlmRhAelHRXdtvNC",
    #     "client_secret": "M__OTtIL7Pw754RBKIEEOCrXsxTef61vWny57keAXqwNN6mvylhg5Yc4XNtajqk4",
    # }
    provided_values = {
        "client_id": "pBwSiPtKmklfuqgZ7KUE05GPYkmySNiT",
        "client_secret": "C2AOzwrW1HxJ4t1gAUa8tdvZnhomVINUNDzj6hLtPxK_KTq5JIt4pHRMgl2m3-dd",
    }

    for label, plain in provided_values.items():
        print("\n==== STEP-BY-STEP:", label, "====")
        print("PLAINTEXT:", plain)
        enc = encrypt(plain)
        print("ENCRYPTED (with prefix):", enc)
        b64_payload = enc[len("enc:"):]
        print("BASE64 PAYLOAD:", b64_payload)
        payload_bytes = base64.urlsafe_b64decode(b64_payload.encode("utf-8"))
        print("PAYLOAD BYTES (hex):", payload_bytes.hex())
        dec = client._decrypt_config_value(enc)
        print("DECRYPTED:", dec)
        ok = (dec == plain)
        print("MATCHES ORIGINAL:", ok)
        if not ok:
            raise AssertionError(f"Decryption mismatch for {label}")


if __name__ == "__main__":
    run_checks()


