import requests
import os
from dotenv import load_dotenv
from app.services.git_service import GitService
import base64

load_dotenv()


class GitLabService(GitService):
    """GitLab API服务实现类，用于获取GitLab仓库信息"""
    
    def __init__(self, pat: str | None = None, base_url: str | None = None):
        # 使用提供的PAT或环境变量中的PAT
        self.gitlab_token = pat or os.getenv("GITLAB_PAT")
        
        # 支持自定义GitLab实例URL
        self.base_url = base_url or os.getenv("GITLAB_API_URL", "https://gitlab.com/api/v4")
        
        if not self.gitlab_token:
            print(
                "\033[93mWarning: No GitLab token provided. Using unauthenticated requests with severe rate limits.\033[0m"
            )
    
    def _get_headers(self):
        headers = {"Accept": "application/json"}
        if self.gitlab_token:
            headers["PRIVATE-TOKEN"] = self.gitlab_token
        return headers
    
    def check_repository_exists(self, username, repo):
        """检查仓库是否存在"""
        # 在GitLab中，需要使用URL编码的路径
        path = f"{username}/{repo}"
        encoded_path = requests.utils.quote(path, safe='')
        
        api_url = f"{self.base_url}/projects/{encoded_path}"
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
        path = f"{username}/{repo}"
        encoded_path = requests.utils.quote(path, safe='')
        
        api_url = f"{self.base_url}/projects/{encoded_path}"
        response = requests.get(api_url, headers=self._get_headers())
        
        if response.status_code == 200:
            return response.json().get("default_branch")
        return None
    
    def get_file_tree(self, username, repo):
        """获取仓库的文件树"""
        path = f"{username}/{repo}"
        encoded_path = requests.utils.quote(path, safe='')
        branch = self.get_default_branch(username, repo) or "main"
        
        # GitLab API不提供递归树，我们需要使用repository/tree端点
        api_url = f"{self.base_url}/projects/{encoded_path}/repository/tree"
        params = {"recursive": "true", "ref": branch, "per_page": 100}
        
        all_files = []
        page = 1
        
        # 处理分页
        while True:
            params["page"] = page
            response = requests.get(api_url, headers=self._get_headers(), params=params)
            
            if response.status_code != 200:
                break
                
            items = response.json()
            if not items:
                break
                
            # 只保留类型为'blob'的文件
            files = [item["path"] for item in items if item["type"] == "blob" and self.should_include_file(item["path"])]
            all_files.extend(files)
            
            # 检查是否有下一页
            if 'X-Next-Page' in response.headers and response.headers['X-Next-Page']:
                page = int(response.headers['X-Next-Page'])
            else:
                break
        
        if not all_files:
            raise ValueError(
                "Could not fetch repository file tree. Repository might not exist, be empty or private."
            )
            
        return "\n".join(all_files)
    
    def get_readme(self, username, repo):
        """获取仓库的README内容"""
        if not self.check_repository_exists(username, repo):
            raise ValueError("Repository does not exist.")
            
        path = f"{username}/{repo}"
        encoded_path = requests.utils.quote(path, safe='')
        branch = self.get_default_branch(username, repo) or "main"
        
        # 尝试常见的README文件名
        readme_filenames = ["README.md", "README", "README.txt", "Readme.md"]
        
        for filename in readme_filenames:
            api_url = f"{self.base_url}/projects/{encoded_path}/repository/files/{requests.utils.quote(filename, safe='')}"
            params = {"ref": branch}
            
            response = requests.get(api_url, headers=self._get_headers(), params=params)
            
            if response.status_code == 200:
                data = response.json()
                # GitLab API返回base64编码的内容
                content = base64.b64decode(data["content"]).decode("utf-8")
                return content
        
        raise ValueError("No README found for the specified repository.")
    
    def get_file_url(self, username, repo, path, branch):
        """生成文件URL，用于点击事件"""
        return f"https://gitlab.com/{username}/{repo}/-/blob/{branch}/{path}"
    
    def get_directory_url(self, username, repo, path, branch):
        """生成目录URL，用于点击事件"""
        return f"https://gitlab.com/{username}/{repo}/-/tree/{branch}/{path}" 