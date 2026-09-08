"""Parse actual game records; never infer a victory from a replay filename."""
import re


def parse_xlog(line):
    """NAO 3.4.3 uses colons; later NetHack versions commonly use tabs."""
    line = line.strip()
    fields = list(re.finditer(r"(?:^|[:\t])([A-Za-z][A-Za-z0-9_]*)=", line))
    return {match[1]: line[match.end():fields[i + 1].start() if i + 1 < len(fields) else len(line)].rstrip("\r\n")
            for i, match in enumerate(fields)}


def legitimate_ascension(record):
    # NAO xlog flags: bit 0 = wizard, bit 1 = discovery. Check both.
    return (record.get("death") == "ascended" and record.get("version") == "3.4.3"
            and "flags" in record and not (int(record["flags"], 0) & 3))
