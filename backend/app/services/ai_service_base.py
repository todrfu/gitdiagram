from abc import ABC, abstractmethod
from typing import AsyncGenerator, Literal

class AIServiceBase(ABC):
    """
    AI服务基类，定义所有AI服务实现必须提供的接口
    """
    
    @abstractmethod
    def call_api(
        self,
        system_prompt: str,
        data: dict,
        api_key: str | None = None,
        reasoning_effort: Literal["low", "medium", "high"] = "medium",
    ) -> str:
        """
        调用AI平台API并返回响应
        
        Args:
            system_prompt (str): 系统提示/指令
            data (dict): 用于格式化用户消息的变量字典
            api_key (str | None): 可选的自定义API密钥
            reasoning_effort: 推理努力程度 (低/中/高)
            
        Returns:
            str: AI的响应文本
        """
        pass
    
    @abstractmethod
    async def call_api_stream(
        self,
        system_prompt: str,
        data: dict,
        api_key: str | None = None,
        reasoning_effort: Literal["low", "medium", "high"] = "medium",
    ) -> AsyncGenerator[str, None]:
        """
        以流式方式调用AI平台API并生成响应
        
        Args:
            system_prompt (str): 系统提示/指令
            data (dict): 用于格式化用户消息的变量字典
            api_key (str | None): 可选的自定义API密钥
            reasoning_effort: 推理努力程度 (低/中/高)
            
        Yields:
            str: AI响应文本的片段
        """
        pass
    
    @abstractmethod
    def count_tokens(self, prompt: str) -> int:
        """
        计算提示中的令牌数量
        
        Args:
            prompt (str): 要计算令牌的提示
            
        Returns:
            int: 输入令牌的估计数量
        """
        pass 