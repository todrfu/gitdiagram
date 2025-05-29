import requests
import os
from dotenv import load_dotenv
from app.services.git_service import GitService
import base64

load_dotenv()


class GiteaService(GitService):
    """Gitea API服务实现类，用于获取Gitea仓库信息"""
    
    def __init__(self, pat: str | None = None, base_url: str | None = None):
        # 使用提供的PAT或环境变量中的PAT
        self.gitea_token = pat or os.getenv("GITEA_PAT")
        
        # 支持自定义Gitea实例URL
        self.base_url = base_url or os.getenv("GITEA_API_URL", "https://gitea.com/api/v1")
        
        if not self.gitea_token:
            print(
                "\033[93mWarning: No Gitea token provided. Using unauthenticated requests with severe rate limits.\033[0m"
            )
    
    def _get_headers(self):
        headers = {"Accept": "application/json"}
        if self.gitea_token:
            headers["Authorization"] = f"token {self.gitea_token}"
        return headers
    
    def check_repository_exists(self, username, repo):
        """检查仓库是否存在"""
        api_url = f"{self.base_url}/repos/{username}/{repo}"
        response = requests.get(api_url, headers=self._get_headers())
        
        if response.status_code == 404:
            return False
        elif response.status_code != 200:
            raise Exception(
                f"Failed to check repository: {response.status_code}, {response.text}"
            )
        return True
    
    def get_default_branch(self, username, repo):
        """获取仓库的默认分支"""
        api_url = f"{self.base_url}/repos/{username}/{repo}"
        response = requests.get(api_url, headers=self._get_headers())
        
        if response.status_code == 200:
            return response.json().get("default_branch")
        return None
    
    def get_file_tree(self, username, repo):
        """获取仓库的文件树"""
        branch = self.get_default_branch(username, repo) or "main"
        
        # Gitea API获取文件树
        api_url = f"{self.base_url}/repos/{username}/{repo}/git/trees/{branch}?recursive=1"
        response = requests.get(api_url, headers=self._get_headers())
        
        if response.status_code != 200:
            raise ValueError(
                "Could not fetch repository file tree. Repository might not exist, be empty or private."
            )
        
        data = response.json()
        if "tree" in data:
            # 过滤文件路径
            paths = [
                item["path"]
                for item in data["tree"]
                if self.should_include_file(item["path"])
            ]
            return "\n".join(paths)
        
        raise ValueError("Could not fetch repository file tree. Invalid response format.")
    
    def get_readme(self, username, repo):
        """获取仓库的README内容"""
        if not self.check_repository_exists(username, repo):
            raise ValueError("Repository does not exist.")
            
        branch = self.get_default_branch(username, repo) or "main"
        
        # 尝试常见的README文件名
        readme_filenames = ["README.md", "README", "README.txt", "Readme.md"]
        
        for filename in readme_filenames:
            api_url = f"{self.base_url}/repos/{username}/{repo}/contents/{filename}"
            params = {"ref": branch}
            
            response = requests.get(api_url, headers=self._get_headers(), params=params)
            
            if response.status_code == 200:
                data = response.json()
                if "content" in data:
                    # 内容通常是base64编码
                    content = base64.b64decode(data["content"]).decode("utf-8")
                    return content
                
        raise ValueError("No README found for the specified repository.")
    
    def get_file_url(self, username, repo, path, branch):
        """生成文件URL，用于点击事件"""
        # 从API URL提取基础域名
        domain = self.base_url.split('/api/')[0]
        if not domain.startswith('http'):
            domain = f"https://{domain}"
        return f"{domain}/{username}/{repo}/src/branch/{branch}/{path}"
    
    def get_directory_url(self, username, repo, path, branch):
        """生成目录URL，用于点击事件"""
        # 从API URL提取基础域名
        domain = self.base_url.split('/api/')[0]
        if not domain.startswith('http'):
            domain = f"https://{domain}"
        return f"{domain}/{username}/{repo}/src/branch/{branch}/{path}" 