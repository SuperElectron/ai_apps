from typing import (Callable, Optional, Sequence, Union)
from typing_extensions import TypedDict
from langchain_core.messages import (AIMessage, AnyMessage, BaseMessage, HumanMessage)
from langchain_core.runnables import (Runnable, RunnableLambda)


class RetryStrategy(TypedDict, total=False):
    """The retry strategy for a tool call."""

    max_attempts: int
    """The maximum number of attempts to make."""
    fallback: Optional[
        Union[
            Runnable[Sequence[AnyMessage], AIMessage],
            Runnable[Sequence[AnyMessage], BaseMessage],
            Callable[[Sequence[AnyMessage]], AIMessage],
        ]
    ]
    """The function to use once validation fails."""
    aggregate_messages: Optional[Callable[[Sequence[AnyMessage]], AIMessage]]
