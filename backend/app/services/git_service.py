from abc import ABC, abstractmethod
from typing import Optional


class GitService(ABC):
    """
    抽象基类，定义所有Git平台服务通用的接口。
    不同的Git平台（如GitHub、GitLab等）都应实现这个接口。
    """
    
    @abstractmethod
    def get_default_branch(self, username: str, repo: str) -> Optional[str]:
        """获取仓库的默认分支"""
        pass
    
    @abstractmethod
    def get_file_tree(self, username: str, repo: str) -> str:
        """获取仓库的文件树，返回格式化的文件路径列表"""
        pass
    
    @abstractmethod
    def get_readme(self, username: str, repo: str) -> str:
        """获取仓库的README内容"""
        pass
    
    @abstractmethod
    def check_repository_exists(self, username: str, repo: str) -> bool:
        """检查仓库是否存在"""
        pass
    
    @abstractmethod
    def get_file_url(self, username: str, repo: str, path: str, branch: str) -> str:
        """生成文件URL，用于点击事件"""
        pass
    
    @abstractmethod
    def get_directory_url(self, username: str, repo: str, path: str, branch: str) -> str:
        """生成目录URL，用于点击事件"""
        pass
    
    @staticmethod
    def should_include_file(path: str) -> bool:
        """判断文件是否应该包含在分析中"""
        # 通用的文件过滤逻辑，所有平台都可以使用
        excluded_patterns = [
            # Dependencies
            "node_modules/",
            "vendor/",
            "venv/",
            # Compiled files
            ".min.",
            ".pyc",
            ".pyo",
            ".pyd",
            ".so",
            ".dll",
            ".class",
            # Asset files
            ".jpg",
            ".jpeg",
            ".png",
            ".gif",
            ".ico",
            ".svg",
            ".ttf",
            ".woff",
            ".webp",
            # Cache and temporary files
            "__pycache__/",
            ".cache/",
            ".tmp/",
            # Lock files and logs
            "yarn.lock",
            "poetry.lock",
            "*.log",
            # Configuration files
            ".vscode/",
            ".idea/",
        ]
        
        return not any(pattern in path.lower() for pattern in excluded_patterns) 