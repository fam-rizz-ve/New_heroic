import { useBackendHealth } from "@/hooks/useBackendHealth";

function LoadingSpinner() {
  return (
    <div className="flex items-center gap-3">
      <div className="h-4 w-4 animate-spin rounded-full border-2 border-blue-500 border-t-transparent" />
      <span className="text-sm text-gray-400">Connecting to backend...</span>
    </div>
  );
}

function ErrorState({ message, onRetry }: { message: string; onRetry: () => void }) {
  return (
    <div className="rounded-lg border border-red-800/40 bg-red-950/30 p-4">
      <div className="flex items-start gap-3">
        <span className="mt-0.5 text-lg text-red-400">⚠</span>
        <div className="flex-1">
          <p className="text-sm font-medium text-red-300">Backend Unreachable</p>
          <p className="mt-1 text-xs text-red-400/80">{message}</p>
          <button
            onClick={onRetry}
            className="mt-2 rounded bg-red-800/40 px-3 py-1 text-xs font-medium text-red-200 transition-colors hover:bg-red-700/50"
          >
            Retry Connection
          </button>
        </div>
      </div>
    </div>
  );
}

function ConnectedState({
  appName,
  version,
}: {
  appName: string;
  version: string;
}) {
  return (
    <div className="rounded-lg border border-green-800/40 bg-green-950/30 p-4">
      <div className="flex items-center gap-3">
        <span className="flex h-3 w-3">
          <span className="absolute inline-flex h-3 w-3 animate-ping rounded-full bg-green-400 opacity-75" />
          <span className="relative inline-flex h-3 w-3 rounded-full bg-green-500" />
        </span>
        <div>
          <p className="text-sm font-medium text-green-300">{appName}</p>
          <p className="text-xs text-green-400/70">v{version} — IPC connected</p>
        </div>
      </div>
    </div>
  );
}

export function BackendStatus() {
  const { status, health, error, retry } = useBackendHealth();

  return (
    <div className="fixed bottom-4 right-4 min-w-[260px]">
      {status === "connecting" && <LoadingSpinner />}
      {status === "error" && error && (
        <ErrorState message={error} onRetry={retry} />
      )}
      {status === "connected" && health && (
        <ConnectedState appName={health.app_name} version={health.version} />
      )}
    </div>
  );
}
