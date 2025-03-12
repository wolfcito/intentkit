"""Core API Router.

This module provides the core API endpoints for agent execution and management.
"""

from typing import Annotated

from fastapi import APIRouter, Body
from pydantic import AfterValidator

from app.core.engine import execute_agent
from models.chat import ChatMessage, ChatMessageCreate

core_router = APIRouter(prefix="/core", tags=["core"])


@core_router.post("/execute", response_model=list[ChatMessage])
async def execute(
    message: Annotated[
        ChatMessageCreate, AfterValidator(ChatMessageCreate.model_validate)
    ] = Body(
        ChatMessageCreate,
        description="The chat message containing agent_id, chat_id and message content",
    ),
) -> list[ChatMessage]:
    """Execute an agent with the given input and return response lines.

    **Request Body:**
    * `message` - The chat message containing agent_id, chat_id and message content

    **Returns:**
    * `list[ChatMessage]` - Formatted response lines from agent execution

    **Raises:**
    * `HTTPException`:
        - 400: If input parameters are invalid
        - 404: If agent not found
        - 500: For other server-side errors
    """
    return await execute_agent(message)
