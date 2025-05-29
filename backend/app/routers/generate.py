from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import StreamingResponse
from dotenv import load_dotenv
import os
from app.services.git_factory import GitServiceFactory
from app.services.ai_factory import AIServiceFactory
from app.prompts import (
    SYSTEM_FIRST_PROMPT,
    SYSTEM_SECOND_PROMPT,
    SYSTEM_THIRD_PROMPT,
    ADDITIONAL_SYSTEM_INSTRUCTIONS_PROMPT,
)
from anthropic._exceptions import RateLimitError
from pydantic import BaseModel
from functools import lru_cache
import re
import json
import asyncio
from typing import Literal, Dict, Any

load_dotenv()

router = APIRouter(prefix="/generate", tags=["AI Diagram Generation"])

# 获取默认AI平台和模型配置
DEFAULT_AI_PLATFORM = os.getenv("DEFAULT_AI_PLATFORM", "openai")
DEFAULT_AI_MODEL = os.getenv("DEFAULT_AI_MODEL", "o3-mini")
DEFAULT_REASONING_EFFORT = os.getenv("DEFAULT_REASONING_EFFORT", "medium")

# 获取AI服务价格配置
AI_PRICING = {
    "openai": {
        "o3-mini": {"input": 0.0000011, "output": 0.0000044},
        "o4-mini": {"input": 0.0000011, "output": 0.0000044},
    },
    "claude": {"claude-3-5-sonnet": {"input": 0.000003, "output": 0.000015}},
    "deepseek": {"deepseek-chat": {"input": 0.000001, "output": 0.000003}},
}

# 获取AI服务令牌限制
AI_TOKEN_LIMITS = {
    "openai": {"o3-mini": 195000, "o4-mini": 195000},
    "claude": {"claude-3-5-sonnet": 180000},
    "deepseek": {"deepseek-chat": 128000},
}

# cache git data to avoid double API calls from cost and generate
@lru_cache(maxsize=100)
def get_cached_git_data(platform: str, username: str, repo: str, token: str | None = None, base_url: str | None = None):
    # 使用工厂创建适当的Git服务
    git_service = GitServiceFactory.create_service(platform, token, base_url)

    default_branch = git_service.get_default_branch(username, repo)
    if not default_branch:
        default_branch = "main"  # fallback value

    file_tree = git_service.get_file_tree(username, repo)
    readme = git_service.get_readme(username, repo)

    return {"default_branch": default_branch, "file_tree": file_tree, "readme": readme, "service": git_service}


class ApiRequest(BaseModel):
    platform: str = "github"  # 默认为GitHub
    username: str
    repo: str
    instructions: str = ""
    api_key: str | None = None
    git_token: str | None = None  # 通用的Git平台令牌
    git_api_url: str | None = None  # 自定义Git API URL
    ai_platform: str | None = None  # AI平台: openai, claude, deepseek
    ai_model: str | None = None  # AI模型，根据平台不同而不同
    reasoning_effort: Literal["low", "medium", "high"] | None = None  # 推理努力程度


@router.post("/cost")
# @limiter.limit("5/minute") # TEMP: disable rate limit for growth??
async def get_generation_cost(request: Request, body: ApiRequest):
    try:
        # 获取AI平台配置
        ai_platform = body.ai_platform or DEFAULT_AI_PLATFORM
        print(f"ai_platform: {ai_platform}")
        ai_model = body.ai_model or DEFAULT_AI_MODEL
        
        # 创建AI服务
        ai_service = AIServiceFactory.create_service(ai_platform, body.api_key, ai_model)

        # Get file tree and README content
        github_data = get_cached_git_data(
            body.platform, body.username, body.repo, body.git_token, body.git_api_url
        )
        file_tree = github_data["file_tree"]
        readme = github_data["readme"]

        # Calculate combined token count
        file_tree_tokens = ai_service.count_tokens(file_tree)
        readme_tokens = ai_service.count_tokens(readme)

        # 获取平台对应的价格
        if ai_platform in AI_PRICING and ai_model in AI_PRICING[ai_platform]:
            pricing = AI_PRICING[ai_platform][ai_model]
            input_cost = ((file_tree_tokens * 2 + readme_tokens) + 3000) * pricing["input"]
            output_cost = 8000 * pricing["output"]  # 8k tokens 的估计输出量
            estimated_cost = input_cost + output_cost
        else:
            # 默认OpenAI o3-mini价格
            input_cost = ((file_tree_tokens * 2 + readme_tokens) + 3000) * 0.0000011
            output_cost = 8000 * 0.0000044
            estimated_cost = input_cost + output_cost

        # Format as currency string
        cost_string = f"${estimated_cost:.2f} USD"
        return {"cost": cost_string}
    except Exception as e:
        return {"error": str(e)}


def process_click_events(diagram: str, platform: str, username: str, repo: str, branch: str, git_service) -> str:
    """
    Process click events in Mermaid diagram to include full Git URLs.
    Detects if path is file or directory and uses appropriate URL format.
    """

    def replace_path(match):
        # Extract the path from the click event
        path = match.group(2).strip("\"'")

        # Determine if path is likely a file (has extension) or directory
        is_file = "." in path.split("/")[-1]

        # Construct Git URL based on platform
        if is_file:
            full_url = git_service.get_file_url(username, repo, path, branch)
        else:
            full_url = git_service.get_directory_url(username, repo, path, branch)

        # Return the full click event with the new URL
        return f'click {match.group(1)} "{full_url}"'

    # Match click events: click ComponentName "path/to/something"
    click_pattern = r'click ([^\s"]+)\s+"([^"]+)"'
    return re.sub(click_pattern, replace_path, diagram)


@router.post("/stream")
async def generate_stream(request: Request, body: ApiRequest):
    try:
        # Initial validation checks
        if len(body.instructions) > 1000:
            return {"error": "Instructions exceed maximum length of 1000 characters"}

        if body.repo in [
            "fastapi",
            "streamlit",
            "flask",
            "api-analytics",
            "monkeytype",
        ]:
            return {"error": "Example repos cannot be regenerated"}

        # 获取AI平台配置
        ai_platform = body.ai_platform or DEFAULT_AI_PLATFORM
        ai_model = body.ai_model or DEFAULT_AI_MODEL
        reasoning_effort = body.reasoning_effort or DEFAULT_REASONING_EFFORT

        async def event_generator():
            try:
                # 创建AI服务
                ai_service = AIServiceFactory.create_service(ai_platform, body.api_key, ai_model)
                
                # Get cached git data
                git_data = get_cached_git_data(
                    body.platform, body.username, body.repo, body.git_token, body.git_api_url
                )
                default_branch = git_data["default_branch"]
                file_tree = git_data["file_tree"]
                readme = git_data["readme"]
                git_service = git_data["service"]

                # Send initial status
                yield f"data: {json.dumps({'status': 'started', 'message': f'使用 {ai_platform} ({ai_model}) 开始生成流程...'})}\n\n"
                await asyncio.sleep(0.1)

                # Token count check
                combined_content = f"{file_tree}\n{readme}"
                token_count = ai_service.count_tokens(combined_content)
                
                # 获取平台的令牌限制
                max_token_limit = 195000  # 默认最大限制
                
                if ai_platform in AI_TOKEN_LIMITS and ai_model in AI_TOKEN_LIMITS[ai_platform]:
                    max_token_limit = AI_TOKEN_LIMITS[ai_platform][ai_model]

                if 50000 < token_count < max_token_limit and not body.api_key:
                    yield f"data: {json.dumps({'error': f'文件树和README合计超过令牌限制 (50,000)。当前大小: {token_count} 令牌。此仓库太大，无法免费分析，但您可以提供自己的 {ai_platform} API密钥继续。'})}\n\n"
                    return
                elif token_count > max_token_limit:
                    yield f"data: {json.dumps({'error': f'仓库过大 (>{max_token_limit}k 令牌)，无法分析。{ai_platform} {ai_model} 的最大上下文长度为 {max_token_limit} 令牌。当前大小: {token_count} 令牌。'})}\n\n"
                    return

                # Prepare prompts
                first_system_prompt = SYSTEM_FIRST_PROMPT
                third_system_prompt = SYSTEM_THIRD_PROMPT
                if body.instructions:
                    first_system_prompt = (
                        first_system_prompt
                        + "\n"
                        + ADDITIONAL_SYSTEM_INSTRUCTIONS_PROMPT
                    )
                    third_system_prompt = (
                        third_system_prompt
                        + "\n"
                        + ADDITIONAL_SYSTEM_INSTRUCTIONS_PROMPT
                    )

                # Phase 1: Get explanation
                yield f"data: {json.dumps({'status': 'explanation_sent', 'message': f'向 {ai_platform} 发送解释请求...'})}\n\n"
                await asyncio.sleep(0.1)
                yield f"data: {json.dumps({'status': 'explanation', 'message': '分析仓库结构...'})}\n\n"
                explanation = ""
                async for chunk in ai_service.call_api_stream(
                    system_prompt=first_system_prompt,
                    data={
                        "file_tree": file_tree,
                        "readme": readme,
                        "instructions": body.instructions,
                    },
                    api_key=body.api_key,
                    reasoning_effort=reasoning_effort,
                ):
                    explanation += chunk
                    yield f"data: {json.dumps({'status': 'explanation_chunk', 'chunk': chunk})}\n\n"

                if "BAD_INSTRUCTIONS" in explanation:
                    yield f"data: {json.dumps({'error': '提供的指令无效或不明确'})}\n\n"
                    return

                # Phase 2: Get component mapping
                yield f"data: {json.dumps({'status': 'mapping_sent', 'message': f'向 {ai_platform} 发送组件映射请求...'})}\n\n"
                await asyncio.sleep(0.1)
                yield f"data: {json.dumps({'status': 'mapping', 'message': '创建组件映射...'})}\n\n"
                full_second_response = ""
                async for chunk in ai_service.call_api_stream(
                    system_prompt=SYSTEM_SECOND_PROMPT,
                    data={"explanation": explanation, "file_tree": file_tree},
                    api_key=body.api_key,
                    reasoning_effort=reasoning_effort,
                ):
                    full_second_response += chunk
                    yield f"data: {json.dumps({'status': 'mapping_chunk', 'chunk': chunk})}\n\n"

                # Extract component mapping
                start_tag = "<component_mapping>"
                end_tag = "</component_mapping>"
                component_mapping_text = full_second_response[
                    full_second_response.find(start_tag) : full_second_response.find(
                        end_tag
                    )
                ]

                # Phase 3: Generate Mermaid diagram
                yield f"data: {json.dumps({'status': 'diagram_sent', 'message': f'向 {ai_platform} 发送图表生成请求...'})}\n\n"
                await asyncio.sleep(0.1)
                yield f"data: {json.dumps({'status': 'diagram', 'message': '生成图表...'})}\n\n"
                mermaid_code = ""
                async for chunk in ai_service.call_api_stream(
                    system_prompt=third_system_prompt,
                    data={
                        "explanation": explanation,
                        "component_mapping": component_mapping_text,
                        "instructions": body.instructions,
                    },
                    api_key=body.api_key,
                    reasoning_effort=reasoning_effort,
                ):
                    mermaid_code += chunk
                    yield f"data: {json.dumps({'status': 'diagram_chunk', 'chunk': chunk})}\n\n"

                # Process final diagram
                mermaid_code = mermaid_code.replace("```mermaid", "").replace("```", "")
                if "BAD_INSTRUCTIONS" in mermaid_code:
                    yield f"data: {json.dumps({'error': '提供的指令无效或不明确'})}\n\n"
                    return

                processed_diagram = process_click_events(
                    mermaid_code, body.platform, body.username, body.repo, default_branch, git_service
                )

                # Send final result
                yield f"data: {json.dumps({
                    'status': 'complete',
                    'diagram': processed_diagram,
                    'explanation': explanation,
                    'mapping': component_mapping_text,
                    'ai_platform': ai_platform,
                    'ai_model': ai_model
                })}\n\n"

            except Exception as e:
                yield f"data: {json.dumps({'error': str(e)})}\n\n"

        return StreamingResponse(
            event_generator(),
            media_type="text/event-stream",
            headers={
                "X-Accel-Buffering": "no",  # Hint to Nginx
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
            },
        )
    except Exception as e:
        return {"error": str(e)}


@router.get("/ai-platforms")
async def get_ai_platforms(request: Request):
    """
    获取所有可用的AI平台信息
    
    Returns:
        Dict[str, Any]: 包含可用平台、模型和推理努力程度选项的信息
    """
    try:
        # 获取可用平台信息
        available_platforms = AIServiceFactory.get_available_platforms()
        
        # 获取推理努力程度选项
        reasoning_effort_options = AIServiceFactory.get_reasoning_effort_options()
        
        # 获取默认配置
        default_config = {
            "default_platform": DEFAULT_AI_PLATFORM,
            "default_model": DEFAULT_AI_MODEL,
            "default_reasoning_effort": DEFAULT_REASONING_EFFORT
        }
        
        # 构建响应
        response = {
            "platforms": available_platforms,
            "reasoning_effort_options": reasoning_effort_options,
            "default_config": default_config
        }
        
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
