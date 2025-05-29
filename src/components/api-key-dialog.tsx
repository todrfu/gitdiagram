"use client";

import { Dialog, DialogContent, DialogHeader, DialogTitle } from "./ui/dialog";
import { Input } from "./ui/input";
import { Button } from "./ui/button";
import { useState, useEffect } from "react";
import Link from "next/link";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "./ui/tabs";

interface ApiKeyDialogProps {
  isOpen: boolean;
  onClose: () => void;
  onSubmit: (apiKey: string, platform: string) => void;
}

// AI平台配置
const AI_PLATFORMS = [
  {
    id: "openai",
    name: "OpenAI",
    keyPrefix: "sk-",
    keyName: "openai_key",
    placeholder: "sk-...",
    docUrl: "https://platform.openai.com/api-keys",
    description: "OpenAI API key for accessing models like GPT-4o mini."
  },
  {
    id: "anthropic",
    name: "Claude",
    keyPrefix: "sk-ant-",
    keyName: "anthropic_key",
    placeholder: "sk-ant-...",
    docUrl: "https://console.anthropic.com/settings/keys",
    description: "Anthropic API key for accessing Claude models."
  },
  {
    id: "deepseek",
    name: "DeepSeek",
    keyPrefix: "sk-",
    keyName: "deepseek_key",
    placeholder: "sk-...",
    docUrl: "https://platform.deepseek.com/",
    description: "DeepSeek API key for accessing DeepSeek models."
  }
];

// 使用所有平台ID创建初始键状态
const createInitialKeysState = (): Record<string, string> => {
  return AI_PLATFORMS.reduce((acc, platform) => {
    acc[platform.id] = "";
    return acc;
  }, {} as Record<string, string>);
};

export function ApiKeyDialog({ isOpen, onClose, onSubmit }: ApiKeyDialogProps) {
  const [currentPlatform, setCurrentPlatform] = useState<string>("openai");
  const [apiKeys, setApiKeys] = useState<Record<string, string>>(createInitialKeysState);

  // 对话框上的加载存储的钥匙打开
  useEffect(() => {
    if (isOpen) {
      const keys = createInitialKeysState();
      
      AI_PLATFORMS.forEach(platform => {
        const storedKey = localStorage.getItem(platform.keyName);
        if (storedKey) {
          keys[platform.id] = storedKey;
        }
      });
      
      setApiKeys(keys);
    }
  }, [isOpen]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const currentKey = apiKeys[currentPlatform] ?? "";
    onSubmit(currentKey, currentPlatform);
  };

  const handleClear = () => {
    const platform = AI_PLATFORMS.find(p => p.id === currentPlatform);
    if (platform) {
      localStorage.removeItem(platform.keyName);
      setApiKeys(prevKeys => ({
        ...prevKeys,
        [currentPlatform]: ""
      }));
    }
  };

  const handleKeyChange = (value: string) => {
    setApiKeys(prevKeys => ({
      ...prevKeys,
      [currentPlatform]: value
    }));
  };

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="border-[3px] border-black bg-purple-200 p-6 shadow-[8px_8px_0_0_#000000] sm:max-w-md">
        <DialogHeader>
          <DialogTitle className="text-xl font-bold text-black">
            AI Service API Keys
          </DialogTitle>
        </DialogHeader>
        
        <Tabs
          defaultValue="openai"
          value={currentPlatform}
          onValueChange={setCurrentPlatform}
          className="w-full"
        >
          <TabsList className="grid w-full grid-cols-3">
            {AI_PLATFORMS.map(platform => (
              <TabsTrigger key={platform.id} value={platform.id}>
                {platform.name}
              </TabsTrigger>
            ))}
          </TabsList>

          {AI_PLATFORMS.map(platform => (
            <TabsContent key={platform.id} value={platform.id}>
              <form onSubmit={handleSubmit} className="space-y-4">
                <div className="text-sm">
                  GitDiagram offers infinite free diagram generations! You can also
                  provide a {platform.name} API key to generate diagrams at your own cost.
                  The key will be stored locally in your browser.
                  <br />
                  <br />
                  <span className="font-medium">Get your {platform.name} API key </span>
                  <Link
                    href={platform.docUrl}
                    className="font-medium text-purple-600 transition-colors duration-200 hover:text-purple-500"
                  >
                    here
                  </Link>
                  .
                </div>
                <Input
                  type="password"
                  placeholder={platform.placeholder}
                  value={apiKeys[platform.id] ?? ""}
                  onChange={(e) => handleKeyChange(e.target.value)}
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
                      disabled={!(apiKeys[platform.id] ?? "").startsWith(platform.keyPrefix)}
                      className="border-[3px] border-black bg-purple-400 px-4 py-2 text-black shadow-[4px_4px_0_0_#000000] transition-transform hover:-translate-x-0.5 hover:-translate-y-0.5 hover:bg-purple-300 disabled:opacity-50"
                    >
                      Save Key
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
              Your API keys will be stored locally in your browser and used
              only for generating diagrams. You can also self-host this app by
              following the instructions in the{" "}
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
