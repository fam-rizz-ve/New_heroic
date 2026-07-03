import { useState, useEffect, useCallback } from "react";
import { api, type GameResponse, type GameSettingsResponse, type WineVersionResponse } from "@/lib/api";

interface GameDetailPageProps {
  gameId: string;
  onBack: () => void;
}

type SettingsTab = "general" | "advanced" | "compatibility" | "system";

const TABS: { key: SettingsTab; label: string }[] = [
  { key: "general", label: "General" },
  { key: "advanced", label: "Advanced" },
  { key: "compatibility", label: "Compatibility" },
  { key: "system", label: "System" },
];

const FSR_QUALITY_OPTIONS = ["ultra", "quality", "balanced", "performance"];

const RUNNER_OPTIONS = [
  { value: "wine", label: "Wine" },
  { value: "proton", label: "Proton" },
  { value: "native", label: "Native" },
];

const WINE_ARCH_OPTIONS = [
  { value: "win64", label: "Win64 (64-bit)" },
  { value: "win32", label: "Win32 (32-bit)" },
];

// ─── Spinner ───
function Spinner({ className = "h-4 w-4" }: { className?: string }) {
  return (
    <svg className={`animate-spin ${className}`} viewBox="0 0 24 24" fill="none">
      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
    </svg>
  );
}

// ─── Toggle Switch ───
function Toggle({ enabled, onChange, label }: { enabled: boolean; onChange: (v: boolean) => void; label: string }) {
  return (
    <label className="flex cursor-pointer items-center justify-between py-2">
      <span className="text-sm text-zinc-300">{label}</span>
      <div className="relative">
        <input
          type="checkbox"
          checked={enabled}
          onChange={(e) => onChange(e.target.checked)}
          className="sr-only"
        />
        <div
          className={`h-5 w-9 rounded-full transition-colors ${
            enabled ? "bg-emerald-600" : "bg-zinc-700"
          }`}
        >
          <div
            className={`h-4 w-4 rounded-full bg-white transition-all mt-0.5 ${
              enabled ? "translate-x-[18px]" : "translate-x-0.5"
            }`}
          />
        </div>
      </div>
    </label>
  );
}

// ════════════════════════════════════════════════════════════════════════════
//  Game Detail Page
// ════════════════════════════════════════════════════════════════════════════

export default function GameDetailPage({ gameId, onBack }: GameDetailPageProps) {
  const [game, setGame] = useState<GameResponse | null>(null);
  const [settings, setSettings] = useState<GameSettingsResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<SettingsTab>("general");
  const [saving, setSaving] = useState(false);
  const [saveMessage, setSaveMessage] = useState<string | null>(null);
  const [actionLoading, setActionLoading] = useState<string | null>(null);
  const [wineVersions, setWineVersions] = useState<WineVersionResponse[]>([]);

  // ─── Env vars editor state ───
  const [envEntries, setEnvEntries] = useState<Array<{ key: string; value: string }>>([]);

  // ─── Load data ───
  const loadData = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [gameData, settingsData, wineData] = await Promise.all([
        api.getGame(gameId),
        api.getGameSettings(gameId),
        api.listInstalledWineVersions().catch(() => [] as WineVersionResponse[]),
      ]);
      setGame(gameData);
      setSettings(settingsData);
      setWineVersions(wineData);
      // Initialise env vars editor
      setEnvEntries(
        Object.entries(settingsData.env_vars).map(([k, v]) => ({ key: k, value: v }))
      );
    } catch (err) {
      const msg = err instanceof Error ? err.message : "Failed to load game";
      setError(msg);
    } finally {
      setLoading(false);
    }
  }, [gameId]);

  useEffect(() => {
    loadData();
  }, [loadData]);

  // ─── Settings update ───
  async function updateSettings(updated: Partial<GameSettingsResponse>) {
    if (!settings) return;
    setSaving(true);
    setSaveMessage(null);
    try {
      const result = await api.updateGameSettings(gameId, updated);
      setSettings(result);
      setSaveMessage("Saved");
      setTimeout(() => setSaveMessage(null), 2000);
    } catch (err) {
      const msg = err instanceof Error ? err.message : "Failed to save";
      setSaveMessage(`Error: ${msg}`);
    } finally {
      setSaving(false);
    }
  }

  function updateLocalSetting<K extends keyof GameSettingsResponse>(
    key: K,
    value: GameSettingsResponse[K]
  ) {
    if (!settings) return;
    setSettings({ ...settings, [key]: value });
  }

  function saveSetting<K extends keyof GameSettingsResponse>(key: K, value: GameSettingsResponse[K]) {
    updateLocalSetting(key, value);
    updateSettings({ [key]: value });
  }

  // ─── Env vars helpers ───
  function syncEnvVars(entries: Array<{ key: string; value: string }>) {
    const env_vars: Record<string, string> = {};
    for (const entry of entries) {
      if (entry.key.trim()) {
        env_vars[entry.key] = entry.value;
      }
    }
    return env_vars;
  }

  function handleEnvChange(index: number, field: "key" | "value", val: string) {
    const next = [...envEntries];
    if (next[index]) {
      next[index] = { ...next[index], [field]: val };
    }
    setEnvEntries(next);
  }

  function addEnvEntry() {
    setEnvEntries((prev) => [...prev, { key: "", value: "" }]);
  }

  function removeEnvEntry(index: number) {
    const next = envEntries.filter((_, i) => i !== index);
    setEnvEntries(next);
  }

  async function saveEnvVars() {
    const env_vars = syncEnvVars(envEntries);
    updateSettings({ env_vars });
  }

  // ─── Game actions ───
  async function handleAction(action: "install" | "launch" | "uninstall" | "close") {
    setActionLoading(action);
    setError(null);
    try {
      if (action === "install") await api.installGame(gameId);
      else if (action === "launch") await api.launchGame(gameId);
      else if (action === "uninstall") await api.uninstallGame(gameId);
      else if (action === "close") await api.closeGame(gameId);
      // Refresh game data
      const gameData = await api.getGame(gameId);
      setGame(gameData);
    } catch (err) {
      const msg = err instanceof Error ? err.message : "Action failed";
      setError(msg);
    } finally {
      setActionLoading(null);
    }
  }

  // ─── Render ───
  if (loading) {
    return (
      <div className="flex h-full items-center justify-center">
        <Spinner className="h-8 w-8 text-emerald-500" />
      </div>
    );
  }

  if (error && !game) {
    return (
      <div className="flex h-full flex-col items-center justify-center gap-4 p-6">
        <div className="rounded-xl border border-red-800/40 bg-red-950/30 p-6 text-center">
          <p className="text-sm text-red-300">{error}</p>
          <button
            onClick={onBack}
            className="mt-4 rounded-lg bg-zinc-800 px-4 py-2 text-sm text-zinc-300 hover:bg-zinc-700"
          >
            Back to Library
          </button>
        </div>
      </div>
    );
  }

  if (!game || !settings) {
    return null;
  }

  const isInstalled = game.status === "installed";
  const isRunning = game.status === "running";
  const isInstalling = game.status === "installing";

  return (
    <div className="flex h-full flex-col overflow-y-auto">
      {/* ═══════════════ HERO SECTION ═══════════════ */}
      <div className="relative">
        {/* Hero gradient background */}
        <div className="h-48 sm:h-56 w-full bg-gradient-to-br from-zinc-800 via-zinc-900 to-zinc-950">
          {game.cover_art_url ? (
            <img
              src={game.cover_art_url}
              alt={game.title}
              className="h-full w-full object-cover opacity-40"
            />
          ) : (
            <div className="absolute inset-0 bg-gradient-to-br from-emerald-900/20 via-zinc-900 to-purple-900/20" />
          )}
          {/* Bottom fade */}
          <div className="absolute inset-x-0 bottom-0 h-24 bg-gradient-to-t from-zinc-950 to-transparent" />
        </div>

        {/* Back button */}
        <button
          onClick={onBack}
          className="absolute left-4 top-4 flex h-8 w-8 items-center justify-center rounded-lg bg-zinc-900/70 text-zinc-400 backdrop-blur-sm transition-colors hover:bg-zinc-800 hover:text-zinc-200"
        >
          <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
          </svg>
        </button>

        {/* Game title overlay */}
        <div className="absolute bottom-4 left-6 right-6">
          <div className="flex items-end justify-between">
            <div>
              <div className="flex items-center gap-2 mb-1">
                <span className="rounded-md bg-zinc-900/80 px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wider text-zinc-400 backdrop-blur-sm">
                  {game.store}
                </span>
                <span
                  className={`rounded-md px-2 py-0.5 text-[10px] font-medium backdrop-blur-sm ${
                    isRunning
                      ? "bg-green-900/60 text-green-300"
                      : isInstalled
                        ? "bg-emerald-900/60 text-emerald-300"
                        : "bg-zinc-900/60 text-zinc-400"
                  }`}
                >
                  {isRunning ? "Playing" : isInstalled ? "Installed" : isInstalling ? "Installing" : "Not Installed"}
                </span>
              </div>
              <h1 className="text-2xl font-bold tracking-tight text-white drop-shadow-lg">
                {game.title}
              </h1>
            </div>
          </div>
        </div>
      </div>

      {/* ═══════════════ ACTION BUTTONS ═══════════════ */}
      <div className="flex items-center gap-3 border-b border-zinc-800/50 px-6 py-4">
        {!isInstalled && !isRunning && !isInstalling && (
          <button
            onClick={() => handleAction("install")}
            disabled={actionLoading === "install"}
            className="flex items-center gap-2 rounded-lg bg-emerald-700 px-6 py-2.5 text-sm font-semibold text-white transition-all hover:bg-emerald-600 disabled:opacity-50"
          >
            {actionLoading === "install" ? (
              <>
                <Spinner className="h-4 w-4" />
                Installing...
              </>
            ) : (
              <>
                <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
                </svg>
                Install
              </>
            )}
          </button>
        )}
        {isInstalled && (
          <button
            onClick={() => handleAction("launch")}
            disabled={actionLoading === "launch"}
            className="flex items-center gap-2 rounded-lg bg-emerald-700 px-6 py-2.5 text-sm font-semibold text-white transition-all hover:bg-emerald-600 disabled:opacity-50"
          >
            {actionLoading === "launch" ? (
              <>
                <Spinner className="h-4 w-4" />
                Launching...
              </>
            ) : (
              <>
                <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z" />
                </svg>
                Play
              </>
            )}
          </button>
        )}
        {isRunning && (
          <button
            onClick={() => handleAction("close")}
            disabled={actionLoading === "close"}
            className="flex items-center gap-2 rounded-lg bg-red-700 px-6 py-2.5 text-sm font-semibold text-white transition-all hover:bg-red-600 disabled:opacity-50"
          >
            {actionLoading === "close" ? (
              <>
                <Spinner className="h-4 w-4" />
                Closing...
              </>
            ) : (
              <>
                <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
                Close
              </>
            )}
          </button>
        )}
        {isInstalled && (
          <button
            onClick={() => handleAction("uninstall")}
            disabled={actionLoading === "uninstall"}
            className="rounded-lg bg-zinc-800 px-4 py-2.5 text-sm text-zinc-400 transition-all hover:bg-red-900/40 hover:text-red-300 disabled:opacity-50"
          >
            {actionLoading === "uninstall" ? "Uninstalling..." : "Uninstall"}
          </button>
        )}

        {error && (
          <span className="ml-auto text-xs text-red-400">{error}</span>
        )}
      </div>

      {/* ═══════════════ SETTINGS ─ TABS ═══════════════ */}
      <div className="border-b border-zinc-800/30 px-6">
        <div className="flex gap-1">
          {TABS.map((tab) => (
            <button
              key={tab.key}
              onClick={() => setActiveTab(tab.key)}
              className={`px-4 py-3 text-sm font-medium transition-all border-b-2 ${
                activeTab === tab.key
                  ? "border-emerald-500 text-emerald-300"
                  : "border-transparent text-zinc-500 hover:text-zinc-300"
              }`}
            >
              {tab.label}
            </button>
          ))}
        </div>
      </div>

      {/* ═══════════════ SETTINGS ─ CONTENT ═══════════════ */}
      <div className="flex-1 px-6 py-5">
        {/* Save indicator */}
        <div className="mb-4 flex items-center justify-between">
          <div />
          <div className="flex items-center gap-2">
            {saving && (
              <span className="flex items-center gap-1.5 text-xs text-zinc-500">
                <Spinner className="h-3 w-3" />
                Saving...
              </span>
            )}
            {saveMessage && (
              <span
                className={`text-xs ${
                  saveMessage.startsWith("Error") ? "text-red-400" : "text-emerald-400"
                }`}
              >
                {saveMessage}
              </span>
            )}
          </div>
        </div>

        {activeTab === "general" && (
          <GeneralTab
            settings={settings}
            wineVersions={wineVersions}
            onSave={saveSetting}
          />
        )}

        {activeTab === "advanced" && (
          <AdvancedTab
            settings={settings}
            envEntries={envEntries}
            onEnvChange={handleEnvChange}
            onAddEnv={addEnvEntry}
            onRemoveEnv={removeEnvEntry}
            onSaveEnv={saveEnvVars}
            onSave={saveSetting}
          />
        )}

        {activeTab === "compatibility" && (
          <CompatibilityTab
            settings={settings}
            onSave={saveSetting}
          />
        )}

        {activeTab === "system" && (
          <SystemTab
            settings={settings}
            onSave={saveSetting}
          />
        )}
      </div>
    </div>
  );
}

// ════════════════════════════════════════════════════════════════════════════
//  General Tab
// ════════════════════════════════════════════════════════════════════════════

function GeneralTab({
  settings,
  wineVersions,
  onSave,
}: {
  settings: GameSettingsResponse;
  wineVersions: WineVersionResponse[];
  onSave: <K extends keyof GameSettingsResponse>(key: K, value: GameSettingsResponse[K]) => void;
}) {
  return (
    <div className="max-w-lg space-y-5">
      {/* Runner selector */}
      <div>
        <label className="mb-1.5 block text-sm font-medium text-zinc-400">Runner</label>
        <select
          value={settings.runner}
          onChange={(e) => onSave("runner", e.target.value)}
          className="w-full rounded-lg border border-zinc-700 bg-zinc-800 px-3 py-2 text-sm text-zinc-200 focus:border-emerald-600 focus:outline-none"
        >
          {RUNNER_OPTIONS.map((opt) => (
            <option key={opt.value} value={opt.value}>
              {opt.label}
            </option>
          ))}
        </select>
      </div>

      {/* Wine version */}
      <div>
        <label className="mb-1.5 block text-sm font-medium text-zinc-400">Wine Version</label>
        {wineVersions.length > 0 ? (
          <select
            value={settings.wine_version ?? ""}
            onChange={(e) => onSave("wine_version", e.target.value || null)}
            className="w-full rounded-lg border border-zinc-700 bg-zinc-800 px-3 py-2 text-sm text-zinc-200 focus:border-emerald-600 focus:outline-none"
          >
            <option value="">Default (system)</option>
            {wineVersions.map((wv) => (
              <option key={wv.name} value={wv.name}>
                {wv.name}
              </option>
            ))}
          </select>
        ) : (
          <input
            type="text"
            value={settings.wine_version ?? ""}
            onChange={(e) => onSave("wine_version", e.target.value || null)}
            placeholder="e.g. wine-ge-8-26"
            className="w-full rounded-lg border border-zinc-700 bg-zinc-800 px-3 py-2 text-sm text-zinc-200 placeholder-zinc-600 focus:border-emerald-600 focus:outline-none"
          />
        )}
      </div>
    </div>
  );
}

// ════════════════════════════════════════════════════════════════════════════
//  Advanced Tab
// ════════════════════════════════════════════════════════════════════════════

function AdvancedTab({
  settings,
  envEntries,
  onEnvChange,
  onAddEnv,
  onRemoveEnv,
  onSaveEnv,
  onSave,
}: {
  settings: GameSettingsResponse;
  envEntries: Array<{ key: string; value: string }>;
  onEnvChange: (index: number, field: "key" | "value", val: string) => void;
  onAddEnv: () => void;
  onRemoveEnv: (index: number) => void;
  onSaveEnv: () => void;
  onSave: <K extends keyof GameSettingsResponse>(key: K, value: GameSettingsResponse[K]) => void;
}) {
  return (
    <div className="max-w-lg space-y-5">
      {/* Arguments */}
      <div>
        <label className="mb-1.5 block text-sm font-medium text-zinc-400">
          Game Arguments
        </label>
        <input
          type="text"
          value={settings.arguments}
          onChange={(e) => onSave("arguments", e.target.value)}
          placeholder="e.g. --opengl --width=1920"
          className="w-full rounded-lg border border-zinc-700 bg-zinc-800 px-3 py-2 text-sm text-zinc-200 placeholder-zinc-600 focus:border-emerald-600 focus:outline-none"
        />
      </div>

      {/* Wine prefix */}
      <div>
        <label className="mb-1.5 block text-sm font-medium text-zinc-400">
          Wine Prefix
        </label>
        <input
          type="text"
          value={settings.wine_prefix ?? ""}
          onChange={(e) => onSave("wine_prefix", e.target.value || null)}
          placeholder="e.g. /home/user/Games/wineprefix"
          className="w-full rounded-lg border border-zinc-700 bg-zinc-800 px-3 py-2 text-sm text-zinc-200 placeholder-zinc-600 focus:border-emerald-600 focus:outline-none"
        />
      </div>

      {/* Wine arch */}
      <div>
        <label className="mb-1.5 block text-sm font-medium text-zinc-400">Wine Architecture</label>
        <select
          value={settings.wine_arch}
          onChange={(e) => onSave("wine_arch", e.target.value)}
          className="w-full rounded-lg border border-zinc-700 bg-zinc-800 px-3 py-2 text-sm text-zinc-200 focus:border-emerald-600 focus:outline-none"
        >
          {WINE_ARCH_OPTIONS.map((opt) => (
            <option key={opt.value} value={opt.value}>
              {opt.label}
            </option>
          ))}
        </select>
      </div>

      {/* Environment variables */}
      <div>
        <div className="mb-2 flex items-center justify-between">
          <label className="text-sm font-medium text-zinc-400">Environment Variables</label>
          <div className="flex gap-2">
            <button
              onClick={onSaveEnv}
              className="rounded bg-emerald-800/50 px-2.5 py-1 text-[11px] font-medium text-emerald-300 hover:bg-emerald-700/50 transition-colors"
            >
              Save Env Vars
            </button>
            <button
              onClick={onAddEnv}
              className="rounded bg-zinc-800 px-2.5 py-1 text-[11px] text-zinc-400 hover:bg-zinc-700 transition-colors"
            >
              + Add
            </button>
          </div>
        </div>
        <div className="space-y-2">
          {envEntries.length === 0 ? (
            <p className="py-2 text-xs text-zinc-600">No environment variables set.</p>
          ) : (
            envEntries.map((entry, i) => (
              <div key={i} className="flex items-center gap-2">
                <input
                  type="text"
                  value={entry.key}
                  onChange={(e) => onEnvChange(i, "key", e.target.value)}
                  placeholder="KEY"
                  className="flex-1 rounded border border-zinc-700 bg-zinc-800 px-2 py-1.5 text-xs font-mono text-zinc-200 placeholder-zinc-600 focus:border-emerald-600 focus:outline-none"
                />
                <span className="text-zinc-600">=</span>
                <input
                  type="text"
                  value={entry.value}
                  onChange={(e) => onEnvChange(i, "value", e.target.value)}
                  placeholder="value"
                  className="flex-[2] rounded border border-zinc-700 bg-zinc-800 px-2 py-1.5 text-xs font-mono text-zinc-200 placeholder-zinc-600 focus:border-emerald-600 focus:outline-none"
                />
                <button
                  onClick={() => onRemoveEnv(i)}
                  className="shrink-0 rounded p-1 text-zinc-500 hover:text-red-400 transition-colors"
                  title="Remove"
                >
                  <svg className="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  );
}

// ════════════════════════════════════════════════════════════════════════════
//  Compatibility Tab
// ════════════════════════════════════════════════════════════════════════════

function CompatibilityTab({
  settings,
  onSave,
}: {
  settings: GameSettingsResponse;
  onSave: <K extends keyof GameSettingsResponse>(key: K, value: GameSettingsResponse[K]) => void;
}) {
  return (
    <div className="max-w-lg space-y-4">
      <Toggle
        enabled={settings.dxvk}
        onChange={(v) => onSave("dxvk", v)}
        label="DXVK (DirectX 9/10/11 → Vulkan)"
      />
      <div className="border-t border-zinc-800/50" />
      <Toggle
        enabled={settings.vkd3d}
        onChange={(v) => onSave("vkd3d", v)}
        label="VKD3D (DirectX 12 → Vulkan)"
      />
      <div className="border-t border-zinc-800/50" />
      <Toggle
        enabled={settings.fsr}
        onChange={(v) => onSave("fsr", v)}
        label="FSR (FidelityFX Super Resolution)"
      />
      {settings.fsr && (
        <div className="ml-6">
          <label className="mb-1.5 block text-xs font-medium text-zinc-500">
            FSR Quality
          </label>
          <select
            value={settings.fsr_quality}
            onChange={(e) => onSave("fsr_quality", e.target.value)}
            className="w-full rounded-lg border border-zinc-700 bg-zinc-800 px-3 py-2 text-sm text-zinc-200 focus:border-emerald-600 focus:outline-none"
          >
            {FSR_QUALITY_OPTIONS.map((opt) => (
              <option key={opt} value={opt}>
                {opt.charAt(0).toUpperCase() + opt.slice(1)}
              </option>
            ))}
          </select>
        </div>
      )}
    </div>
  );
}

// ════════════════════════════════════════════════════════════════════════════
//  System Tab
// ════════════════════════════════════════════════════════════════════════════

function SystemTab({
  settings,
  onSave,
}: {
  settings: GameSettingsResponse;
  onSave: <K extends keyof GameSettingsResponse>(key: K, value: GameSettingsResponse[K]) => void;
}) {
  return (
    <div className="max-w-lg space-y-4">
      <Toggle
        enabled={settings.game_mode}
        onChange={(v) => onSave("game_mode", v)}
        label="GameMode (Feral Interactive)"
      />
      <div className="border-t border-zinc-800/50" />
      <Toggle
        enabled={settings.mangohud}
        onChange={(v) => onSave("mangohud", v)}
        label="MangoHud (Performance Overlay)"
      />
      <div className="border-t border-zinc-800/50" />
      <Toggle
        enabled={settings.use_steam_runtime}
        onChange={(v) => onSave("use_steam_runtime", v)}
        label="Steam Runtime (Steam Linux Runtime)"
      />
      <div className="border-t border-zinc-800/50" />

      {/* Pre-launch command */}
      <div>
        <label className="mb-1.5 block text-sm font-medium text-zinc-400">
          Pre-Launch Command
        </label>
        <input
          type="text"
          value={settings.pre_launch_command}
          onChange={(e) => onSave("pre_launch_command", e.target.value)}
          placeholder="e.g. gamemoderun %command%"
          className="w-full rounded-lg border border-zinc-700 bg-zinc-800 px-3 py-2 text-sm text-zinc-200 placeholder-zinc-600 focus:border-emerald-600 focus:outline-none"
        />
      </div>

      {/* Post-exit command */}
      <div>
        <label className="mb-1.5 block text-sm font-medium text-zinc-400">
          Post-Exit Command
        </label>
        <input
          type="text"
          value={settings.post_exit_command}
          onChange={(e) => onSave("post_exit_command", e.target.value)}
          placeholder="e.g. notify-send 'Game closed'"
          className="w-full rounded-lg border border-zinc-700 bg-zinc-800 px-3 py-2 text-sm text-zinc-200 placeholder-zinc-600 focus:border-emerald-600 focus:outline-none"
        />
      </div>
    </div>
  );
}
