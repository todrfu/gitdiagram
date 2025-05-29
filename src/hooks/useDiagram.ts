import { useState, useEffect, useCallback } from "react";
import {
  cacheDiagramAndExplanation,
  getCachedDiagram,
} from "~/app/_actions/cache";
import { getLastGeneratedDate } from "~/app/_actions/repo";
import { getCostOfGeneration } from "~/lib/fetch-backend";
import { exampleRepos } from "~/lib/exampleRepos";

interface StreamState {
  status:
    | "idle"
    | "started"
    | "explanation_sent"
    | "explanation"
    | "explanation_chunk"
    | "mapping_sent"
    | "mapping"
    | "mapping_chunk"
    | "diagram_sent"
    | "diagram"
    | "diagram_chunk"
    | "complete"
    | "error";
  message?: string;
  explanation?: string;
  mapping?: string;
  diagram?: string;
  error?: string;
}

interface StreamResponse {
  status: StreamState["status"];
  message?: string;
  chunk?: string;
  explanation?: string;
  mapping?: string;
  diagram?: string;
  error?: string;
}

// AI平台到localStorage键名的映射
const AI_PLATFORM_KEYS = {
  openai: "openai_key",
  anthropic: "anthropic_key",
  deepseek: "deepseek_key"
};

// 默认AI平台
const DEFAULT_AI_PLATFORM = "openai";

export function useDiagram(username: string, repo: string, platform = "github") {
  const [diagram, setDiagram] = useState<string>("");
  const [error, setError] = useState<string>("");
  const [loading, setLoading] = useState<boolean>(true);
  const [lastGenerated, setLastGenerated] = useState<Date | undefined>();
  const [cost, setCost] = useState<string>("");
  const [showApiKeyDialog, setShowApiKeyDialog] = useState(false);
  // const [tokenCount, setTokenCount] = useState<number>(0);
  const [state, setState] = useState<StreamState>({ status: "idle" });
  const [aiPlatform, setAiPlatform] = useState<string>(DEFAULT_AI_PLATFORM);
  const [hasUsedFreeGeneration, setHasUsedFreeGeneration] = useState<boolean>(
    () => {
      if (typeof window === "undefined") return false;
      return localStorage.getItem("has_used_free_generation") === "true";
    },
  );

  // 获取当前AI平台的API密钥
  const getCurrentAiPlatformKey = useCallback(() => {
    const keyName = AI_PLATFORM_KEYS[aiPlatform as keyof typeof AI_PLATFORM_KEYS] || AI_PLATFORM_KEYS.openai;
    return localStorage.getItem(keyName) ?? undefined;
  }, [aiPlatform]);

  const generateDiagram = useCallback(
    async (instructions = "", gitToken?: string) => {
      setState({
        status: "started",
        message: "Starting generation process...",
      });

      try {
        const baseUrl =
          process.env.NEXT_PUBLIC_API_DEV_URL ?? "https://api.gitdiagram.com";
          
        // 获取存储的Git平台配置（私有仓库）
        let token = gitToken;
        
        if (platform === "gitlab") {
          const storedToken = localStorage.getItem("gitlab_token");
          
          if (!token && storedToken) {
            token = storedToken;
          }
        } else if (platform === "gitea") {
          const storedToken = localStorage.getItem("gitea_token");
          
          if (!token && storedToken) {
            token = storedToken;
          }
        }
        
        const response = await fetch(`${baseUrl}/generate/stream`, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            platform,
            username,
            repo,
            instructions,
            api_key: getCurrentAiPlatformKey(),
            git_token: token,
            ai_platform: aiPlatform
          }),
        });
        if (!response.ok) {
          throw new Error("Failed to start streaming");
        }
        const reader = response.body?.getReader();
        if (!reader) {
          throw new Error("No reader available");
        }

        let explanation = "";
        let mapping = "";
        let diagram = "";

        // Process the stream
        const processStream = async () => {
          try {
            while (true) {
              const { done, value } = await reader.read();
              if (done) break;

              // Convert the chunk to text
              const chunk = new TextDecoder().decode(value);
              const lines = chunk.split("\n");

              // Process each SSE message
              for (const line of lines) {
                if (line.startsWith("data: ")) {
                  try {
                    const data = JSON.parse(line.slice(6)) as StreamResponse;

                    // If we receive an error, set loading to false immediately
                    if (data.error) {
                      setState({ status: "error", error: data.error });
                      setLoading(false);
                      return; // Add this to stop processing
                    }

                    // Update state based on the message type
                    switch (data.status) {
                      case "started":
                        setState((prev) => ({
                          ...prev,
                          status: "started",
                          message: data.message,
                        }));
                        break;
                      case "explanation_sent":
                        setState((prev) => ({
                          ...prev,
                          status: "explanation_sent",
                          message: data.message,
                        }));
                        break;
                      case "explanation":
                        setState((prev) => ({
                          ...prev,
                          status: "explanation",
                          message: data.message,
                        }));
                        break;
                      case "explanation_chunk":
                        if (data.chunk) {
                          explanation += data.chunk;
                          setState((prev) => ({ ...prev, explanation }));
                        }
                        break;
                      case "mapping_sent":
                        setState((prev) => ({
                          ...prev,
                          status: "mapping_sent",
                          message: data.message,
                        }));
                        break;
                      case "mapping":
                        setState((prev) => ({
                          ...prev,
                          status: "mapping",
                          message: data.message,
                        }));
                        break;
                      case "mapping_chunk":
                        if (data.chunk) {
                          mapping += data.chunk;
                          setState((prev) => ({ ...prev, mapping }));
                        }
                        break;
                      case "diagram_sent":
                        setState((prev) => ({
                          ...prev,
                          status: "diagram_sent",
                          message: data.message,
                        }));
                        break;
                      case "diagram":
                        setState((prev) => ({
                          ...prev,
                          status: "diagram",
                          message: data.message,
                        }));
                        break;
                      case "diagram_chunk":
                        if (data.chunk) {
                          diagram += data.chunk;
                          setState((prev) => ({ ...prev, diagram }));
                        }
                        break;
                      case "complete":
                        setState({
                          status: "complete",
                          explanation: data.explanation,
                          diagram: data.diagram,
                        });
                        const date = await getLastGeneratedDate(username, repo);
                        setLastGenerated(date ?? undefined);
                        if (!hasUsedFreeGeneration) {
                          localStorage.setItem(
                            "has_used_free_generation",
                            "true",
                          );
                          setHasUsedFreeGeneration(true);
                        }
                        break;
                      case "error":
                        setState({ status: "error", error: data.error });
                        break;
                    }
                  } catch (e) {
                    console.error("Error parsing SSE message:", e);
                  }
                }
              }
            }
          } finally {
            reader.releaseLock();
          }
        };

        await processStream();
      } catch (error) {
        setState({
          status: "error",
          error:
            error instanceof Error
              ? error.message
              : "An unknown error occurred",
        });
        setLoading(false);
      }
    },
    [username, repo, platform, hasUsedFreeGeneration, aiPlatform, getCurrentAiPlatformKey],
  );

  useEffect(() => {
    if (state.status === "complete" && state.diagram) {
      // Cache the completed diagram with the usedOwnKey flag
      const hasApiKey = !!getCurrentAiPlatformKey();
      void cacheDiagramAndExplanation(
        username,
        repo,
        state.diagram,
        state.explanation ?? "No explanation provided",
        hasApiKey,
      );
      setDiagram(state.diagram);
      void getLastGeneratedDate(username, repo).then((date) =>
        setLastGenerated(date ?? undefined),
      );
    } else if (state.status === "error") {
      setLoading(false);
    }
  }, [state.status, state.diagram, username, repo, state.explanation, getCurrentAiPlatformKey]);

  const getDiagram = useCallback(async () => {
    setLoading(true);
    setError("");
    setCost("");

    try {
      // Check cache first - always allow access to cached diagrams
      const cached = await getCachedDiagram(username, repo);
      
      // 获取存储的Git平台配置
      let gitToken = null;
      
      if (platform === "gitlab") {
        gitToken = localStorage.getItem("gitlab_token");
      } else if (platform === "gitea") {
        gitToken = localStorage.getItem("gitea_token");
      }

      if (cached) {
        setDiagram(cached);
        const date = await getLastGeneratedDate(username, repo);
        setLastGenerated(date ?? undefined);
        return;
      }

      // Get cost estimate
      const costEstimate = await getCostOfGeneration(
        username,
        repo,
        "",
        gitToken ?? undefined,
        platform
      );

      if (costEstimate.error) {
        console.error("Cost estimation failed:", costEstimate.error);
        setError(costEstimate.error);
        return;
      }

      setCost(costEstimate.cost ?? "");

      // Start streaming generation
      await generateDiagram("", gitToken ?? undefined);

    } catch (error) {
      console.error("Error in getDiagram:", error);
      setError("Something went wrong. Please try again later.");
    } finally {
      setLoading(false);
    }
  }, [username, repo, platform, generateDiagram]);

  useEffect(() => {
    void getDiagram();
  }, [getDiagram]);

  const isExampleRepo = (repoName: string): boolean => {
    return Object.values(exampleRepos).some((value) =>
      value.includes(repoName),
    );
  };

  const handleModify = async (instructions: string) => {
    if (isExampleRepo(repo)) {
      setError("Example repositories cannot be modified.");
      return;
    }

    setLoading(true);
    setError("");
    setCost("");
    try {
      // Start streaming generation with instructions
      await generateDiagram(instructions);
    } catch (error) {
      console.error("Error modifying diagram:", error);
      setError("Failed to modify diagram. Please try again later.");
    } finally {
      setLoading(false);
    }
  };

  const handleRegenerate = async (instructions: string) => {
    if (isExampleRepo(repo)) {
      setError("Example repositories cannot be regenerated.");
      return;
    }

    setLoading(true);
    setError("");
    setCost("");
    try {
      // 获取存储的Git平台配置
      let gitToken = null;
      
      if (platform === "gitlab") {
        gitToken = localStorage.getItem("gitlab_token");
      } else if (platform === "gitea") {
        gitToken = localStorage.getItem("gitea_token");
      }

      const costEstimate = await getCostOfGeneration(
        username, 
        repo, 
        "",
        gitToken ?? undefined,
        platform
      );

      if (costEstimate.error) {
        console.error("Cost estimation failed:", costEstimate.error);
        setError(costEstimate.error);
        return;
      }

      setCost(costEstimate.cost ?? "");

      // Start streaming generation with instructions
      await generateDiagram(instructions, gitToken ?? undefined);
    } catch (error) {
      console.error("Error regenerating diagram:", error);
      setError("Failed to regenerate diagram. Please try again later.");
    } finally {
      setLoading(false);
    }
  };

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(diagram);
    } catch (error) {
      console.error("Error copying to clipboard:", error);
    }
  };

  const handleExportImage = () => {
    const svgElement = document.querySelector(".mermaid svg");
    if (!(svgElement instanceof SVGSVGElement)) return;

    try {
      const canvas = document.createElement("canvas");
      const scale = 4;

      const bbox = svgElement.getBBox();
      const transform = svgElement.getScreenCTM();
      if (!transform) return;

      const width = Math.ceil(bbox.width * transform.a);
      const height = Math.ceil(bbox.height * transform.d);
      canvas.width = width * scale;
      canvas.height = height * scale;

      const ctx = canvas.getContext("2d");
      if (!ctx) return;

      const svgData = new XMLSerializer().serializeToString(svgElement);
      const img = new Image();

      img.onload = () => {
        ctx.fillStyle = "white";
        ctx.fillRect(0, 0, canvas.width, canvas.height);

        ctx.scale(scale, scale);
        ctx.drawImage(img, 0, 0, width, height);

        const a = document.createElement("a");
        a.download = "diagram.png";
        a.href = canvas.toDataURL("image/png", 1.0);
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
      };

      img.src =
        "data:image/svg+xml;base64," +
        btoa(unescape(encodeURIComponent(svgData)));
    } catch (error) {
      console.error("Error generating PNG:", error);
    }
  };

  const handleApiKeySubmit = async (apiKey: string, platform: string) => {
    setShowApiKeyDialog(false);
    setLoading(true);
    setError("");

    // 更新当前AI平台
    setAiPlatform(platform);

    // Then generate diagram using stored key
    const github_pat = localStorage.getItem("github_pat");
    try {
      await generateDiagram("", github_pat ?? undefined);
    } catch (error) {
      console.error("Error generating with API key:", error);
      setError(`Failed to generate diagram with provided ${platform} API key.`);
    } finally {
      setLoading(false);
    }
  };

  const handleCloseApiKeyDialog = () => {
    setShowApiKeyDialog(false);
  };

  const handleOpenApiKeyDialog = () => {
    setShowApiKeyDialog(true);
  };

  return {
    diagram,
    error,
    loading,
    lastGenerated,
    cost,
    handleModify,
    handleRegenerate,
    handleCopy,
    showApiKeyDialog,
    // tokenCount,
    handleApiKeySubmit,
    handleCloseApiKeyDialog,
    handleOpenApiKeyDialog,
    handleExportImage,
    state,
    aiPlatform,
    setAiPlatform,
  };
}
