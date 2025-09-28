import os
from typing import TypedDict, Annotated, Sequence
from operator import add as add_messages
from langgraph.graph import StateGraph, END
from langchain_core.messages import BaseMessage, SystemMessage, ToolMessage
from langchain_core.tools import tool
from langchain_google_genai import ChatGoogleGenerativeAI

# System prompt (same as your original)
system_prompt = """
You are an intelligent AI assistant who summarizes and/or answers user question based on the context provided in the given text.
when a user asks a question refer to the tool or the provided document and answer the question.
"""

class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], add_messages]


def should_continue(state: AgentState) -> bool:
    """Return True if the last message requests a tool call (defensive)."""
    try:
        last = state['messages'][-1]
    except Exception:
        return False

    # If wrapper attaches `tool_calls` list to the message
    if hasattr(last, "tool_calls") and isinstance(last.tool_calls, (list, tuple)):
        return len(last.tool_calls) > 0

    # Also accept a JSON tool-call pattern in message content
    try:
        import json
        parsed = json.loads(last.content.strip())
        return isinstance(parsed, dict) and parsed.get("tool") is not None
    except Exception:
        return False


def create_rag_agent(retriever, vectorstore):
    """
    Factory that creates a RAG agent (compiled StateGraph) and a retriever_tool bound to the provided retriever/vectorstore.

    Args:
        retriever: a LangChain retriever object (e.g., vectorstore.as_retriever()).
        vectorstore: the underlying vectorstore instance (used as a fallback).

    Returns:
        (rag_agent, retriever_tool): compiled graph agent and the retriever tool function.
    """

    @tool
    def retriever_tool(query: str) -> str:
        """
        Search the uploaded document vectorstore and return the top relevant passages.

        Args:
            query (str): User query to search against the document embedding index.

        Returns:
            str: Concatenated summaries of the top matching document chunks (or a not-found message).
        """
        # Try common API names defensively
        try:
            docs = retriever.get_relevant_documents(query)
        except Exception:
            try:
                docs = retriever.retrieve(query)
            except Exception:
                try:
                    # fallback: if vectorstore is available
                    docs = vectorstore.as_retriever().get_relevant_documents(query)
                except Exception as e:
                    return f"Retriever error: {e}"

        if not docs:
            return "I found no relevant information in the provided document."

        results = []
        for i, doc in enumerate(docs[:5], start=1):
            content = getattr(doc, "page_content", str(doc))[:1200]
            results.append(f"Document {i}:\\n{content}")

        return "\\n\\n".join(results)

    # Keep tools list and dict
    tools = [retriever_tool]
    tools_dict = {t.name: t for t in tools}

    # LLM setup: use env var GOOGLE_API_KEY for Gemini-like configuration
    GOOGLE_API_KEY = os.environ.get('GOOGLE_API_KEY')
    llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash-lite", temperature=0, google_api_key=GOOGLE_API_KEY)

    # attempt to bind tools if the LLM wrapper supports it; ignore otherwise
    try:
        llm = llm.bind_tools(tools)
    except Exception:
        pass

    def call_llm(state: AgentState) -> AgentState:
        """Call the LLM with the current state and system prompt."""
        messages = list(state['messages'])
        messages_with_system_prompt = [SystemMessage(content=system_prompt)] + messages
        message = llm.invoke(messages_with_system_prompt)
        return {'messages': [message]}

    def take_action(state: AgentState) -> AgentState:
        """Execute tool calls from the LLM's response and return ToolMessage-wrapped results."""
        last_msg = state['messages'][-1]
        tool_calls = []

        # If wrapper supplies tool_calls attribute, use it
        if hasattr(last_msg, "tool_calls") and isinstance(last_msg.tool_calls, (list, tuple)):
            tool_calls = last_msg.tool_calls
        else:
            # Try to parse JSON tool call structure from message content
            try:
                import json
                parsed = json.loads(last_msg.content.strip())
                if isinstance(parsed, dict) and parsed.get("tool"):
                    tool_calls = [{
                        "id": None,
                        "name": parsed.get("tool"),
                        "args": parsed.get("args", {})
                    }]
            except Exception:
                tool_calls = []

        results = []
        for t in tool_calls:
            name = t.get('name')
            args = t.get('args', {}) if isinstance(t.get('args', {}), dict) else {}
            print(f"Calling Tool: {name} with query: {args.get('query', 'No query provided')}")

            if not name or name not in tools_dict:
                print(f"\nTool: {name} does not exist.")
                result = "Incorrect Tool Name, Please Retry and Select tool from List of Available tools."
            else:
                tool_obj = tools_dict[name]
                # Safe invocation: try .invoke(...) then call directly, handle arg unpacking variations
                try:
                    if hasattr(tool_obj, "invoke"):
                        tool_result = tool_obj.invoke(**args)
                    else:
                        tool_result = tool_obj(**args)
                except TypeError:
                    try:
                        # maybe the tool expects a single arg (positional)
                        tool_result = tool_obj(args)
                    except Exception as e:
                        tool_result = f"Tool invocation failed: {e}"
                except Exception as e:
                    tool_result = f"Tool invocation failed: {e}"

                result = tool_result

            results.append(ToolMessage(tool_call_id=t.get('id', None), name=name, content=str(result)))

        print("Tools Execution Complete. Back to the model!")
        return {'messages': results}

    # Graph construction (same control flow as original)
    graph = StateGraph(AgentState)
    graph.add_node("llm", call_llm)
    graph.add_node("retriever_agent", take_action)

    graph.add_conditional_edges(
        "llm",
        should_continue,
        {True: "retriever_agent", False: END}
    )
    graph.add_edge("retriever_agent", "llm")
    graph.set_entry_point("llm")

    rag_agent = graph.compile()

    return rag_agent, retriever_tool
