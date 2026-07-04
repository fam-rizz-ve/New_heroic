import { useState, useEffect, useRef, useCallback } from "react";
import { api, type RunnerInfo, type WineVersionResponse, type WineProgressResponse } from "@/lib/api";

// ─── Auth instructions for stores (fallback if backend doesn't provide) ───
const STORE_AUTH_INSTRUCTIONS: Record<string, string> = {
  epic:
    "1. Click 'Login in Browser' to open the Epic Games login page. " +
    "2. Log in with your Epic account. " +
    "3. After logging in, you'll be redirected. Copy the authorization code from the URL. " +
    "4. Paste the code below and click Connect.",
  gog:
    "1. Click 'Login in Browser' to open the GOG login page. " +
    "2. Log in with your GOG account. " +
    "3. After logging in, copy the 'code' parameter from the browser URL. " +
    "4. Paste the code below and click Connect.",
};

const STORE_NAMES = ["epic", "gog"] as const;

const STORE_DISPLAY: Record<string, { label: string; icon: string; desc: string }> = {
  epic: { label: "Epic Games", icon: "🎮", desc: "Connect your Epic Games account" },
  gog: { label: "GOG", icon: "📚", desc: "Connect your GOG account" },
};

// ─── Spinner component ───
function Spinner({ className = "h-4 w-4" }: { className?: string }) {
  return (
    <svg className={`animate-spin ${className}`} viewBox="0 0 24 24" fill="none">
      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
    </svg>
  );
}

// ─── Progress bar component ───
function ProgressBar({ percentage, downloaded_mb, total_mb, speed_mbps }: WineProgressResponse) {
  const clamped = Math.min(100, Math.max(0, percentage));
  return (
    <div className="mt-2">
      <div className="flex items-center justify-between text-[10px] text-zinc-500 mb-1">
        <span>{downloaded_mb.toFixed(1)} MB / {total_mb.toFixed(1)} MB</span>
        <span>{speed_mbps.toFixed(1)} MB/s</span>
      </div>
      <div className="h-2 w-full overflow-hidden rounded-full bg-zinc-800">
        <div
          className="h-full rounded-full bg-gradient-to-r from-emerald-600 to-emerald-400 transition-all duration-500 ease-out"
          style={{ width: `${clamped}%` }}
        />
      </div>
      <p className="mt-1 text-center text-[10px] text-zinc-500">{clamped.toFixed(0)}%</p>
    </div>
  );
}

// ════════════════════════════════════════════════════════════════════════════
//  Settings Page
// ════════════════════════════════════════════════════════════════════════════

export default function SettingsPage() {
  // ─── Store state ───
  const [storeStatuses, setStoreStatuses] = useState<Record<string, { is_authenticated: boolean }>>({});
  const [loadingStoreStatus, setLoadingStoreStatus] = useState(true);
  const [showAuthInput, setShowAuthInput] = useState<Record<string, boolean>>({});
  const [authInstructions, setAuthInstructions] = useState<Record<string, string>>({});
  const [authCodes, setAuthCodes] = useState<Record<string, string>>({});
  const [authing, setAuthing] = useState<string | null>(null);
  const [authMessage, setAuthMessage] = useState<{ store: string; msg: string; ok: boolean } | null>(null);
  const [syncing, setSyncing] = useState<string | null>(null);
  const [syncMessage, setSyncMessage] = useState<{ store: string; msg: string; ok: boolean } | null>(null);
  const [autoLogging, setAutoLogging] = useState<string | null>(null);

  // ─── Wine Manager state ───
  const [wineTab, setWineTab] = useState<"available" | "installed">("available");
  const [availableWine, setAvailableWine] = useState<WineVersionResponse[]>([]);
  const [installedWine, setInstalledWine] = useState<WineVersionResponse[]>([]);
  const [wineLoading, setWineLoading] = useState(false);
  const [wineError, setWineError] = useState<string | null>(null);
  const [installingWine, setInstallingWine] = useState<string | null>(null);
  const [deletingWine, setDeletingWine] = useState<string | null>(null);
  const [wineProgress, setWineProgress] = useState<WineProgressResponse | null>(null);
  const winePollRef = useRef<ReturnType<typeof setInterval> | null>(null);

  // ─── Cover refresh state ───
  const [refreshingCovers, setRefreshingCovers] = useState(false);
  const [coversProgress, setCoversProgress] = useState<string | null>(null);

  // ─── Runners state ───
  const [runners, setRunners] = useState<RunnerInfo[]>([]);
  const [runnersLoading, setRunnersLoading] = useState(true);
  const [detecting, setDetecting] = useState(false);

  // ─── Load data on mount ───
  useEffect(() => {
    loadStoreStatuses();
    loadRunners();
    loadWineData();
  }, []);

  // Cleanup wine poll on unmount
  useEffect(() => {
    return () => {
      if (winePollRef.current) clearInterval(winePollRef.current);
    };
  }, []);

  // ══════════════════════════════════════════════════════════════
  //  Store Methods
  // ══════════════════════════════════════════════════════════════

  async function loadStoreStatuses() {
    setLoadingStoreStatus(true);
    const results: Record<string, { is_authenticated: boolean }> = {};
    await Promise.all(
      STORE_NAMES.map(async (name) => {
        try {
          const status = await api.getStoreStatus(name);
          results[name] = { is_authenticated: status.is_authenticated };
        } catch {
          results[name] = { is_authenticated: false };
        }
      }),
    );
    setStoreStatuses(results);
    setLoadingStoreStatus(false);
  }

  async function handleLoginInBrowser(storeName: string) {
    try {
      const data = await api.getStoreAuthUrl(storeName);
      setAuthInstructions((prev) => ({
        ...prev,
        [storeName]: data.instructions || (STORE_AUTH_INSTRUCTIONS[storeName] ?? "Follow the steps in your browser to authenticate."),
      }));
      setShowAuthInput((prev) => ({ ...prev, [storeName]: true }));
      setAuthMessage(null);
      // Open the auth URL in the system browser
      window.open(data.auth_url, "_blank");
    } catch (err) {
      const msg = err instanceof Error ? err.message : "Failed to get auth URL";
      setAuthMessage({ store: storeName, msg: `❌ ${msg}`, ok: false });
    }
  }

  async function handleAutoLogin(storeName: string) {
    setAutoLogging(storeName);
    setAuthMessage(null);
    try {
      await api.browserAuth(storeName);
      setAuthMessage({ store: storeName, msg: "✅ Authenticated!", ok: true });
      setShowAuthInput((prev) => ({ ...prev, [storeName]: false }));
      await loadStoreStatuses();
    } catch (err) {
      const msg = typeof err === 'object' && err !== null ? String((err as Record<string, unknown>).message ?? "") || String(err) : String(err);
      const isTimeout = /timed? ?out|timeout|408/i.test(msg);
      const isNotImpl = /does not support|not implemented|501/i.test(msg);
      setAuthMessage({
        store: storeName,
        msg: isTimeout
          ? "❌ Auth timed out after 120s. Please try again."
          : isNotImpl
            ? "❌ Auto login not available for this store. Use the manual login method."
            : `❌ ${msg}`,
        ok: false,
      });
    } finally {
      setAutoLogging(null);
    }
  }

  async function handleConnect(storeName: string) {
    const code = authCodes[storeName];
    if (!code?.trim()) return;

    setAuthing(storeName);
    setAuthMessage(null);
    try {
      await api.connectStore(storeName, code);
      setAuthMessage({ store: storeName, msg: "✅ Authenticated!", ok: true });
      setAuthCodes((prev) => ({ ...prev, [storeName]: "" }));
      setShowAuthInput((prev) => ({ ...prev, [storeName]: false }));
      await loadStoreStatuses();
    } catch (err) {
      const msg = err instanceof Error ? err.message : "Authentication failed";
      setAuthMessage({ store: storeName, msg: `❌ ${msg}`, ok: false });
    } finally {
      setAuthing(null);
    }
  }

  async function handleSync(storeName: string) {
    setSyncing(storeName);
    setSyncMessage(null);
    try {
      // Start background sync
      const { task_id } = await api.startBackgroundSync(storeName);

      // Poll for completion
      let completed = false;
      let attempts = 0;
      const maxAttempts = 300; // 300 * 2s = 10 minutes max

      while (!completed && attempts < maxAttempts) {
        await new Promise(r => setTimeout(r, 2000));
        attempts++;

        const status = await api.getSyncStatus(task_id);

        if (status.status === "completed") {
          const imported = status.result?.imported ?? 0;
          const errors = status.result?.errors ?? [];
          const total = status.result?.total ?? 0;
          const errMsg = errors.length > 0 ? ` (${errors.length} errors)` : "";
          setSyncMessage({
            store: storeName,
            msg: `✅ Synced ${imported}/${total} games${errMsg}`,
            ok: errors.length === 0
          });
          completed = true;
        } else if (status.status === "failed") {
          setSyncMessage({
            store: storeName,
            msg: `❌ Sync failed: ${status.error ?? "Unknown error"}`,
            ok: false
          });
          completed = true;
        }
        // "running" → continue polling
      }

      if (!completed) {
        setSyncMessage({
          store: storeName,
          msg: "❌ Sync timed out after 10 minutes",
          ok: false
        });
      }
    } catch (err) {
      const msg = err instanceof Error ? err.message : "Sync failed";
      setSyncMessage({ store: storeName, msg: `❌ ${msg}`, ok: false });
    } finally {
      setSyncing(null);
    }
  }

  // ══════════════════════════════════════════════════════════════
  //  Wine Methods
  // ══════════════════════════════════════════════════════════════

  async function loadWineData() {
    setWineLoading(true);
    setWineError(null);
    try {
      const [available, installed] = await Promise.all([
        api.listAvailableWineVersions(),
        api.listInstalledWineVersions(),
      ]);
      setAvailableWine(available);
      setInstalledWine(installed);
    } catch (err) {
      const msg = err instanceof Error ? err.message : "Failed to load wine versions";
      setWineError(msg);
    } finally {
      setWineLoading(false);
    }
  }

  const stopWinePoll = useCallback(() => {
    if (winePollRef.current) {
      clearInterval(winePollRef.current);
      winePollRef.current = null;
    }
  }, []);

  async function startWineProgressPoll(versionName: string) {
    stopWinePoll();
    winePollRef.current = setInterval(async () => {
      try {
        const progress = await api.getWineDownloadProgress(versionName);
        setWineProgress(progress);
        if (progress.percentage >= 100) {
          stopWinePoll();
          setInstallingWine(null);
          setWineProgress(null);
          await loadWineData();
        }
      } catch {
        stopWinePoll();
        setInstallingWine(null);
        setWineProgress(null);
      }
    }, 2000);
  }

  async function handleInstallWine(version: WineVersionResponse) {
    if (!version.url) return;
    setInstallingWine(version.name);
    setWineProgress(null);
    try {
      await api.installWineVersion(version.name, version.url);
      await startWineProgressPoll(version.name);
    } catch (err) {
      const msg = err instanceof Error ? err.message : "Failed to install";
      setWineError(msg);
      setInstallingWine(null);
    }
  }

  async function handleDeleteWine(versionName: string) {
    setDeletingWine(versionName);
    try {
      await api.deleteWineVersion(versionName);
      await loadWineData();
    } catch (err) {
      const msg = err instanceof Error ? err.message : "Failed to delete";
      setWineError(msg);
    } finally {
      setDeletingWine(null);
    }
  }

  // ══════════════════════════════════════════════════════════════
  //  Runner Methods
  // ══════════════════════════════════════════════════════════════

  async function loadRunners() {
    try {
      const runnerList = await api.listRunners();
      setRunners(runnerList);
    } catch {
      // Silently fail — runners are supplementary
    } finally {
      setRunnersLoading(false);
    }
  }

  async function handleDetectRunners() {
    setDetecting(true);
    try {
      const detected = await api.detectRunners();
      setRunners(detected);
    } catch {
      // Silently fail
    } finally {
      setDetecting(false);
    }
  }

  // ══════════════════════════════════════════════════════════════
  //  Cover Methods
  // ══════════════════════════════════════════════════════════════

  async function handleRefreshCovers() {
    setRefreshingCovers(true);
    setCoversProgress(null);
    try {
      const result = await api.refreshAllCovers();
      setCoversProgress(`Found ${result.refreshed} covers, ${result.failed} failed`);
    } catch (err) {
      const msg = err instanceof Error ? err.message : "Failed";
      setCoversProgress(`Error: ${msg}`);
    } finally {
      setRefreshingCovers(false);
    }
  }

  // ══════════════════════════════════════════════════════════════
  //  Render
  // ══════════════════════════════════════════════════════════════

  return (
    <div className="h-full overflow-y-auto">
      <div className="mx-auto max-w-4xl p-6">
        <h1 className="mb-8 text-2xl font-bold tracking-tight text-zinc-100">
          Settings
        </h1>

        {/* ═════════ STORE ACCOUNTS ═════════ */}
        <section className="mb-12">
          <div className="mb-5 flex items-center gap-3">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-purple-900/40">
              <svg className="h-4 w-4 text-purple-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
              </svg>
            </div>
            <h2 className="text-lg font-semibold text-zinc-200">Store Accounts</h2>
          </div>

          <div className="grid gap-5 sm:grid-cols-2">
            {STORE_NAMES.map((storeName) => {
              const status = storeStatuses[storeName];
              const isAuth = status?.is_authenticated ?? false;
              const storeInfo = STORE_DISPLAY[storeName];
              if (!storeInfo) return null;

              return (
                <div key={storeName} className="glass rounded-xl p-5 transition-all duration-200 hover:border-zinc-700/60">
                  {/* Header row */}
                  <div className="mb-4 flex items-center justify-between">
                    <div className="flex items-center gap-3">
                      <span className="text-2xl">{storeInfo.icon}</span>
                      <div>
                        <h3 className="font-medium text-zinc-200">{storeInfo.label}</h3>
                        <p className="text-xs text-zinc-500">{storeInfo.desc}</p>
                      </div>
                    </div>
                    <div className="flex items-center gap-2">
                      {loadingStoreStatus ? (
                        <Spinner className="h-4 w-4 text-zinc-500" />
                      ) : (
                        <span
                          className={`flex h-2.5 w-2.5 rounded-full ${
                            isAuth ? "bg-emerald-500 shadow-sm shadow-emerald-500/40" : "bg-zinc-600"
                          }`}
                          title={isAuth ? "Connected" : "Disconnected"}
                        />
                      )}
                    </div>
                  </div>

                  {/* Auth controls */}
                  {!isAuth ? (
                    <>
                      {/* Login in Browser button */}
                      <button
                        onClick={() => handleLoginInBrowser(storeName)}
                        className="mb-3 flex w-full items-center justify-center gap-2 rounded-lg border border-purple-700/40 bg-purple-900/30 px-4 py-2 text-sm font-medium text-purple-300 transition-all hover:bg-purple-800/40 hover:border-purple-600/60"
                      >
                        <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 12a9 9 0 01-9 9m9-9a9 9 0 00-9-9m9 9H3m9 9a9 9 0 01-9-9m9 9c1.657 0 3-4.03 3-9s-1.343-9-3-9m0 18c-1.657 0-3-4.03-3-9s1.343-9 3-9m-9 9a9 9 0 019-9" />
                        </svg>
                        Login in Browser
                      </button>

                      {/* Auto Login button — opens browser automatically */}
                      <button
                        onClick={() => handleAutoLogin(storeName)}
                        disabled={autoLogging === storeName}
                        className="mb-3 flex w-full items-center justify-center gap-2 rounded-lg border border-emerald-700/40 bg-emerald-900/30 px-4 py-2 text-sm font-medium text-emerald-300 transition-all hover:bg-emerald-800/40 hover:border-emerald-600/60 disabled:opacity-50"
                      >
                        {autoLogging === storeName ? (
                          <>
                            <Spinner className="h-4 w-4" />
                            Waiting for browser login...
                          </>
                        ) : (
                          <>
                            <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
                            </svg>
                            Auto Login (Browser)
                          </>
                        )}
                      </button>

                      {/* Instructions + input (shown after clicking login) */}
                      {showAuthInput[storeName] && (
                        <div className="mb-3 space-y-3 animate-fadeIn">
                          <div className="rounded-lg border border-zinc-700/50 bg-zinc-800/40 p-3">
                            <p className="text-xs leading-relaxed text-zinc-400">
                              {authInstructions[storeName] ?? STORE_AUTH_INSTRUCTIONS[storeName] ?? "Follow your browser to authenticate."}
                            </p>
                          </div>
                          <div className="flex gap-2">
                            <input
                              type="text"
                              placeholder="Enter authorization code..."
                              value={authCodes[storeName] ?? ""}
                              onChange={(e) =>
                                setAuthCodes((prev) => ({ ...prev, [storeName]: e.target.value }))
                              }
                              className="flex-1 rounded-lg border border-zinc-700 bg-zinc-800 px-3 py-2 text-sm text-zinc-200 placeholder-zinc-600 focus:border-emerald-600 focus:outline-none"
                              onKeyDown={(e) => e.key === "Enter" && handleConnect(storeName)}
                            />
                            <button
                              onClick={() => handleConnect(storeName)}
                              disabled={authing === storeName}
                              className="rounded-lg bg-purple-700 px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-purple-600 disabled:opacity-50"
                            >
                              {authing === storeName ? (
                                <span className="flex items-center gap-1.5">
                                  <Spinner className="h-3.5 w-3.5" />
                                  Connecting...
                                </span>
                              ) : (
                                "Connect"
                              )}
                            </button>
                          </div>
                          {authMessage?.store === storeName && (
                            <p className={`text-xs ${authMessage.ok ? "text-emerald-400" : "text-red-400"}`}>
                              {authMessage.msg}
                            </p>
                          )}
                        </div>
                      )}
                    </>
                  ) : (
                    <div className="space-y-3">
                      {/* Connected state */}
                      <div className="flex items-center gap-2 rounded-lg bg-emerald-900/20 px-3 py-2">
                        <span className="flex h-2 w-2 rounded-full bg-emerald-500" />
                        <span className="text-xs font-medium text-emerald-400">Connected</span>
                      </div>

                      {/* Sync button */}
                      <button
                        onClick={() => handleSync(storeName)}
                        disabled={syncing === storeName}
                        className="flex w-full items-center justify-center gap-2 rounded-lg bg-zinc-800 px-4 py-2 text-sm text-zinc-300 transition-colors hover:bg-zinc-700 disabled:opacity-50"
                      >
                        {syncing === storeName ? (
                          <>
                            <Spinner className="h-3.5 w-3.5" />
                            Syncing games...
                          </>
                        ) : (
                          <>
                            <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                            </svg>
                            Sync Games
                          </>
                        )}
                      </button>
                      {syncMessage?.store === storeName && (
                        <p className={`text-xs ${syncMessage.ok ? "text-emerald-400" : "text-red-400"}`}>
                          {syncMessage.msg}
                        </p>
                      )}
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </section>

        {/* ═════════ WINE MANAGER ═════════ */}
        <section className="mb-12">
          <div className="mb-5 flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-amber-900/40">
                <svg className="h-4 w-4 text-amber-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19.428 15.428a2 2 0 00-1.022-.547l-2.387-.477a6 6 0 00-3.86.517l-.318.158a6 6 0 01-3.86.517L6.05 15.21a2 2 0 00-1.806.547M8 4h8l-1 1v5.172a2 2 0 00.586 1.414l5 5c1.26 1.26.367 3.414-1.415 3.414H4.828c-1.782 0-2.674-2.154-1.414-3.414l5-5A2 2 0 009 10.172V5L8 4z" />
                </svg>
              </div>
              <h2 className="text-lg font-semibold text-zinc-200">Wine Manager</h2>
            </div>

            {/* Refresh */}
            <button
              onClick={loadWineData}
              disabled={wineLoading}
              className="rounded-lg bg-zinc-800 px-3 py-1.5 text-sm text-zinc-400 hover:bg-zinc-700 hover:text-zinc-200 transition-colors disabled:opacity-50"
            >
              {wineLoading ? "Loading..." : "Refresh"}
            </button>
          </div>

          {/* Tabs */}
          <div className="mb-4 flex gap-1 rounded-lg bg-zinc-900 p-1">
            <button
              onClick={() => setWineTab("available")}
              className={`flex-1 rounded-md px-4 py-2 text-sm font-medium transition-all ${
                wineTab === "available"
                  ? "bg-zinc-800 text-zinc-100 shadow-sm"
                  : "text-zinc-500 hover:text-zinc-300"
              }`}
            >
              Available Versions
            </button>
            <button
              onClick={() => setWineTab("installed")}
              className={`flex-1 rounded-md px-4 py-2 text-sm font-medium transition-all ${
                wineTab === "installed"
                  ? "bg-zinc-800 text-zinc-100 shadow-sm"
                  : "text-zinc-500 hover:text-zinc-300"
              }`}
            >
              Installed
              {installedWine.length > 0 && (
                <span className="ml-2 rounded-full bg-emerald-800/40 px-1.5 py-0.5 text-[10px] text-emerald-300">
                  {installedWine.length}
                </span>
              )}
            </button>
          </div>

          {/* Wine content */}
          <div className="glass rounded-xl">
            {wineError && (
              <div className="border-b border-red-800/30 p-4 text-sm text-red-400">
                {wineError}
              </div>
            )}

            {/* Download progress bar */}
            {wineProgress && (
              <div className="border-b border-zinc-800/50 p-4">
                <div className="flex items-center gap-2 mb-2">
                  <Spinner className="h-3.5 w-3.5 text-emerald-400" />
                  <span className="text-xs font-medium text-zinc-300">
                    Downloading {installingWine}...
                  </span>
                </div>
                <ProgressBar {...wineProgress} />
              </div>
            )}

            {wineLoading ? (
              <div className="flex items-center justify-center py-12">
                <Spinner className="h-6 w-6 text-emerald-500" />
              </div>
            ) : wineTab === "available" ? (
              <WineAvailableList
                versions={availableWine}
                installedNames={new Set(installedWine.map((v) => v.name))}
                installingWine={installingWine}
                onInstall={handleInstallWine}
              />
            ) : (
              <WineInstalledList
                versions={installedWine}
                deletingWine={deletingWine}
                onDelete={handleDeleteWine}
              />
            )}
          </div>
        </section>

        {/* ═════════ RUNNERS ═════════ */}
        <section className="mb-12">
          <div className="mb-5 flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-emerald-900/40">
                <svg className="h-4 w-4 text-emerald-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z" />
                </svg>
              </div>
              <h2 className="text-lg font-semibold text-zinc-200">Runners</h2>
            </div>
            <button
              onClick={handleDetectRunners}
              disabled={detecting}
              className="rounded-lg bg-zinc-800 px-3 py-1.5 text-sm text-zinc-300 hover:bg-zinc-700 transition-colors disabled:opacity-50"
            >
              {detecting ? "Detecting..." : "Detect Runners"}
            </button>
          </div>

          {runnersLoading ? (
            <div className="flex items-center justify-center py-12">
              <Spinner className="h-6 w-6 text-emerald-500" />
            </div>
          ) : (
            <div className="grid gap-3 sm:grid-cols-3">
              {runners.length === 0 ? (
                <div className="col-span-full py-8 text-center text-sm text-zinc-600">
                  No runners detected. Click "Detect Runners" to scan your system.
                </div>
              ) : (
                runners.map((runner) => (
                  <div key={runner.name} className="glass rounded-xl p-4 transition-all duration-200 hover:border-zinc-700/60">
                    <div className="flex items-center justify-between">
                      <h3 className="text-sm font-medium text-zinc-200">
                        {runner.display_name}
                      </h3>
                      <span
                        className={`flex h-2.5 w-2.5 rounded-full ${
                          runner.is_installed ? "bg-emerald-500 shadow-sm shadow-emerald-500/40" : "bg-zinc-600"
                        }`}
                      />
                    </div>
                    <p className="mt-1 text-xs text-zinc-500">
                      {runner.is_installed ? runner.version : "Not installed"}
                    </p>
                    {runner.path && (
                      <p className="mt-1 truncate font-mono text-[10px] text-zinc-600">
                        {runner.path}
                      </p>
                    )}
                  </div>
                ))
              )}
            </div>
          )}
        </section>

        {/* ═════════ ABOUT ═════════ */}
        <section className="mb-10">
          <div className="mb-5 flex items-center gap-3">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-blue-900/40">
              <svg className="h-4 w-4 text-blue-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            </div>
            <h2 className="text-lg font-semibold text-zinc-200">About</h2>
          </div>
          <div className="glass rounded-xl p-5">
            <p className="text-sm text-zinc-400 leading-relaxed">
              New Heroic — A modern open-source game launcher for Linux. Built
              with Tauri, React, and Python FastAPI.
            </p>
            <p className="mt-3 text-xs text-zinc-600">
              Version 0.1.0 — GPLv3 License
            </p>

            {/* Refresh Covers */}
            <div className="mt-5 border-t border-zinc-800/50 pt-4">
              <button
                onClick={handleRefreshCovers}
                disabled={refreshingCovers}
                className="rounded-lg bg-zinc-800 px-4 py-2 text-sm text-zinc-300 transition-colors hover:bg-zinc-700 disabled:opacity-50"
              >
                {refreshingCovers ? (
                  <span className="flex items-center gap-2">
                    <Spinner className="h-3.5 w-3.5" />
                    Refreshing Covers...
                  </span>
                ) : (
                  "Refresh Missing Covers"
                )}
              </button>
              {coversProgress && (
                <p className="mt-2 text-xs text-zinc-500">{coversProgress}</p>
              )}
            </div>
          </div>
        </section>
      </div>
    </div>
  );
}

// ════════════════════════════════════════════════════════════════════════════
//  Wine Available List
// ════════════════════════════════════════════════════════════════════════════

function WineAvailableList({
  versions,
  installedNames,
  installingWine,
  onInstall,
}: {
  versions: WineVersionResponse[];
  installedNames: Set<string>;
  installingWine: string | null;
  onInstall: (version: WineVersionResponse) => void;
}) {
  if (versions.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-12 text-zinc-600">
        <svg className="mb-3 h-10 w-10" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1} d="M19.428 15.428a2 2 0 00-1.022-.547l-2.387-.477a6 6 0 00-3.86.517l-.318.158a6 6 0 01-3.86.517L6.05 15.21a2 2 0 00-1.806.547M8 4h8l-1 1v5.172a2 2 0 00.586 1.414l5 5c1.26 1.26.367 3.414-1.415 3.414H4.828c-1.782 0-2.674-2.154-1.414-3.414l5-5A2 2 0 009 10.172V5L8 4z" />
        </svg>
        <p className="text-sm">No wine versions available</p>
        <p className="mt-1 text-xs text-zinc-500">
          Could not fetch available wine versions from upstream.
        </p>
      </div>
    );
  }

  return (
    <div className="divide-y divide-zinc-800/50">
      {versions.map((version) => {
        const isInstalled = installedNames.has(version.name);
        const isInstalling = installingWine === version.name;
        return (
          <div key={version.name} className="flex items-center justify-between px-4 py-3 transition-colors hover:bg-zinc-800/30">
            <div className="min-w-0 flex-1">
              <p className="truncate text-sm font-medium text-zinc-200">
                {version.name}
              </p>
              <div className="mt-0.5 flex items-center gap-3 text-[11px] text-zinc-500">
                <span>
                  {version.source}
                </span>
                {version.release_date && (
                  <>
                    <span className="text-zinc-700">•</span>
                    <span>{version.release_date}</span>
                  </>
                )}
              </div>
            </div>
            <div className="ml-4 shrink-0">
              {isInstalled ? (
                <span className="inline-flex items-center gap-1 rounded-md bg-emerald-900/30 px-2.5 py-1 text-[11px] font-medium text-emerald-400">
                  <svg className="h-3 w-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                  </svg>
                  Installed
                </span>
              ) : isInstalling ? (
                <span className="inline-flex items-center gap-1.5 rounded-md bg-blue-900/30 px-2.5 py-1 text-[11px] font-medium text-blue-400">
                  <Spinner className="h-3 w-3" />
                  Installing...
                </span>
              ) : (
                <button
                  onClick={() => onInstall(version)}
                  disabled={!version.url}
                  className="rounded-md bg-zinc-800 px-3 py-1.5 text-xs font-medium text-zinc-300 transition-colors hover:bg-emerald-700 hover:text-white disabled:cursor-not-allowed disabled:opacity-40"
                  title={!version.url ? "No download URL available" : `Install ${version.name}`}
                >
                  Install
                </button>
              )}
            </div>
          </div>
        );
      })}
    </div>
  );
}

// ════════════════════════════════════════════════════════════════════════════
//  Wine Installed List
// ════════════════════════════════════════════════════════════════════════════

function WineInstalledList({
  versions,
  deletingWine,
  onDelete,
}: {
  versions: WineVersionResponse[];
  deletingWine: string | null;
  onDelete: (versionName: string) => void;
}) {
  if (versions.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-12 text-zinc-600">
        <svg className="mb-3 h-10 w-10" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1} d="M19.428 15.428a2 2 0 00-1.022-.547l-2.387-.477a6 6 0 00-3.86.517l-.318.158a6 6 0 01-3.86.517L6.05 15.21a2 2 0 00-1.806.547M8 4h8l-1 1v5.172a2 2 0 00.586 1.414l5 5c1.26 1.26.367 3.414-1.415 3.414H4.828c-1.782 0-2.674-2.154-1.414-3.414l5-5A2 2 0 009 10.172V5L8 4z" />
        </svg>
        <p className="text-sm">No wine versions installed</p>
        <p className="mt-1 text-xs text-zinc-500">
          Install a wine version from the "Available" tab.
        </p>
      </div>
    );
  }

  return (
    <div className="divide-y divide-zinc-800/50">
      {versions.map((version) => {
        const isDeleting = deletingWine === version.name;
        return (
          <div key={version.name} className="flex items-center justify-between px-4 py-3 transition-colors hover:bg-zinc-800/30">
            <div className="min-w-0 flex-1">
              <p className="truncate text-sm font-medium text-zinc-200">
                {version.name}
              </p>
              <div className="mt-0.5 flex items-center gap-3 text-[11px] text-zinc-500">
                <span>{version.source}</span>
                {version.release_date && (
                  <>
                    <span className="text-zinc-700">•</span>
                    <span>{version.release_date}</span>
                  </>
                )}
                {version.install_path && (
                  <>
                    <span className="text-zinc-700">•</span>
                    <span className="font-mono truncate max-w-[180px]">
                      {version.install_path}
                    </span>
                  </>
                )}
              </div>
            </div>
            <div className="ml-4 shrink-0">
              <button
                onClick={() => onDelete(version.name)}
                disabled={isDeleting}
                className="rounded-md bg-red-900/30 px-3 py-1.5 text-xs font-medium text-red-400 transition-colors hover:bg-red-800/50 disabled:opacity-50"
              >
                {isDeleting ? "Deleting..." : "Delete"}
              </button>
            </div>
          </div>
        );
      })}
    </div>
  );
}
