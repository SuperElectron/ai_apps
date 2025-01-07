from langchain_core.messages import (AIMessage, AnyMessage, ToolCall)
from langchain_core.prompt_values import PromptValue
from langchain_core.runnables import (Runnable, RunnableLambda)
from langchain_core.language_models import BaseChatModel
from langgraph.prebuilt import ValidationNode
from typing import (Any, Dict, List, Literal, Optional, Sequence, Type, Union)
from pydantic import BaseModel, Field
import logging

from pipeline.retry import _bind_validator_with_retries, RetryStrategy

logger = logging.getLogger("extraction")


def bind(
        llm: BaseChatModel,
        *,
        tools: list,
        tool_choice: Optional[str] = None,
        max_attempts: int = 3,
) -> Runnable[Union[List[AnyMessage], PromptValue], AIMessage]:
    """
    Binds a language model to a set of tools with enhanced JSONPatch-based retry capabilities,
    enabling operations for tool validation and error correction.

    This function combines multiple components such as JSONPatch utilities, a retry strategy,
     and validation mechanisms to ensure robust interactions with external tools. It supports
     automatic error correction through JSONPatch operations applied to tool call parameters.

    Parameters
    ----------
    llm : BaseChatModel
        The language model to be bound with tools.
    tools : list
        A list of tools to be bound with the language model.
    tool_choice : Optional[str], optional
        Specifies the selected tool if more than one exists. Default is None.
    max_attempts : int
        Maximum number of retry attempts for validation corrections. Default is 3.

    Returns
    -------
    Runnable[Union[List[AnyMessage], PromptValue], AIMessage]
        A callable object that integrates the bound language model, validator, and retry strategy.

    Raises
    ------
    ImportError
        If the 'jsonpatch' library is not installed, which is required for JSONPatch-based retries.
    """

    try:
        # type: ignore[import-untyped]
        import jsonpatch
    except ImportError:
        raise ImportError("The 'jsonpatch' library is required for JSONPatch-based retries.")

    class JsonPatch(BaseModel):
        """A JSON Patch document represents an operation to be performed on a JSON document.

        Note that the op and path are ALWAYS required. Value is required for ALL operations except 'remove'.
        Examples:

        ```json
        {"op": "add", "path": "/a/b/c", "patch_value": 1}
        {"op": "replace", "path": "/a/b/c", "patch_value": 2}
        {"op": "remove", "path": "/a/b/c"}
        ```
        """

        op: Literal["add", "remove", "replace"] = Field(
            ...,
            description="The operation to be performed. Must be one of 'add', 'remove', 'replace'.", )
        path: str = Field(
            ...,
            description="A JSON Pointer path that references a location within the target document where the operation is performed.",
        )
        value: Any = Field(
            ...,
            description="The value to be used within the operation. REQUIRED for 'add', 'replace', and 'test' operations.",
        )

    class PatchFunctionParameters(BaseModel):
        """Respond with all JSONPatch operation to correct validation errors caused by passing in incorrect or incomplete parameters in a previous tool call."""

        tool_call_id: str = Field(
            ...,
            description="The ID of the original tool call that generated the error. Must NOT be an ID of a PatchFunctionParameters tool call.",
        )
        reasoning: str = Field(
            ...,
            description="Think step-by-step, listing each validation error and the"
                        " JSONPatch operation needed to correct it. "
                        "Cite the fields in the JSONSchema you referenced in developing this plan.",
        )
        patches: list[JsonPatch] = Field(
            ...,
            description="A list of JSONPatch operations to be applied to the previous tool call's response.",
        )

    bound_llm = llm.bind_tools(tools, tool_choice=tool_choice)
    fallback_llm = llm.bind_tools([PatchFunctionParameters])

    def aggregate_messages(messages: Sequence[AnyMessage]) -> AIMessage:
        # Get all the AI messages and apply json patches
        resolved_tool_calls: Dict[Union[str, None], ToolCall] = {}
        content: Union[str, List[Union[str, dict]]] = ""
        for m in messages:
            if m.type != "ai":
                continue
            if not content:
                content = m.content
            for tc in m.tool_calls:
                if tc["name"] == PatchFunctionParameters.__name__:
                    tcid = tc["args"]["tool_call_id"]
                    if tcid not in resolved_tool_calls:
                        logger.debug(
                            f"JsonPatch tool call ID {tc['args']['tool_call_id']} not found."
                            f"Valid tool call IDs: {list(resolved_tool_calls.keys())}"
                        )
                        tcid = next(iter(resolved_tool_calls.keys()), None)
                    orig_tool_call = resolved_tool_calls[tcid]
                    current_args = orig_tool_call["args"]
                    patches = tc["args"].get("patches") or []
                    orig_tool_call["args"] = jsonpatch.apply_patch(
                        current_args,
                        patches,
                    )
                    orig_tool_call["id"] = tc["id"]
                else:
                    resolved_tool_calls[tc["id"]] = tc.copy()
        return AIMessage(
            content=content,
            tool_calls=list(resolved_tool_calls.values()),
        )

    def format_exception(error: BaseException, call: ToolCall, schema: Type[BaseModel]):
        return (
                f"Error:\n\n```\n{repr(error)}\n```\n"
                "Expected Parameter Schema:\n\n" + f"```json\n{schema.schema_json()}\n```\n"
                                                   f"Please respond with a JSONPatch to correct the error for tool_call_id=[{call['id']}]."
        )

    validator = ValidationNode(
        tools + [PatchFunctionParameters],
        format_error=format_exception,
    )
    retry_strategy = RetryStrategy(
        max_attempts=max_attempts,
        fallback=fallback_llm,
        aggregate_messages=aggregate_messages,
    )
    return _bind_validator_with_retries(
        bound_llm,
        validator=validator,
        retry_strategy=retry_strategy,
        tool_choice=tool_choice,
    ).with_config(metadata={"retry_strategy": "jsonpatch"})
