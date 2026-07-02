"""Expanded tests for the Memory system."""

from datetime import datetime
import pytest

from src.memory.history import Memory, Interaction


class TestInteraction:
    def test_creates_with_minimal_args(self):
        i = Interaction(user="u", assistant="a")
        assert i.user == "u"
        assert i.assistant == "a"

    def test_timestamp_defaults_to_now(self):
        i = Interaction(user="u", assistant="a")
        assert isinstance(i.timestamp, datetime)

    def test_topic_defaults_to_none(self):
        i = Interaction(user="u", assistant="a")
        assert i.topic is None


class TestMemoryAdd:
    def test_add_single_interaction(self, memory):
        memory.add_interaction(user="oi", assistant="tudo bem?")
        assert len(memory.history) == 1

    def test_add_updates_current_topic(self, memory):
        memory.add_interaction(user="q", assistant="r", topic="matematica")
        assert memory.current_topic == "matematica"

    def test_add_uses_current_topic_when_not_specified(self, memory):
        memory.add_interaction(user="q", assistant="r", topic="fisica")
        memory.add_interaction(user="q2", assistant="r2")
        assert memory.history[-1].topic == "fisica"

    def test_add_stores_scaffolding(self, memory):
        memory.add_interaction(user="q", assistant="r", scaffolding="N1")
        assert memory.history[-1].scaffolding_used == "N1"


class TestMemoryOverflow:
    def test_discards_oldest_when_full(self, small_memory):
        for i in range(5):
            small_memory.add_interaction(user=f"u{i}", assistant=f"r{i}")
        assert len(small_memory.history) == 3
        assert small_memory.history[-1].user == "u4"

    @pytest.mark.skip(reason="max_size=0 not yet implemented")
    def test_max_size_zero_discards_all(self):
        m = Memory(max_size=0)
        m.add_interaction(user="u", assistant="r")

    @pytest.mark.skip(reason="max_size=0 not yet implemented")
    def test_max_size_zero_keeps_empty(self):
        m = Memory(max_size=0)
        assert len(m.history) == 0


class TestMemoryContext:
    def test_empty_history_returns_default_message(self, memory):
        ctx = memory.get_context()
        assert ctx == "(primeira interação — sem histórico)"

    def test_context_includes_last_n_interactions(self, memory):
        for i in range(5):
            memory.add_interaction(user=f"u{i}", assistant=f"r{i}")
        ctx = memory.get_context(last_n=2)
        assert "u3" in ctx
        assert "u4" in ctx
        assert "u0" not in ctx

    def test_context_formats_properly(self, memory):
        memory.add_interaction(user="oi", assistant="ola")
        ctx = memory.get_context()
        assert "[Interação 1]" in ctx
        assert "Aluno: oi" in ctx
        assert "EDUcador: ola" in ctx

    def test_truncates_long_messages(self, memory):
        long = "x" * 500
        memory.add_interaction(user=long, assistant="curto")
        ctx = memory.get_context()
        assert "..." in ctx
        assert len(ctx.split("Aluno:")[1].split("\n")[0].strip()) <= 303

    def test_context_includes_topic(self, memory):
        memory.add_interaction(user="q", assistant="r", topic="historia")
        ctx = memory.get_context()
        assert "Tópico: historia" in ctx


class TestMemorySerialization:
    def test_to_dict_returns_list_of_dicts(self, memory):
        memory.add_interaction(user="u", assistant="r")
        data = memory.to_dict()
        assert isinstance(data, list)
        assert isinstance(data[0], dict)

    def test_to_dict_contains_keys(self, memory):
        memory.add_interaction(user="u", assistant="r", topic="t", scaffolding="s")
        data = memory.to_dict()
        assert "user" in data[0]
        assert "assistant" in data[0]
        assert "timestamp" in data[0]
        assert "topic" in data[0]
        assert "scaffolding_used" in data[0]

    def test_roundtrip_preserves_data(self, memory):
        memory.add_interaction(user="pergunta", assistant="resposta", topic="tema")
        data = memory.to_dict()
        m2 = Memory.from_dict(data)
        assert m2.history[0].user == "pergunta"
        assert m2.history[0].assistant == "resposta"
        assert m2.history[0].topic == "tema"

    def test_roundtrip_preserves_current_topic(self, memory):
        memory.add_interaction(user="q", assistant="r", topic="genetica")
        data = memory.to_dict()
        m2 = Memory.from_dict(data)
        assert m2.current_topic == "genetica"

    def test_unicode_content(self, memory):
        memory.add_interaction(
            user="coração ção",
            assistant="resposta com acentuação",
        )
        data = memory.to_dict()
        m2 = Memory.from_dict(data)
        assert m2.history[0].user == "coração ção"

    def test_empty_to_dict(self, memory):
        assert memory.to_dict() == []


class TestMemorySummary:
    def test_summary_total_interactions(self, memory):
        memory.add_interaction(user="u1", assistant="r1")
        memory.add_interaction(user="u2", assistant="r2")
        assert memory.get_summary()["total_interactions"] == 2

    def test_summary_last_user(self, memory):
        memory.add_interaction(user="ultimo", assistant="r")
        assert memory.get_summary()["last_user"] == "ultimo"

    def test_summary_none_for_empty(self, memory):
        s = memory.get_summary()
        assert s["total_interactions"] == 0
        assert s["last_user"] is None

    def test_summary_current_topic(self, memory):
        memory.add_interaction(user="q", assistant="r", topic="quimica")
        assert memory.get_summary()["current_topic"] == "quimica"


class TestMemoryClear:
    def test_clear_removes_all(self, memory):
        memory.add_interaction(user="u", assistant="r")
        memory.clear()
        assert len(memory.history) == 0

    def test_clear_resets_topic(self, memory):
        memory.add_interaction(user="q", assistant="r", topic="bio")
        memory.clear()
        assert memory.current_topic is None

    def test_clear_then_add_works(self, memory):
        memory.add_interaction(user="u1", assistant="r1")
        memory.clear()
        memory.add_interaction(user="u2", assistant="r2")
        assert len(memory.history) == 1
        assert memory.history[0].user == "u2"


class TestMemoryRecentTopics:
    def test_returns_most_recent_topics(self, memory):
        memory.add_interaction(user="q1", assistant="r1", topic="A")
        memory.add_interaction(user="q2", assistant="r2", topic="B")
        memory.add_interaction(user="q3", assistant="r3", topic="C")
        topics = memory.get_recent_topics(n=2)
        assert topics == ["C", "B"]

    def test_deduplicates_consecutive_same_topic(self, memory):
        memory.add_interaction(user="q1", assistant="r1", topic="mat")
        memory.add_interaction(user="q2", assistant="r2", topic="mat")
        memory.add_interaction(user="q3", assistant="r3", topic="fis")
        topics = memory.get_recent_topics(n=5)
        assert topics == ["fis", "mat"]

    def test_limits_to_n_topics(self, memory):
        for i in range(10):
            memory.add_interaction(user=f"q{i}", assistant=f"r{i}", topic=f"T{i}")
        topics = memory.get_recent_topics(n=3)
        assert len(topics) == 3

    def test_empty_history_returns_empty_list(self, memory):
        assert memory.get_recent_topics() == []


class TestMemoryLastInteraction:
    def test_returns_none_for_empty(self, memory):
        assert memory.get_last_interaction() is None

    def test_returns_last_interaction(self, memory):
        memory.add_interaction(user="first", assistant="r1")
        memory.add_interaction(user="last", assistant="r2")
        assert memory.get_last_interaction().user == "last"
