import tempfile
import unittest
from pathlib import Path

from agent.knowledge.graph import KnowledgeGraph


class KnowledgeGraphTests(unittest.TestCase):
    def test_graph_search_and_edges(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            graph = KnowledgeGraph(Path(tmp) / "knowledge_graph.db")
            graph.upsert_node("concepts", "c1", "planning optimization")
            graph.upsert_node("tasks", "t1", "execute optimization")
            graph.add_edge("c1", "t1", "reference")
            matches = graph.search("planning")
            rel = graph.discover_relationships("c1")
            self.assertEqual(len(matches["matches"]), 1)
            self.assertEqual(len(rel["outgoing"]), 1)
            graph.close()


if __name__ == "__main__":
    unittest.main()
