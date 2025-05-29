from openai import OpenAI as DeepSeekAPI
from dotenv import load_dotenv
from app.utils.format_message import format_user_message
from app.services.ai_service_base import AIServiceBase
import os
import aiohttp
import json
import tiktoken
from typing import AsyncGenerator, Literal

load_dotenv()

class DeepSeekService(AIServiceBase):
    def __init__(self):
        self.default_client = DeepSeekAPI(
            api_key=os.getenv("DEEPSEEK_API_KEY"),
        )
        # 尝试使用适合DeepSeek模型的编码器或默认值
        try:
            self.encoding = tiktoken.get_encoding("cl100k_base")  # 可能需要根据DeepSeek的要求调整
        except:
            self.encoding = tiktoken.get_encoding("gpt2")  # 兜底使用通用编码器
            
        self.base_url = "https://api.deepseek.com/v1/chat/completions"  # DeepSeek API端点
        self.default_model = "deepseek-chat"  # 默认模型名称

    def call_api(
        self,
        system_prompt: str,
        data: dict,
        api_key: str | None = None,
        reasoning_effort: Literal["low", "medium", "high"] = "medium",
    ) -> str:
        """
        调用DeepSeek API并返回响应。
        
        Args:
            system_prompt (str): 系统提示/指令
            data (dict): 用于格式化用户消息的变量字典
            api_key (str | None): 可选的自定义API密钥
            reasoning_effort: 推理努力程度（由于DeepSeek可能不支持此参数，可能会被忽略）
            
        Returns:
            str: DeepSeek的响应文本
        """
        # 创建用户消息
        user_message = format_user_message(data)
        
        # 使用自定义API密钥或默认客户端
        client = DeepSeekAPI(api_key=api_key) if api_key else self.default_client
        
        try:
            print(f"调用DeepSeek API，使用API密钥: {'自定义密钥' if api_key else '默认密钥'}")
            
            # 转换reasoning_effort为temperature
            temp_map = {"low": 0.7, "medium": 0.5, "high": 0.2}
            temperature = temp_map.get(reasoning_effort, 0.5)
            
            # 调用DeepSeek API
            completion = client.chat.completions.create(
                model=self.default_model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message},
                ],
                max_tokens=4000,  # 根据DeepSeek限制调整
                temperature=temperature,
            )
            
            print("API调用成功完成")
            
            if completion.choices[0].message.content is None:
                raise ValueError("DeepSeek没有返回内容")
                
            return completion.choices[0].message.content
            
        except Exception as e:
            print(f"DeepSeek API调用错误: {str(e)}")
            raise

    async def call_api_stream(
        self,
        system_prompt: str,
        data: dict,
        api_key: str | None = None,
        reasoning_effort: Literal["low", "medium", "high"] = "medium",
    ) -> AsyncGenerator[str, None]:
        """
        以流式方式调用DeepSeek API并生成响应。
        
        Args:
            system_prompt (str): 系统提示/指令
            data (dict): 用于格式化用户消息的变量字典
            api_key (str | None): 可选的自定义API密钥
            reasoning_effort: 推理努力程度
            
        Yields:
            str: DeepSeek响应文本的片段
        """
        # 创建用户消息
        user_message = format_user_message(data)
        
        # 准备API请求头
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key or os.getenv('DEEPSEEK_API_KEY')}",
        }
        
        # 转换reasoning_effort为temperature
        temp_map = {"low": 0.7, "medium": 0.5, "high": 0.2}
        temperature = temp_map.get(reasoning_effort, 0.5)
        
        # 准备请求负载
        payload = {
            "model": self.default_model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message},
            ],
            "max_tokens": 4000,
            "temperature": temperature,
            "stream": True,
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.base_url, headers=headers, json=payload
                ) as response:
                    
                    if response.status != 200:
                        error_text = await response.text()
                        print(f"错误响应: {error_text}")
                        raise ValueError(
                            f"DeepSeek API返回状态码 {response.status}: {error_text}"
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
                                print(f"JSON解码错误: {e} 行内容: {line}")
                                continue
                                
                    if line_count == 0:
                        print("警告: 流响应中没有收到行")
                        
        except aiohttp.ClientError as e:
            print(f"连接错误: {str(e)}")
            raise ValueError(f"无法连接到DeepSeek API: {str(e)}")
        except Exception as e:
            print(f"流式API调用中出现意外错误: {str(e)}")
            raise
            
    def count_tokens(self, prompt: str) -> int:
        """
        计算提示中的令牌数量。
        
        Args:
            prompt (str): 要计算令牌的提示
            
        Returns:
            int: 输入令牌的估计数量
        """
        try:
            # 使用tiktoken估算令牌数
            num_tokens = len(self.encoding.encode(prompt))
            return num_tokens
        except Exception as e:
            print(f"计算令牌时出错: {str(e)}")
            # 如果无法使用tiktoken，回退到简单的估算方法
            return len(prompt.split()) * 4  # 粗略估计 