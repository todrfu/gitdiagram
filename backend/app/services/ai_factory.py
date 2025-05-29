from app.services.ai_service_base import AIServiceBase
from app.services.o3_mini_openai_service import OpenAIo3Service
from app.services.o4_mini_openai_service import OpenAIo4Service
from app.services.claude_service import ClaudeService
from app.services.deepseek_service import DeepSeekService
from typing import Optional, Dict, Any


class AIServiceFactory:
    """
    AI服务工厂类，根据AI平台类型返回相应的服务实现
    """
    
    @staticmethod
    def create_service(
        platform: str, 
        api_key: Optional[str] = None, 
        model: Optional[str] = None
    ) -> AIServiceBase:
        """
        创建并返回AI服务实例
        
        Args:
            platform: AI平台标识符，如'openai'、'claude'、'deepseek'
            api_key: API密钥（可选）
            model: 模型名称（可选）
            
        Returns:
            AIServiceBase: 相应平台的AI服务实现
            
        Raises:
            ValueError: 如果平台不受支持
        """
        platform = platform.lower()
        
        if platform == 'openai':
            if model and model.startswith('o4'):
                return OpenAIo4Service()
            else:
                return OpenAIo3Service()
        elif platform == 'claude':
            return ClaudeService()
        elif platform == 'deepseek':
            return DeepSeekService()
        else:
            raise ValueError(f"不支持的AI平台: {platform}")
            
    @staticmethod
    def get_available_platforms() -> Dict[str, Dict[str, Any]]:
        """
        获取所有可用的AI平台及其模型信息
        
        Returns:
            Dict[str, Dict[str, Any]]: 平台名称到平台信息的映射
        """
        return {
            "openai": {
                "name": "OpenAI",
                "models": ["o3-mini", "o4-mini"],
                "default_model": "o3-mini",
                "description": "OpenAI提供的AI模型",
                "requires_api_key": True
            },
            "claude": {
                "name": "Claude",
                "models": ["claude-3-5-sonnet"],
                "default_model": "claude-3-5-sonnet",
                "description": "Anthropic提供的Claude AI模型",
                "requires_api_key": True
            },
            "deepseek": {
                "name": "DeepSeek",
                "models": ["deepseek-chat"],
                "default_model": "deepseek-chat",
                "description": "DeepSeek提供的AI模型",
                "requires_api_key": True
            }
        }
        
    @staticmethod
    def get_reasoning_effort_options() -> Dict[str, str]:
        """
        获取推理努力程度选项
        
        Returns:
            Dict[str, str]: 推理努力程度选项的名称和描述
        """
        return {
            "low": "低 - 速度更快，但质量可能较低",
            "medium": "中 - 平衡速度和质量",
            "high": "高 - 质量更好，但速度较慢"
        } 