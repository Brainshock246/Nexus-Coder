import tempfile
import unittest
from pathlib import Path

from agent.memory.long_term import LongTermMemory
from agent.memory.short_term import ShortTermMemory


class MemoryTests(unittest.TestCase):
    def test_short_term_memory_roundtrip(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "short.json"
            stm = ShortTermMemory(path)
            stm.add({"k": "v"})
            self.assertEqual(stm.recent(1)[0]["k"], "v")

    def test_long_term_memory_search(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            ltm = LongTermMemory(Path(tmp) / "long.db")
            ltm.write("note", "hello memory")
            matches = ltm.search("hello")
            self.assertEqual(len(matches), 1)
            ltm.close()


if __name__ == "__main__":
    unittest.main()

