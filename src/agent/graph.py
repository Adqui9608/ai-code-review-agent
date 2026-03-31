"""LangGraph StateGraph definition for the code review pipeline."""

from __future__ import annotations

from langgraph.graph import END, StateGraph

from src.agent.nodes import (
    ReviewState,
    aggregate,
    analyze_file,
    filter_files,
    format_review,
    parse_diff,
)


def build_review_graph() -> StateGraph:
    """Build and compile the code review LangGraph pipeline.

    Returns:
        A compiled graph ready for invocation with ReviewState.
    """
    graph = StateGraph(ReviewState)

    graph.add_node("parse_diff", parse_diff)
    graph.add_node("filter_files", filter_files)
    graph.add_node("analyze_file", analyze_file)
    graph.add_node("aggregate", aggregate)
    graph.add_node("format_review", format_review)

    graph.set_entry_point("parse_diff")
    graph.add_edge("parse_diff", "filter_files")
    graph.add_edge("filter_files", "analyze_file")
    graph.add_edge("analyze_file", "aggregate")
    graph.add_edge("aggregate", "format_review")
    graph.add_edge("format_review", END)

    return graph.compile()
