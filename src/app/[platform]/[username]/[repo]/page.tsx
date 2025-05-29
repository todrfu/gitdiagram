"use client";

import { useParams } from "next/navigation";
import MainCard from "~/components/main-card";
import Loading from "~/components/loading";
import MermaidChart from "~/components/mermaid-diagram";
import { useDiagram } from "~/hooks/useDiagram";
import { ApiKeyDialog } from "~/components/api-key-dialog";
import { ApiKeyButton } from "~/components/api-key-button";
import { useState } from "react";
import { useStarReminder } from "~/hooks/useStarReminder";

export default function Repo() {
  const [zoomingEnabled, setZoomingEnabled] = useState(false);
  const params = useParams<{ platform: string; username: string; repo: string }>();

  // 使用URL参数获取平台、用户名和仓库名
  const platform = params.platform.toLowerCase();
  const username = params.username.toLowerCase();
  const repo = params.repo.toLowerCase();

  // Use the star reminder hook
  useStarReminder();

  const {
    diagram,
    error,
    loading,
    lastGenerated,
    cost,
    showApiKeyDialog,
    handleModify,
    handleRegenerate,
    handleCopy,
    handleApiKeySubmit,
    handleCloseApiKeyDialog,
    handleOpenApiKeyDialog,
    handleExportImage,
    state,
  } = useDiagram(username, repo, platform);

  return (
    <div className="flex flex-col items-center p-4">
      <div className="flex w-full justify-center pt-8">
        <MainCard
          isHome={false}
          platform={platform}
          username={username}
          repo={repo}
          showCustomization={!loading && !error}
          onModify={handleModify}
          onRegenerate={handleRegenerate}
          onCopy={handleCopy}
          lastGenerated={lastGenerated}
          onExportImage={handleExportImage}
          zoomingEnabled={zoomingEnabled}
          onZoomToggle={() => setZoomingEnabled(!zoomingEnabled)}
          loading={loading}
        />
      </div>
      <div className="mt-8 flex w-full flex-col items-center gap-8">
        {loading ? (
          <Loading
            cost={cost}
            status={state.status}
            explanation={state.explanation}
            mapping={state.mapping}
            diagram={state.diagram}
          />
        ) : error || state.error ? (
          <div className="mt-12 text-center">
            <p className="max-w-4xl text-lg font-medium text-purple-600">
              {error || state.error}
            </p>
            {(error?.includes("API key") ||
              state.error?.includes("API key")) && (
              <div className="mt-8 flex flex-col items-center gap-2">
                <ApiKeyButton onClick={handleOpenApiKeyDialog} />
              </div>
            )}
          </div>
        ) : (
          <div className="flex w-full justify-center px-4">
            <MermaidChart chart={diagram} zoomingEnabled={zoomingEnabled} />
          </div>
        )}
      </div>

      <ApiKeyDialog
        isOpen={showApiKeyDialog}
        onClose={handleCloseApiKeyDialog}
        onSubmit={handleApiKeySubmit}
      />
    </div>
  );
} 