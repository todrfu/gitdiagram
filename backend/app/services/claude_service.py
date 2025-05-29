from anthropic import Anthropic
from dotenv import load_dotenv
from app.utils.format_message import format_user_message
from app.services.ai_service_base import AIServiceBase
from typing import AsyncGenerator, Literal
import aiohttp
import json
import os

load_dotenv()


class ClaudeService(AIServiceBase):
    def __init__(self):
        self.default_client = Anthropic()
        self.base_url = "https://api.anthropic.com/v1/messages"

    def call_api(
        self, 
        system_prompt: str, 
        data: dict, 
        api_key: str | None = None,
        reasoning_effort: Literal["low", "medium", "high"] = "medium",
    ) -> str:
        """
        Makes an API call to Claude and returns the response.

        Args:
            system_prompt (str): The instruction/system prompt
            data (dict): Dictionary of variables to format into the user message
            api_key (str | None): Optional custom API key
            reasoning_effort: Level of reasoning effort (adjusts temperature)

        Returns:
            str: Claude's response text
        """
        # Create the user message with the data
        user_message = format_user_message(data)

        # Use custom client if API key provided, otherwise use default
        client = Anthropic(api_key=api_key) if api_key else self.default_client
        
        # 根据reasoning_effort调整temperature
        temp_map = {"low": 0.7, "medium": 0.3, "high": 0}
        temperature = temp_map.get(reasoning_effort, 0.3)

        message = client.messages.create(
            model="claude-3-5-sonnet-latest",
            max_tokens=4096,
            temperature=temperature,
            system=system_prompt,
            messages=[
                {"role": "user", "content": [{"type": "text", "text": user_message}]}
            ],
        )
        return message.content[0].text  # type: ignore

    async def call_api_stream(
        self,
        system_prompt: str,
        data: dict,
        api_key: str | None = None,
        reasoning_effort: Literal["low", "medium", "high"] = "medium",
    ) -> AsyncGenerator[str, None]:
        """
        Makes a streaming API call to Claude and yields the responses.

        Args:
            system_prompt (str): The instruction/system prompt
            data (dict): Dictionary of variables to format into the user message
            api_key (str | None): Optional custom API key
            reasoning_effort: Level of reasoning effort (adjusts temperature)

        Yields:
            str: Chunks of Claude's response text
        """
        # Create the user message with the data
        user_message = format_user_message(data)
        
        # 根据reasoning_effort调整temperature
        temp_map = {"low": 0.7, "medium": 0.3, "high": 0}
        temperature = temp_map.get(reasoning_effort, 0.3)
        
        headers = {
            "Content-Type": "application/json",
            "x-api-key": api_key or os.getenv("ANTHROPIC_API_KEY", ""),
            "anthropic-version": "2023-06-01",
        }
        
        payload = {
            "model": "claude-3-5-sonnet-latest",
            "max_tokens": 4096,
            "temperature": temperature,
            "system": system_prompt,
            "messages": [
                {"role": "user", "content": [{"type": "text", "text": user_message}]}
            ],
            "stream": True,
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.base_url, headers=headers, json=payload
                ) as response:
                    
                    if response.status != 200:
                        error_text = await response.text()
                        print(f"Error response: {error_text}")
                        raise ValueError(
                            f"Claude API returned status code {response.status}: {error_text}"
                        )
                    
                    async for line in response.content:
                        line = line.decode("utf-8").strip()
                        if not line or line == "event: ping":
                            continue
                            
                        if line.startswith("data: "):
                            if line == "data: [DONE]":
                                break
                            try:
                                data = json.loads(line[6:])
                                if data.get("type") == "content_block_delta":
                                    content = data.get("delta", {}).get("text", "")
                                    if content:
                                        yield content
                            except json.JSONDecodeError as e:
                                print(f"JSON decode error: {e} for line: {line}")
                                continue
                                
        except aiohttp.ClientError as e:
            print(f"Connection error: {str(e)}")
            raise ValueError(f"Failed to connect to Claude API: {str(e)}")
        except Exception as e:
            print(f"Unexpected error in streaming API call: {str(e)}")
            raise

    def count_tokens(self, prompt: str) -> int:
        """
        Counts the number of tokens in a prompt.

        Args:
            prompt (str): The prompt to count tokens for

        Returns:
            int: Number of input tokens
        """
        response = self.default_client.messages.count_tokens(
            model="claude-3-5-sonnet-latest",
            messages=[{"role": "user", "content": prompt}],
        )
        return response.input_tokens
