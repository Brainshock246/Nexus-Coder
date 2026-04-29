import unittest

from agent.memory.compression import MemoryCompressor


class MemoryCompressionTests(unittest.TestCase):
    def test_compress_groups_by_tool(self) -> None:
        compressor = MemoryCompressor()
        result = compressor.compress(
            [
                {"action": {"tool": "file_reader"}, "reflection": {"success": True}},
                {"action": {"tool": "file_reader"}, "reflection": {"success": False}},
                {"action": {"tool": "web_search"}, "reflection": {"success": True}},
            ]
        )
        self.assertGreaterEqual(len(result["summary"]), 2)


if __name__ == "__main__":
    unittest.main()
