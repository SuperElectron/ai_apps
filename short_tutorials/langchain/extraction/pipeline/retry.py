import operator
import uuid
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import (AIMessage, AnyMessage, BaseMessage, HumanMessage)
from langchain_core.prompt_values import PromptValue
from langchain_core.runnables import (Runnable, RunnableLambda)
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ValidationNode
from pydantic import BaseModel, Field, field_validator
from typing import (Annotated, Callable, List, Literal, Optional, Sequence, Union)
from typing_extensions import TypedDict
from pipeline.reply_strategy import RetryStrategy


def _default_aggregator(messages: Sequence[AnyMessage]) -> AIMessage:
    for m in messages[::-1]:
        if m.type == "ai":
            return m
    raise ValueError("No AI message found in the sequence.")


def _bind_validator_with_retries(
        llm: Union[
            Runnable[Sequence[AnyMessage], AIMessage],
            Runnable[Sequence[BaseMessage], BaseMessage],
        ],
        *,
        validator: ValidationNode,
        retry_strategy: RetryStrategy,
        tool_choice: Optional[str] = None,
) -> Runnable[Union[List[AnyMessage], PromptValue], AIMessage]:
    """
    Bind a validator with retries to process messages through an LLM and validator chain.
    This function establishes a processing pipeline by binding an LLM, retry strategy, and
    validator with mechanisms for error handling and message aggregation.

    Parameters:
    llm (Union[Runnable[Sequence[AnyMessage], AIMessage], Runnable[Sequence[BaseMessage], BaseMessage]]):
        A runnable instance representing the language model that processes input messages.
    validator (ValidationNode):
        A validation node applied to the processed messages for evaluation.
    retry_strategy (RetryStrategy):
        Strategy defining the retry mechanism for processing messages in case of failure.
    tool_choice (Optional[str]):
        An optional tool name used within the validation phase to generate specific
        tool-related responses.

    Returns:
    Runnable[Union[List[AnyMessage], PromptValue], AIMessage]:
        A runnable chain that processes input messages, validates responses, and applies
        retry strategies based on configuration.

    Classes:
    State:
        Typed dictionary for maintaining the processing state during retries.
        Attributes:
            messages: List to hold processed messages with support for appending
                or overwriting.
            attempt_number: Tracks the current retry attempt number.
            initial_num_messages: Holds the initial number of messages
                before retrying.
            input_format: Tracks input format as either "list" or "dict".

    Finalizer:
        A callable wrapper for aggregating generated messages at the final step.
    """

    def add_or_overwrite_messages(left: list, right: Union[list, dict]) -> list:
        """Append messages. If the update is a 'finalized' output, replace the whole list."""
        if isinstance(right, dict) and "finalize" in right:
            finalized = right["finalize"]
            if not isinstance(finalized, list):
                finalized = [finalized]
            for m in finalized:
                if m.id is None:
                    m.id = str(uuid.uuid4())
            return finalized
        res = add_messages(left, right)
        if not isinstance(res, list):
            return [res]
        return res

    class State(TypedDict):
        messages: Annotated[list, add_or_overwrite_messages]
        attempt_number: Annotated[int, operator.add]
        initial_num_messages: int
        input_format: Literal["list", "dict"]

    builder = StateGraph(State)

    def dedict(x: State) -> list:
        """Get the messages from the state."""
        return x["messages"]

    model = dedict | llm | (lambda msg: {"messages": [msg], "attempt_number": 1})
    fbrunnable = retry_strategy.get("fallback")
    if fbrunnable is None:
        fb_runnable = llm
    elif isinstance(fbrunnable, Runnable):
        fb_runnable = fbrunnable  # type: ignore
    else:
        fb_runnable = RunnableLambda(fbrunnable)
    fallback = (
            dedict | fb_runnable | (lambda msg: {"messages": [msg], "attempt_number": 1})
    )

    def count_messages(state: State) -> dict:
        return {"initial_num_messages": len(state.get("messages", []))}

    builder.add_node("count_messages", count_messages)
    builder.add_node("llm", model)
    builder.add_node("fallback", fallback)

    # To support patch-based retries, we need to be able to
    # aggregate the messages over multiple turns.
    # The next sequence selects only the relevant messages
    # and then applies the validator
    select_messages = retry_strategy.get("aggregate_messages") or _default_aggregator

    def select_generated_messages(state: State) -> list:
        """Select only the messages generated within this loop."""
        selected = state["messages"][state["initial_num_messages"]:]
        return [select_messages(selected)]

    def endict_validator_output(x: Sequence[AnyMessage]) -> dict:
        if tool_choice and not x:
            return {
                "messages": [
                    HumanMessage(
                        content=f"ValidationError: please respond with a valid tool call [tool_choice={tool_choice}].",
                        additional_kwargs={"is_error": True},
                    )
                ]
            }
        return {"messages": x}

    validator_runnable = select_generated_messages | validator | endict_validator_output
    builder.add_node("validator", validator_runnable)

    class Finalizer:

        def __init__(self, aggregator: Optional[Callable[[list], AIMessage]] = None):
            self._aggregator = aggregator or _default_aggregator

        def __call__(self, state: State) -> dict:
            """Return just the AI message."""
            initial_num_messages = state["initial_num_messages"]
            generated_messages = state["messages"][initial_num_messages:]
            return {
                "messages": {
                    "finalize": self._aggregator(generated_messages),
                }
            }

    # We only want to emit the final message
    builder.add_node("finalizer", Finalizer(retry_strategy.get("aggregate_messages")))

    # Define the connectivity
    builder.add_edge(START, "count_messages")
    builder.add_edge("count_messages", "llm")

    def route_validator(state: State):
        if state["messages"][-1].tool_calls or tool_choice is not None:
            return "validator"
        return END

    builder.add_conditional_edges("llm", route_validator, ["validator", END])
    builder.add_edge("fallback", "validator")
    max_attempts = retry_strategy.get("max_attempts", 3)

    def route_validation(state: State):
        if state["attempt_number"] > max_attempts:
            raise ValueError(
                f"Could not extract a valid value in {max_attempts} attempts."
            )
        for m in state["messages"][::-1]:
            if m.type == "ai":
                break
            if m.additional_kwargs.get("is_error"):
                return "fallback"
        return "finalizer"

    builder.add_conditional_edges("validator", route_validation, ["finalizer", "fallback"])

    builder.add_edge("finalizer", END)

    # These functions let the step be used in a MessageGraph
    # or a StateGraph with 'messages' as the key.
    def encode(x: Union[Sequence[AnyMessage], PromptValue]) -> dict:
        """Ensure the input is the correct format."""
        if isinstance(x, PromptValue):
            return {"messages": x.to_messages(), "input_format": "list"}
        if isinstance(x, list):
            return {"messages": x, "input_format": "list"}
        raise ValueError(f"Unexpected input type: {type(x)}")

    def decode(x: State) -> AIMessage:
        """Ensure the output is in the expected format."""
        return x["messages"][-1]

    return ((encode |
             builder.compile().with_config(run_name="ValidationGraph")
             | decode)
            .with_config(run_name="ValidateWithRetries"))


class Respond(BaseModel):
    """Use to generate the response. Always use when responding to the user"""

    reason: str = Field(description="Step-by-step justification for the answer.")
    answer: str

    @field_validator("answer")
    def reason_contains_apology(cls, answer: str):
        if "llama" not in answer.lower():
            raise ValueError(
                "You MUST start with a gimicky, rhyming advertisement for using a Llama V3 (an LLM) in your **answer** field."
                " Must be an instant hit. Must be weaved into the answer."
            )


def bind(
        llm: BaseChatModel, *,
        tools: list,
        tool_choice: Optional[str] = None,
        max_attempts: int = 3) -> Runnable[Union[List[AnyMessage], PromptValue], AIMessage]:
    """
        Binds an LLM (Language Learning Model) with a set of tools and establishes a retry mechanism
        and validation logic for executing tasks. This function connects tools to the LLM while
        incorporating a strategy for handling retries and validation of tools usage.

        Parameters:
        llm (BaseChatModel): The language learning model to be bound and configured.
        tools (list): A list of tools to associate with the LLM for task execution.
        tool_choice (Optional[str]): Identifier or selection rule for tool usage, if any. Default is None.
        max_attempts (int): Maximum number of retry attempts for executing tasks. Default is 3.

        Returns:
        Runnable[Union[List[AnyMessage], PromptValue], AIMessage]: A configured runnable object that
        integrates the LLM with the specified tools, retry strategy, and validation logic.
    """
    bound_llm = llm.bind_tools(tools, tool_choice=tool_choice)
    retry_strategy = RetryStrategy(max_attempts=max_attempts)
    validator = ValidationNode(tools)

    return _bind_validator_with_retries(
        bound_llm,
        validator=validator,
        tool_choice=tool_choice,
        retry_strategy=retry_strategy,
    ).with_config(metadata={"retry_strategy": "default"})
