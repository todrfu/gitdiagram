"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import { FaGithub } from "react-icons/fa";
import { getStarCount } from "~/app/_actions/github";
import { PrivateReposDialog } from "./private-repos-dialog";
import { ApiKeyDialog } from "./api-key-dialog";

export function Header() {
  const [isPrivateReposDialogOpen, setIsPrivateReposDialogOpen] =
    useState(false);
  const [isApiKeyDialogOpen, setIsApiKeyDialogOpen] = useState(false);
  const [starCount, setStarCount] = useState<number | null>(null);

  useEffect(() => {
    void getStarCount().then(setStarCount);
  }, []);

  const formatStarCount = (count: number | null) => {
    if (!count) return "10.0k";
    if (count >= 1000) {
      return `${(count / 1000).toFixed(1)}k`;
    }
    return count.toString();
  };

  const handlePrivateReposSubmit = (token: string, platform: string) => {
    // 根据平台类型存储对应的令牌
    if (platform === "github") {
      localStorage.setItem("github_pat", token);
    } else if (platform === "gitlab") {
      localStorage.setItem("gitlab_token", token);
    } else if (platform === "gitea") {
      localStorage.setItem("gitea_token", token);
    }
    setIsPrivateReposDialogOpen(false);
  };

  const handleApiKeySubmit = (apiKey: string, platform: string) => {
    // 根据平台存储API密钥
    const keyMap: Record<string, string> = {
      openai: "openai_key",
      anthropic: "anthropic_key",
      deepseek: "deepseek_key"
    };
    
    const keyName = keyMap[platform];
    if (keyName) {
      localStorage.setItem(keyName, apiKey);
    }
    
    setIsApiKeyDialogOpen(false);
  };

  return (
    <header className="border-b-[3px] border-black">
      <div className="mx-auto flex h-16 max-w-4xl items-center justify-between px-4 sm:px-8">
        <Link href="/" className="flex items-center">
          <span className="text-lg font-semibold sm:text-xl">
            <span className="text-black transition-colors duration-200 hover:text-gray-600">
              Git
            </span>
            <span className="text-purple-600 transition-colors duration-200 hover:text-purple-500">
              Diagram
            </span>
          </span>
        </Link>
        <nav className="flex items-center gap-3 sm:gap-6">
          <span
            onClick={() => setIsApiKeyDialogOpen(true)}
            className="cursor-pointer text-sm font-medium text-black transition-transform hover:translate-y-[-2px] hover:text-purple-600"
          >
            <span className="flex items-center sm:hidden">
              <span>API Key</span>
            </span>
            <span className="hidden items-center gap-1 sm:flex">
              <span>API Key</span>
            </span>
          </span>
          <span
            onClick={() => setIsPrivateReposDialogOpen(true)}
            className="cursor-pointer text-sm font-medium text-black transition-transform hover:translate-y-[-2px] hover:text-purple-600"
          >
            <span className="sm:hidden">Private Repos</span>
            <span className="hidden sm:inline">Private Repos</span>
          </span>
          <Link
            href="https://github.com/ahmedkhaleel2004/gitdiagram"
            className="flex items-center gap-1 text-sm font-medium text-black transition-transform hover:translate-y-[-2px] hover:text-purple-600 sm:gap-2"
          >
            <FaGithub className="h-5 w-5" />
            <span className="hidden sm:inline">GitHub</span>
          </Link>
          <span className="flex items-center gap-1 text-sm font-medium text-black">
            <span className="text-amber-400">★</span>
            {formatStarCount(starCount)}
          </span>
        </nav>

        <PrivateReposDialog
          isOpen={isPrivateReposDialogOpen}
          onClose={() => setIsPrivateReposDialogOpen(false)}
          onSubmit={handlePrivateReposSubmit}
        />
        <ApiKeyDialog
          isOpen={isApiKeyDialogOpen}
          onClose={() => setIsApiKeyDialogOpen(false)}
          onSubmit={handleApiKeySubmit}
        />
      </div>
    </header>
  );
}
