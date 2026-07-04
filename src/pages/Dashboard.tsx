import { useEffect, useState, useCallback, useRef, useMemo } from "react";
import { useVirtualizer } from "@tanstack/react-virtual";
import { api, type GameResponse } from "@/lib/api";
import GameCard from "@/components/GameCard";
import GameContextMenu from "@/components/GameContextMenu";
import { useColumns } from "@/hooks/useColumns";

type FilterType = "all" | "installed" | "not_installed" | "epic" | "gog" | "local" | "steam" | "favorites";

const FILTERS: { key: FilterType; label: string }[] = [
  { key: "all", label: "All" },
  { key: "installed", label: "Installed" },
  { key: "not_installed", label: "Not Installed" },
  { key: "epic", label: "Epic" },
  { key: "gog", label: "GOG" },
  { key: "local", label: "Local" },
  { key: "steam", label: "Steam" },
  { key: "favorites", label: "Favorites" },
];

interface DashboardProps {
  onGameSelect?: (gameId: string) => void;
}

export default function Dashboard({ onGameSelect }: DashboardProps) {
  const [games, setGames] = useState<GameResponse[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [search, setSearch] = useState("");
  const [activeFilter, setActiveFilter] = useState<FilterType>("all");
  const [showAddGame, setShowAddGame] = useState(false);
  const [newGameTitle, setNewGameTitle] = useState("");
  const [newGameStore, setNewGameStore] = useState("local");
  const [newGameRunner, setNewGameRunner] = useState("native");

  // Context menu
  const [contextMenu, setContextMenu] = useState<{ gameId: string; x: number; y: number } | null>(null);

  // Sync state from stores
  const [syncing, setSyncing] = useState<string | null>(null);
  const [lastSyncTimes, setLastSyncTimes] = useState<Record<string, Date | null>>({});

  // Virtual scrolling
  const scrollRef = useRef<HTMLDivElement>(null);
  const columns = useColumns(scrollRef);

  const rowCount = useMemo(
    () => Math.ceil(games.length / columns),
    [games.length, columns]
  );

  const rowVirtualizer = useVirtualizer({
    count: rowCount,
    getScrollElement: () => scrollRef.current,
    estimateSize: () => 340,
    overscan: 3,
  });

  const loadGames = useCallback(async () => {
    try {
      setLoading(true);
      // Fetch all games from the unified API
      const data = await api.listUnifiedGames();
      let filtered = data;

      // Client-side filtering
      if (activeFilter === "installed") {
        filtered = data.filter(
          (g) => g.status === "installed" || g.status === "running"
        );
      } else if (activeFilter === "not_installed") {
        filtered = data.filter((g) => g.status === "not_installed");
      } else if (activeFilter === "favorites") {
        filtered = data.filter((g) => g.is_favorite);
      } else if (activeFilter !== "all") {
        filtered = data.filter((g) => g.store === activeFilter);
      }

      if (search) {
        const q = search.toLowerCase();
        filtered = filtered.filter((g) => g.title.toLowerCase().includes(q));
      }

      setGames(filtered);
    } catch (err) {
      const msg = err instanceof Error ? err.message : "Failed to load games";
      setError(msg);
    } finally {
      setLoading(false);
    }
  }, [activeFilter, search]);

  useEffect(() => {
    loadGames();
  }, [loadGames]);

  async function handleAddGame() {
    if (!newGameTitle.trim()) return;
    try {
      await api.addGame("default", {
        title: newGameTitle,
        store: newGameStore,
        runner: newGameRunner,
      });
      setNewGameTitle("");
      setShowAddGame(false);
      await loadGames();
    } catch (err) {
      const msg = err instanceof Error ? err.message : "Failed to add game";
      setError(msg);
    }
  }

  async function handleGameAction(gameId: string, action: string) {
    try {
      if (action === "install") await api.installGame(gameId);
      else if (action === "uninstall") await api.uninstallGame(gameId);
      else if (action === "launch") await api.launchGame(gameId);
      else if (action === "close") await api.closeGame(gameId);
      await loadGames();
    } catch (err) {
      const msg = err instanceof Error ? err.message : String(err);
      setError(msg);
    }
  }

  async function handleToggleFavorite(gameId: string) {
    try {
      await api.toggleFavorite(gameId);
      await loadGames();
    } catch (err) {
      const msg = err instanceof Error ? err.message : "Failed to toggle favorite";
      setError(msg);
    }
  }

  async function handleSync(storeName: string) {
    setSyncing(storeName);
    try {
      // Start background sync
      const { task_id } = await api.startBackgroundSync(storeName);

      // Poll for completion
      let completed = false;
      let attempts = 0;
      const maxAttempts = 300;

      while (!completed && attempts < maxAttempts) {
        await new Promise(r => setTimeout(r, 2000));
        attempts++;

        const status = await api.getSyncStatus(task_id);

        if (status.status === "completed") {
          setLastSyncTimes((prev) => ({ ...prev, [storeName]: new Date() }));
          await loadGames();
          completed = true;
        } else if (status.status === "failed") {
          setError(`Sync failed: ${status.error ?? "Unknown error"}`);
          completed = true;
        }
      }

      if (!completed) {
        setError("Sync timed out after 10 minutes");
      }
    } catch (err) {
      const msg = err instanceof Error ? err.message : "Sync failed";
      setError(msg);
    } finally {
      setSyncing(null);
    }
  }

  function formatLastSync(date: Date | null): string {
    if (!date) return "";
    const diff = Date.now() - date.getTime();
    const mins = Math.floor(diff / 60000);
    if (mins < 1) return "Just now";
    if (mins === 1) return "1 min ago";
    if (mins < 60) return `${mins} min ago`;
    const hours = Math.floor(mins / 60);
    if (hours === 1) return "1 hour ago";
    return `${hours} hours ago`;
  }

  return (
    <div className="flex h-full flex-col">
      {/* Top bar: Title + Search */}
      <div className="flex items-center gap-4 border-b border-zinc-800/50 px-6 py-4">
        <div className="flex-1">
          <h1 className="text-lg font-semibold text-zinc-100">Library</h1>
          <p className="text-xs text-zinc-500">
            {games.length} game{games.length !== 1 ? "s" : ""}
          </p>
        </div>

        <div className="relative flex-1 max-w-md">
          <svg
            className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-zinc-500"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
            />
          </svg>
          <input
            type="text"
            placeholder="Search games..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full rounded-xl border border-zinc-800 bg-zinc-900 py-2 pl-10 pr-4 text-sm text-zinc-200 placeholder-zinc-600 transition-colors focus:border-emerald-700 focus:outline-none focus:ring-1 focus:ring-emerald-700/50"
          />
        </div>

        <button
          onClick={() => setShowAddGame(true)}
          className="rounded-xl bg-emerald-700 px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-emerald-600"
        >
          + Add Game
        </button>
      </div>

      {/* Filter pills */}
      <div className="flex items-center gap-2 border-b border-zinc-800/30 px-6 py-3">
        {FILTERS.map((filter) => (
          <button
            key={filter.key}
            onClick={() => setActiveFilter(filter.key)}
            className={`rounded-full px-4 py-1.5 text-xs font-medium transition-all ${
              activeFilter === filter.key
                ? "bg-emerald-700 text-white shadow-sm"
                : "bg-zinc-800/50 text-zinc-400 hover:bg-zinc-700 hover:text-zinc-200"
            }`}
          >
            {filter.label}
          </button>
        ))}

        <div className="ml-auto flex items-center gap-3">
          {lastSyncTimes["epic"] && syncing !== "epic" && (
            <span className="text-[10px] text-zinc-600">
              Epic: {formatLastSync(lastSyncTimes["epic"])}
            </span>
          )}
          <button
            onClick={() => handleSync("epic")}
            disabled={syncing === "epic"}
            className="flex items-center gap-1.5 rounded-full bg-zinc-800/50 px-3 py-1.5 text-xs text-zinc-400 hover:bg-zinc-700 hover:text-zinc-200 transition-all disabled:opacity-50"
          >
            {syncing === "epic" ? (
              <>
                <svg className="h-3 w-3 animate-spin" viewBox="0 0 24 24" fill="none">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                </svg>
                Syncing Epic...
              </>
            ) : (
              <>
                <svg className="h-3 w-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                </svg>
                Sync Epic
              </>
            )}
          </button>
          {lastSyncTimes["gog"] && syncing !== "gog" && (
            <span className="text-[10px] text-zinc-600">
              GOG: {formatLastSync(lastSyncTimes["gog"])}
            </span>
          )}
          <button
            onClick={() => handleSync("gog")}
            disabled={syncing === "gog"}
            className="flex items-center gap-1.5 rounded-full bg-zinc-800/50 px-3 py-1.5 text-xs text-zinc-400 hover:bg-zinc-700 hover:text-zinc-200 transition-all disabled:opacity-50"
          >
            {syncing === "gog" ? (
              <>
                <svg className="h-3 w-3 animate-spin" viewBox="0 0 24 24" fill="none">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                </svg>
                Syncing GOG...
              </>
            ) : (
              <>
                <svg className="h-3 w-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                </svg>
                Sync GOG
              </>
            )}
          </button>
        </div>
      </div>

      {/* Games grid */}
      <div ref={scrollRef} className="flex-1 overflow-y-auto p-6" onScroll={() => setContextMenu(null)}>
        {error && (
          <div className="mb-4 rounded-xl border border-red-800/40 bg-red-950/30 p-3 text-sm text-red-300">
            {error}
            <button
              onClick={() => setError(null)}
              className="ml-2 text-red-400 hover:text-red-200"
            >
              ✕
            </button>
          </div>
        )}

        {showAddGame && (
          <div className="mb-6 rounded-xl border border-zinc-700 bg-zinc-900 p-4">
            <div className="mb-3 text-sm font-medium text-zinc-300">
              Add New Game
            </div>
            <div className="grid grid-cols-3 gap-3">
              <input
                type="text"
                placeholder="Game title"
                value={newGameTitle}
                onChange={(e) => setNewGameTitle(e.target.value)}
                className="rounded-lg border border-zinc-700 bg-zinc-800 px-3 py-2 text-sm text-zinc-200 placeholder-zinc-500 focus:border-emerald-600 focus:outline-none"
                onKeyDown={(e) => e.key === "Enter" && handleAddGame()}
              />
              <select
                value={newGameStore}
                onChange={(e) => setNewGameStore(e.target.value)}
                className="rounded-lg border border-zinc-700 bg-zinc-800 px-3 py-2 text-sm text-zinc-200 focus:border-emerald-600 focus:outline-none"
              >
                <option value="local">Local</option>
                <option value="epic">Epic Games</option>
                <option value="gog">GOG</option>
              </select>
              <select
                value={newGameRunner}
                onChange={(e) => setNewGameRunner(e.target.value)}
                className="rounded-lg border border-zinc-700 bg-zinc-800 px-3 py-2 text-sm text-zinc-200 focus:border-emerald-600 focus:outline-none"
              >
                <option value="native">Native</option>
                <option value="wine">Wine</option>
                <option value="proton">Proton</option>
              </select>
            </div>
            <div className="mt-3 flex gap-2">
              <button
                onClick={handleAddGame}
                className="rounded-lg bg-emerald-700 px-4 py-1.5 text-sm font-medium text-white hover:bg-emerald-600"
              >
                Add
              </button>
              <button
                onClick={() => setShowAddGame(false)}
                className="rounded-lg bg-zinc-700 px-4 py-1.5 text-sm text-zinc-400 hover:text-zinc-200"
              >
                Cancel
              </button>
            </div>
          </div>
        )}

        {loading ? (
          <div className="flex items-center justify-center py-20">
            <div className="h-8 w-8 animate-spin rounded-full border-2 border-emerald-500 border-t-transparent" />
          </div>
        ) : games.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-20 text-zinc-600">
            <svg
              className="mb-4 h-16 w-16"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={1}
                d="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z"
              />
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={1}
                d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
              />
            </svg>
            <p className="text-lg font-medium">No games yet</p>
            <p className="mt-1 text-sm text-zinc-500">
              Add a game or sync your store accounts
            </p>
            <div className="mt-4 flex gap-3">
              <button
                onClick={() => setShowAddGame(true)}
                className="rounded-lg bg-emerald-700 px-4 py-2 text-sm font-medium text-white hover:bg-emerald-600"
              >
                + Add Game
              </button>
              <button
                onClick={() => handleSync("epic")}
                className="rounded-lg bg-zinc-800 px-4 py-2 text-sm text-zinc-300 hover:bg-zinc-700"
              >
                Sync Epic
              </button>
            </div>
          </div>
        ) : (
          <div
            style={{
              height: `${rowVirtualizer.getTotalSize()}px`,
              position: "relative",
            }}
          >
            {rowVirtualizer.getVirtualItems().map((virtualRow) => {
              const startIdx = virtualRow.index * columns;
              const rowItems = games.slice(startIdx, startIdx + columns);
              return (
                <div
                  key={virtualRow.key}
                  style={{
                    position: "absolute",
                    top: 0,
                    left: 0,
                    width: "100%",
                    transform: `translateY(${virtualRow.start}px)`,
                  }}
                  className="flex gap-4"
                >
                  {rowItems.map((game) => (
                    <div
                      key={game.id}
                      className="flex-1 min-w-0"
                      style={{ maxWidth: `calc(${100 / columns}% - ${(columns - 1) * 16 / columns}px)` }}
                    >
                      <GameCard
                        game={game}
                        onAction={(action) => handleGameAction(game.id, action)}
                        onSelect={onGameSelect}
                        onContextMenu={(gameId, x, y) => setContextMenu({ gameId, x, y })}
                      />
                    </div>
                  ))}
                </div>
              );
            })}
          </div>
        )}

        {contextMenu && (() => {
          const game = games.find(g => g.id === contextMenu.gameId);
          if (!game) return null;
          return (
            <GameContextMenu
              game={game}
              x={contextMenu.x}
              y={contextMenu.y}
              onClose={() => setContextMenu(null)}
              onPlay={(id) => { setContextMenu(null); handleGameAction(id, "launch"); }}
              onInstall={(id) => { setContextMenu(null); handleGameAction(id, "install"); }}
              onSettings={(id) => { setContextMenu(null); onGameSelect?.(id); }}
              onToggleFavorite={(id) => { setContextMenu(null); handleToggleFavorite(id); }}
              onRemove={(id) => { setContextMenu(null); handleGameAction(id, "uninstall"); }}
              onOpenFolder={(id) => {
                setContextMenu(null);
                api.openGameFolder(id).catch((err) => {
                  const msg = err instanceof Error ? err.message : "Failed to open folder";
                  setError(msg);
                });
              }}
            />
          );
        })()}
      </div>
    </div>
  );
}
