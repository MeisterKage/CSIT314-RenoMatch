TEST_PASSWORD = "Passw0rd!"

TEST_CONFIG = {
    "TESTING": True,
    "SECRET_KEY": "test-secret",
    "WTF_CSRF_ENABLED": False,
    "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
    "SEED_ON_EMPTY": False,
}


def png_bytes(extra: int = 0) -> bytes:
    """A real 1x1 PNG, padded with `extra` bytes of trailing data to reach a chosen size."""
    import struct
    import zlib

    def chunk(kind: bytes, data: bytes) -> bytes:
        body = kind + data
        return struct.pack(">I", len(data)) + body + struct.pack(">I", zlib.crc32(body))

    header = struct.pack(">IIBBBBB", 1, 1, 8, 2, 0, 0, 0)
    pixels = zlib.compress(b"\x00\xff\x00\x00")
    png = b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", header) + chunk(b"IDAT", pixels)
    return png + chunk(b"IEND", b"") + b"\x00" * extra


def jpeg_bytes() -> bytes:
    """The start of a JPEG: enough for the content check, which reads the leading bytes."""
    return b"\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x00\x00\x01\x00\x01\x00\x00\xff\xd9"


GIF_BYTES = b"GIF89a\x01\x00\x01\x00\x80\x00\x00\x00\x00\x00\xff\xff\xff!\xf9\x04\x01"
