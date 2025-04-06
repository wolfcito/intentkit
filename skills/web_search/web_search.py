import logging
from typing import Type, Optional

import httpx
from langchain_core.runnables import RunnableConfig
from pydantic import BaseModel, Field

from skills.web_search.base import WebSearchBaseTool

logger = logging.getLogger(__name__)


class WebSearchInput(BaseModel):
    """Input for WebSearch tool."""

    query: str = Field(
        description="The search query to look up on the web.",
    )
    max_results: int = Field(
        description="Maximum number of search results to return (1-10).",
        default=5,
        ge=1,
        le=10,
    )
    include_images: bool = Field(
        description="Whether to include image URLs in the results.",
        default=False,
    )
    include_raw_content: bool = Field(
        description="Whether to include raw HTML content in the results.",
        default=False,
    )


class WebSearch(WebSearchBaseTool):
    """Tool for searching the web.

    This tool uses Tavily's search API to search the web and return relevant results.

    Attributes:
        name: The name of the tool.
        description: A description of what the tool does.
        args_schema: The schema for the tool's input arguments.
    """

    name: str = "web_search"
    description: str = (
        "Search the web for current information on a topic. Use this tool when you need to find"
        " up-to-date information, facts, news, or any content available online.\n"
        "You must call this tool whenever the user asks for information that may not be in your training data,"
        " requires current data, or when you're unsure about facts."
    )
    args_schema: Type[BaseModel] = WebSearchInput

    async def _arun(
        self, 
        query: str, 
        max_results: int = 5, 
        include_images: bool = False, 
        include_raw_content: bool = False, 
        config: RunnableConfig = None, 
        **kwargs
    ) -> str:
        """Implementation of the web search tool.

        Args:
            query: The search query to look up.
            max_results: Maximum number of search results to return (1-10).
            include_images: Whether to include image URLs in the results.
            include_raw_content: Whether to include raw HTML content in the results.
            config: The configuration for the tool call.

        Returns:
            str: Formatted search results with titles, snippets, and URLs.
        """
        context = self.context_from_config(config)
        logger.debug(f"web_search.py: Running web search with context {context}")
        
        # Get the API key from the agent's configuration
        api_key = context.config.get("api_key")
        if not api_key:
            return "Error: No Tavily API key provided in the configuration."
        
        # Limit max_results to a reasonable range
        max_results = max(1, min(max_results, 10))
        
        # Call Tavily search API
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    "https://api.tavily.com/search",
                    json={
                        "api_key": api_key,
                        "query": query,
                        "max_results": max_results,
                        "include_images": include_images,
                        "include_raw_content": include_raw_content,
                    },
                )
                
                if response.status_code != 200:
                    logger.error(f"web_search.py: Error from Tavily API: {response.status_code} - {response.text}")
                    return f"Error searching the web: {response.status_code} - {response.text}"
                
                data = response.json()
                results = data.get("results", [])
                
                if not results:
                    return f"No results found for query: '{query}'"
                
                # Format the results
                formatted_results = f"Web search results for: '{query}'\n\n"
                
                for i, result in enumerate(results, 1):
                    title = result.get("title", "No title")
                    content = result.get("content", "No content")
                    url = result.get("url", "No URL")
                    
                    formatted_results += f"{i}. {title}\n"
                    formatted_results += f"{content}\n"
                    formatted_results += f"Source: {url}\n\n"
                
                return formatted_results.strip()
                
        except Exception as e:
            logger.error(f"web_search.py: Error searching web: {e}")
            return f"Error occurred while searching the web: {str(e)}" 