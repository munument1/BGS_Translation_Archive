"""Bounded SSU8/SSU9 reader. Reads source SST bytes without executing them."""
import hashlib
from pathlib import Path
import struct
MAX_TEXT_BYTES=1024*1024
MAX_LABELS=4096
MAX_RECORDS=300000

class SSTError(ValueError):
    pass


class Reader:
    def __init__(self, content: bytes):
        self.content = content
        self.pos = 0

    def take(self, count: int) -> bytes:
        if count < 0 or count > len(self.content) - self.pos:
            raise SSTError(f"Truncated at offset {self.pos}, requested {count} bytes")
        start = self.pos
        self.pos += count
        return self.content[start : self.pos]

    def number(self, fmt: str) -> int:
        return struct.unpack("<" + fmt, self.take(struct.calcsize("<" + fmt)))[0]

    def text(self) -> str:
        n = self.number("I")
        if n > MAX_TEXT_BYTES or n % 2:
            raise SSTError(f"Bad UTF-16LE byte length {n} at offset {self.pos - 4}")
        try:
            return self.take(n).decode("utf-16-le", errors="strict")
        except UnicodeError as error:
            raise SSTError(f"Invalid UTF-16LE at offset {self.pos - n}") from error


def parse_sst(path: Path, *, max_file_bytes: int = 16 * 1024 * 1024) -> dict:
    """Parse an SST as *untrusted bytes*; never write to the source path."""
    length = path.stat().st_size
    if length > max_file_bytes:
        raise SSTError(f"File too large for safe probe: {length} > {max_file_bytes}")
    if length < 9:
        raise SSTError("SST too short")
    with path.open("rb") as stream:
        content = stream.read(max_file_bytes + 1)
    if len(content) != length:
        raise SSTError("File size changed during read or exceeds limit")

    rd = Reader(content)
    magic = rd.take(4)
    if magic not in (b"SSU8", b"SSU9"):
        raise SSTError(f"Unsupported SST signature {magic!r}; parser accepts SSU8/SSU9 only")
    if magic == b"SSU9" and length < 13:
        raise SSTError("SSU9 header too short")
    flags = rd.number("B")
    masters = []
    if magic == b"SSU9":
        # VocabUserHeader8 (SSU9, version 8) introduced the master list.
        # VocabUserHeader7 (SSU8, version 7) begins directly with labels.
        master_count = rd.number("I")
        if master_count > MAX_LABELS:
            raise SSTError(f"Unreasonable master count: {master_count}")
        masters = [rd.text() for _ in range(master_count)]
    collaboration_count = rd.number("I")
    if collaboration_count > MAX_LABELS:
        raise SSTError(f"Unreasonable collaboration label count: {collaboration_count}")
    labels = [{"id": rd.number("I"), "text": rd.text()} for _ in range(collaboration_count)]

    mappings = []
    while rd.pos < len(content):
        if len(mappings) >= MAX_RECORDS:
            raise SSTError("Unreasonable record count")
        offset = rd.pos
        list_index = rd.number("B")
        if list_index not in (0, 1, 2):
            raise SSTError(f"Invalid list index {list_index} at {offset}")
        string_id = rd.number("I")
        form_id = rd.number("I")
        record_name = rd.take(4).decode("ascii", errors="strict")
        field_name = rd.take(4).decode("ascii", errors="strict")
        index = rd.number("H")
        index_max = rd.number("H")
        editor_id_hash = rd.number("I")
        collaboration_id = rd.number("B")
        status_flags = rd.number("B")
        source = rd.text()
        translated = rd.text()
        mappings.append(
            {
                "offset": offset,
                "list_index": list_index,
                "string_id": string_id,
                "form_id": f"0x{form_id:08X}",
                "record_name": record_name,
                "field_name": field_name,
                "index": index,
                "index_max": index_max,
                "editor_id_hash": f"0x{editor_id_hash:08X}",
                "collaboration_id": collaboration_id,
                "status_flags_raw": status_flags,
                "source": source,
                "korean": translated,
            }
        )
    return {
        "signature": magic.decode("ascii"),
        "header_flags_raw": flags,
        "master_files": masters,
        "collaboration_labels": labels,
        "records": mappings,
        "record_count": len(mappings),
        "sha256": hashlib.sha256(content).hexdigest(),
        "complete_to_eof": rd.pos == len(content),
    }

