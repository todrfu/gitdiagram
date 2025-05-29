from openai import OpenAI
from dotenv import load_dotenv
from app.utils.format_message import format_user_message
from app.services.ai_service_base import AIServiceBase
import tiktoken
import os
import aiohttp
import json
from typing import AsyncGenerator, Literal

load_dotenv()


class OpenAIo3Service(AIServiceBase):
    def __init__(self):
        self.default_client = OpenAI(
            api_key=os.getenv("OPENAI_API_KEY"),
        )
        self.encoding = tiktoken.get_encoding("o200k_base")  # Encoder for OpenAI models
        self.base_url = "https://api.openai.com/v1/chat/completions"

    def call_api(
        self,
        system_prompt: str,
        data: dict,
        api_key: str | None = None,
        reasoning_effort: Literal["low", "medium", "high"] = "low",
    ) -> str:
        """
        Makes an API call to OpenAI o3-mini and returns the response.

        Args:
            system_prompt (str): The instruction/system prompt
            data (dict): Dictionary of variables to format into the user message
            api_key (str | None): Optional custom API key
            reasoning_effort: Level of reasoning effort (low/medium/high)

        Returns:
            str: o3-mini's response text
        """
        # Create the user message with the data
        user_message = format_user_message(data)

        # Use custom client if API key provided, otherwise use default
        client = OpenAI(api_key=api_key) if api_key else self.default_client

        try:
            print(
                f"Making non-streaming API call to o3-mini with API key: {'custom key' if api_key else 'default key'}"
            )

            completion = client.chat.completions.create(
                model="o3-mini",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message},
                ],
                max_completion_tokens=12000,  # Adjust as needed
                temperature=0.2,
                reasoning_effort=reasoning_effort,
            )

            print("API call completed successfully")

            if completion.choices[0].message.content is None:
                raise ValueError("No content returned from OpenAI o3-mini")

            return completion.choices[0].message.content

        except Exception as e:
            print(f"Error in OpenAI o3-mini API call: {str(e)}")
            raise

    async def call_api_stream(
        self,
        system_prompt: str,
        data: dict,
        api_key: str | None = None,
        reasoning_effort: Literal["low", "medium", "high"] = "low",
    ) -> AsyncGenerator[str, None]:
        """
        Makes a streaming API call to OpenAI o3-mini and yields the responses.

        Args:
            system_prompt (str): The instruction/system prompt
            data (dict): Dictionary of variables to format into the user message
            api_key (str | None): Optional custom API key
            reasoning_effort: Level of reasoning effort (low/medium/high)

        Yields:
            str: Chunks of o3-mini's response text
        """
        # Create the user message with the data
        user_message = format_user_message(data)

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key or self.default_client.api_key}",
        }

        payload = {
            "model": "o3-mini",
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message},
            ],
            "max_completion_tokens": 12000,
            "stream": True,
            "reasoning_effort": reasoning_effort,
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
                            f"OpenAI API returned status code {response.status}: {error_text}"
                        )

                    line_count = 0
                    async for line in response.content:
                        line = line.decode("utf-8").strip()
                        if not line:
                            continue

                        line_count += 1

                        if line.startswith("data: "):
                            if line == "data: [DONE]":
                                break
                            try:
                                data = json.loads(line[6:])
                                content = (
                                    data.get("choices", [{}])[0]
                                    .get("delta", {})
                                    .get("content")
                                )
                                if content:
                                    yield content
                            except json.JSONDecodeError as e:
                                print(f"JSON decode error: {e} for line: {line}")
                                continue

                    if line_count == 0:
                        print("Warning: No lines received in stream response")

        except aiohttp.ClientError as e:
            print(f"Connection error: {str(e)}")
            raise ValueError(f"Failed to connect to OpenAI API: {str(e)}")
        except Exception as e:
            print(f"Unexpected error in streaming API call: {str(e)}")
            raise

    def count_tokens(self, prompt: str) -> int:
        """
        Counts the number of tokens in a prompt.

        Args:
            prompt (str): The prompt to count tokens for

        Returns:
            int: Estimated number of input tokens
        """
        num_tokens = len(self.encoding.encode(prompt))
        return num_tokens
