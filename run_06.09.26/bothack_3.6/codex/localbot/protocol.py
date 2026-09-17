"""Ordered screen/input boundaries emitted by the patched tty window port."""
class ProtocolError(RuntimeError):
    pass

class Decoder:
    marker = b'\x1b]777;'
    def __init__(self):
        self.buffer = b''
    def feed(self, data):
        self.buffer += data
        if len(self.buffer) > 2**20:
            raise ProtocolError('No input boundary within 1 MiB of terminal output')
        result=[]
        while self.marker in self.buffer:
            before, rest = self.buffer.split(self.marker,1)
            if b'\x07' not in rest:
                break
            kind, self.buffer=rest.split(b'\x07',1)
            if kind not in (b'input',b'command',b'ack'):
                raise ProtocolError(f'Unknown boundary {kind!r}')
            result.append((kind,before))
        return result

class JSONTail:
    """Read a growing JSONL stream without interpreting a partial final line."""
    def __init__(self, stream):
        self.stream=stream
        self.pending=''
    def poll(self):
        import json
        self.pending+=self.stream.read()
        lines=self.pending.split('\n')
        self.pending=lines.pop()
        return [json.loads(line) for line in lines if line]
