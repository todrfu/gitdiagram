"use client";

import { Dialog, DialogContent, DialogHeader, DialogTitle } from "./ui/dialog";
import { Input } from "./ui/input";
import { Button } from "./ui/button";
import { useState, useEffect } from "react";
import Link from "next/link";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "./ui/tabs";

interface PrivateReposDialogProps {
  isOpen: boolean;
  onClose: () => void;
  onSubmit: (token: string, platform: string) => void;
}

// Git平台配置
const GIT_PLATFORMS = [
  {
    id: "github",
    name: "GitHub",
    keyName: "github_pat",
    keyPrefix: "ghp_",
    placeholder: "ghp_...",
    minLength: 4,
    docUrl: "https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/managing-your-personal-access-tokens",
    description: "To enable private repositories, you'll need to provide a GitHub Personal Access Token with repo scope. The token will be stored locally in your browser."
  },
  {
    id: "gitlab",
    name: "GitLab",
    keyName: "gitlab_token",
    keyPrefix: "glpat-",
    placeholder: "glpat-...",
    minLength: 6,
    docUrl: "https://docs.gitlab.com/ee/user/profile/personal_access_tokens.html",
    description: "To access private repositories, you'll need to provide a GitLab Personal Access Token. The token will be stored locally in your browser."
  },
  {
    id: "gitea",
    name: "Gitea",
    keyName: "gitea_token",
    keyPrefix: "",
    placeholder: "Gitea token...",
    minLength: 5,
    docUrl: "https://docs.gitea.io/en-us/api-usage/#generating-and-listing-api-tokens",
    description: "To access private repositories, you'll need to provide a Gitea Access Token. The token will be stored locally in your browser."
  }
];

// 创建初始令牌状态
const createInitialTokensState = (): Record<string, string> => {
  return GIT_PLATFORMS.reduce((acc, platform) => {
    acc[platform.id] = "";
    return acc;
  }, {} as Record<string, string>);
};

export function PrivateReposDialog({
  isOpen,
  onClose,
  onSubmit,
}: PrivateReposDialogProps) {
  const [currentPlatform, setCurrentPlatform] = useState<string>("github");
  const [tokens, setTokens] = useState<Record<string, string>>(createInitialTokensState);

  // 对话框打开时加载所有平台的令牌
  useEffect(() => {
    if (isOpen) {
      const savedTokens = createInitialTokensState();
      
      GIT_PLATFORMS.forEach(platform => {
        const storedToken = localStorage.getItem(platform.keyName);
        if (storedToken) {
          savedTokens[platform.id] = storedToken;
        }
      });
      
      setTokens(savedTokens);
    }
  }, [isOpen]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const currentToken = tokens[currentPlatform] ?? "";
    onSubmit(currentToken, currentPlatform);
  };

  const handleClear = () => {
    const platform = GIT_PLATFORMS.find(p => p.id === currentPlatform);
    if (platform) {
      localStorage.removeItem(platform.keyName);
      setTokens(prevTokens => ({
        ...prevTokens,
        [currentPlatform]: ""
      }));
    }
  };

  const handleTokenChange = (value: string) => {
    setTokens(prevTokens => ({
      ...prevTokens,
      [currentPlatform]: value
    }));
  };

  const isTokenValid = (platformId: string, token: string): boolean => {
    const platform = GIT_PLATFORMS.find(p => p.id === platformId);
    if (!platform) return false;
    
    if (platform.keyPrefix && token) {
      return token.startsWith(platform.keyPrefix);
    } else {
      return token.length >= (platform.minLength || 1);
    }
  };

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="border-[3px] border-black bg-purple-200 p-6 shadow-[8px_8px_0_0_#000000] sm:max-w-md">
        <DialogHeader>
          <DialogTitle className="text-xl font-bold text-black">
            Private Repository Access
          </DialogTitle>
        </DialogHeader>
        <Tabs
          defaultValue="github"
          value={currentPlatform}
          onValueChange={setCurrentPlatform}
          className="w-full"
        >
          <TabsList className="grid w-full grid-cols-3">
            {GIT_PLATFORMS.map(platform => (
              <TabsTrigger key={platform.id} value={platform.id}>
                {platform.name}
              </TabsTrigger>
            ))}
          </TabsList>

          {GIT_PLATFORMS.map(platform => (
            <TabsContent key={platform.id} value={platform.id}>
              <form onSubmit={handleSubmit} className="space-y-4">
                <div className="text-sm">
                  {platform.description} Find out how{" "}
                  <Link
                    href={platform.docUrl}
                    className="text-purple-600 transition-colors duration-200 hover:text-purple-500"
                  >
                    here
                  </Link>
                  .
                </div>
                <Input
                  type="password"
                  placeholder={platform.placeholder}
                  value={tokens[platform.id] ?? ""}
                  onChange={(e) => handleTokenChange(e.target.value)}
                  className="flex-1 rounded-md border-[3px] border-black px-3 py-2 text-base font-bold shadow-[4px_4px_0_0_#000000] placeholder:text-base placeholder:font-normal placeholder:text-gray-700"
                  required
                />
                <div className="flex items-center justify-between">
                  <button
                    type="button"
                    onClick={handleClear}
                    className="text-sm text-purple-600 hover:text-purple-500"
                  >
                    Clear
                  </button>
                  <div className="flex gap-3">
                    <Button
                      type="button"
                      onClick={onClose}
                      className="border-[3px] border-black bg-gray-200 px-4 py-2 text-black shadow-[4px_4px_0_0_#000000] transition-transform hover:-translate-x-0.5 hover:-translate-y-0.5 hover:bg-gray-300"
                    >
                      Cancel
                    </Button>
                    <Button
                      type="submit"
                      disabled={!isTokenValid(platform.id, tokens[platform.id] ?? "")}
                      className="border-[3px] border-black bg-purple-400 px-4 py-2 text-black shadow-[4px_4px_0_0_#000000] transition-transform hover:-translate-x-0.5 hover:-translate-y-0.5 hover:bg-purple-300 disabled:opacity-50"
                    >
                      Save Token
                    </Button>
                  </div>
                </div>
              </form>
            </TabsContent>
          ))}
        </Tabs>

        <details className="group mt-4 text-sm [&>summary:focus-visible]:outline-none">
          <summary className="cursor-pointer font-medium text-purple-700 hover:text-purple-600">
            Data storage disclaimer
          </summary>
          <div className="animate-accordion-down mt-2 space-y-2 overflow-hidden pl-2">
            <p>
              Take note that the diagram data will be stored in my database
              (not that I would use it for anything anyways). You can also
              self-host this app by following the instructions in the{" "}
              <Link
                href="https://github.com/ahmedkhaleel2004/gitdiagram"
                className="text-purple-600 transition-colors duration-200 hover:text-purple-500"
              >
                README
              </Link>
              .
            </p>
          </div>
        </details>
      </DialogContent>
    </Dialog>
  );
}
