"use client";

import * as React from "react";
import { Check, ChevronsUpDown } from "lucide-react";
import { cn } from "~/lib/utils";
import {
  Command,
  CommandEmpty,
  CommandGroup,
  CommandInput,
  CommandItem,
} from "~/components/ui/command";
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "~/components/ui/popover";
import { Button } from "~/components/ui/button";

export type GitPlatform = {
  id: string;
  name: string;
  color: string;
  urlPattern: string;
};

const gitPlatforms: GitPlatform[] = [
  {
    id: "github",
    name: "GitHub",
    color: "text-black",
    urlPattern: "https://github.com/username/repo",
  },
  {
    id: "gitlab",
    name: "GitLab",
    color: "text-orange-600",
    urlPattern: "https://gitlab.com/username/repo",
  },
  {
    id: "gitea",
    name: "Gitea",
    color: "text-green-600",
    urlPattern: "https://gitea.com/username/repo",
  },
];

interface PlatformSelectorProps {
  value: string;
  onValueChange: (value: string) => void;
  onUrlPatternChange: (pattern: string) => void;
  className?: string;
}

export function PlatformSelector({
  value,
  onValueChange,
  onUrlPatternChange,
  className,
}: PlatformSelectorProps) {
  const [open, setOpen] = React.useState(false);
  
  // 获取当前选择的平台信息
  const selectedPlatform = gitPlatforms.find(platform => platform.id === value) ?? gitPlatforms[0];

  // 当选择改变时，更新URL模式
  const handleSelectionChange = (platformId: string) => {
    onValueChange(platformId);
    const platform = gitPlatforms.find(p => p.id === platformId);
    if (platform) {
      onUrlPatternChange(platform.urlPattern);
    }
    setOpen(false);
  };

  return (
    <Popover open={open} onOpenChange={setOpen}>
      <PopoverTrigger asChild>
        <Button
          variant="outline"
          role="combobox"
          aria-expanded={open}
          className={cn(
            "flex w-full justify-between border-[3px] border-black shadow-[4px_4px_0_0_#000000]",
            className
          )}
        >
          <span className={selectedPlatform?.color}>
            {selectedPlatform?.name}
          </span>
          <ChevronsUpDown className="ml-2 h-4 w-4 shrink-0 opacity-50" />
        </Button>
      </PopoverTrigger>
      <PopoverContent className="w-full p-0">
        <Command>
          <CommandInput placeholder="Search platform..." />
          <CommandEmpty>Platform not found</CommandEmpty>
          <CommandGroup>
            {gitPlatforms.map((platform) => (
              <CommandItem
                key={platform.id}
                value={platform.id}
                onSelect={() => handleSelectionChange(platform.id)}
              >
                <Check
                  className={cn(
                    "mr-2 h-4 w-4",
                    value === platform.id ? "opacity-100" : "opacity-0"
                  )}
                />
                <span className={platform.color}>{platform.name}</span>
              </CommandItem>
            ))}
          </CommandGroup>
        </Command>
      </PopoverContent>
    </Popover>
  );
} 