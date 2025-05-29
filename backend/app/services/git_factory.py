from app.services.git_service import GitService
from app.services.github_service import GitHubService
from app.services.gitlab_service import GitLabService
from app.services.gitea_service import GiteaService
from typing import Optional


class GitServiceFactory:
    """
    Git服务工厂类，根据平台类型返回相应的Git服务实现
    """
    
    @staticmethod
    def create_service(platform: str, token: Optional[str] = None, base_url: Optional[str] = None) -> GitService:
        """
        创建并返回Git服务实例
        
        Args:
            platform: 平台标识符，如'github'、'gitlab'、'gitea'
            token: 访问令牌（可选）
            base_url: API基础URL（可选，用于自定义实例）
            
        Returns:
            GitService: 相应平台的Git服务实现
            
        Raises:
            ValueError: 如果平台不受支持
        """
        platform = platform.lower()
        
        if platform == 'github':
            return GitHubService(pat=token)
        elif platform == 'gitlab':
            return GitLabService(pat=token, base_url=base_url)
        elif platform == 'gitea':
            return GiteaService(pat=token, base_url=base_url)
        else:
            raise ValueError(f"Unsupported platform: {platform}") 