import type { GameResponse } from "@/lib/api";

interface GameCardProps {
  game: GameResponse;
  onAction: (action: "install" | "uninstall" | "launch" | "close") => void;
  onSelect?: (gameId: string) => void;
  onContextMenu?: (gameId: string, x: number, y: number) => void;
}

export default function GameCard({ game, onAction, onSelect, onContextMenu }: GameCardProps) {
  const isInstalled = game.status === "installed";
  const isRunning = game.status === "running";
  const isInstalling = game.status === "installing";

  const storeColors: Record<string, string> = {
    epic: "bg-purple-900/60 text-purple-300",
    gog: "bg-blue-900/60 text-blue-300",
    local: "bg-zinc-800 text-zinc-400",
    steam: "bg-orange-900/60 text-orange-300",
  };

  const storeLabel =
    game.store.charAt(0).toUpperCase() + game.store.slice(1);

  const storeColorClass = storeColors[game.store] ?? "bg-zinc-800 text-zinc-400";

  return (
    <div
      className="group relative overflow-hidden rounded-xl border border-zinc-800 bg-zinc-900/60 transition-all duration-200 hover:border-emerald-700/40 hover:shadow-lg hover:shadow-emerald-900/10 hover:-translate-y-0.5 cursor-pointer"
      style={{ contentVisibility: "auto", containIntrinsicSize: "340px" }}
      onClick={() => onSelect?.(game.id)}
      onContextMenu={(e) => {
        e.preventDefault();
        onContextMenu?.(game.id, e.clientX, e.clientY);
      }}
    >
      {/* Cover art area */}
      <div className="aspect-[3/4] w-full overflow-hidden bg-gradient-to-br from-zinc-800 via-zinc-900 to-zinc-950">
        {game.cover_art_url ? (
          <img
            src={game.cover_art_url}
            alt={game.title}
            loading="lazy"
            className="h-full w-full object-cover transition-transform duration-300 group-hover:scale-105"
          />
        ) : (
          <div className="flex h-full items-center justify-center">
            <svg
              className="h-12 w-12 text-zinc-700"
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
            </svg>
          </div>
        )}

        {/* Store badge */}
        <span
          className={`absolute left-2 top-2 rounded-md px-1.5 py-0.5 text-[10px] font-semibold uppercase tracking-wider ${storeColorClass}`}
        >
          {storeLabel}
        </span>

        {/* Favorite star indicator */}
        {game.is_favorite && (
          <svg className="absolute right-2 top-2 h-5 w-5 text-amber-400 drop-shadow-lg" fill="currentColor" viewBox="0 0 24 24">
            <path d="M11.049 2.927c.3-.921 1.603-.921 1.902 0l1.519 4.674a1 1 0 00.95.69h4.915c.969 0 1.371 1.24.588 1.81l-3.976 2.888a1 1 0 00-.363 1.118l1.518 4.674c.3.922-.755 1.688-1.538 1.118l-3.976-2.888a1 1 0 00-1.176 0l-3.976 2.888c-.783.57-1.838-.197-1.538-1.118l1.518-4.674a1 1 0 00-.363-1.118l-3.976-2.888c-.784-.57-.38-1.81.588-1.81h4.914a1 1 0 00.951-.69l1.519-4.674z" />
          </svg>
        )}

        {/* Action overlay on hover — stops propagation so clicking an action
            button doesn't navigate to the game detail page */}
        <div
          className="absolute inset-0 flex items-end bg-gradient-to-t from-black/80 via-transparent to-transparent p-3 opacity-0 transition-opacity duration-200 group-hover:opacity-100"
          onClick={(e) => e.stopPropagation()}
        >
          {!isInstalled && !isRunning && !isInstalling && (
            <button
              onClick={() => onAction("install")}
              className="w-full rounded-lg bg-emerald-600 py-2 text-xs font-semibold text-white shadow-lg transition-colors hover:bg-emerald-500"
            >
              Install
            </button>
          )}
          {isInstalled && (
            <div className="flex w-full gap-2">
              <button
                onClick={() => onAction("launch")}
                className="flex-1 rounded-lg bg-emerald-600 py-2 text-xs font-semibold text-white shadow-lg transition-colors hover:bg-emerald-500"
              >
                Launch
              </button>
              <button
                onClick={() => onAction("uninstall")}
                className="rounded-lg bg-red-800/80 px-3 py-2 text-xs text-red-200 shadow-lg transition-colors hover:bg-red-700"
                title="Uninstall"
              >
                ✕
              </button>
            </div>
          )}
          {isRunning && (
            <button
              onClick={() => onAction("close")}
              className="w-full rounded-lg bg-red-700 py-2 text-xs font-semibold text-white shadow-lg transition-colors hover:bg-red-600"
            >
              Close
            </button>
          )}
          {isInstalling && (
            <div className="w-full rounded-lg bg-blue-800/60 py-2 text-center text-xs font-medium text-blue-200">
              <div className="flex items-center justify-center gap-2">
                <div className="h-3 w-3 animate-spin rounded-full border-2 border-blue-400 border-t-transparent" />
                Installing...
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Game info */}
      <div className="p-3">
        <h3 className="truncate text-sm font-medium text-zinc-200 transition-colors group-hover:text-emerald-300">
          {game.title}
        </h3>
        <p className="mt-0.5 text-xs text-zinc-500 capitalize">
          {game.status === "not_installed" && "Not installed"}
          {game.status === "installed" && "Ready to play"}
          {game.status === "running" && "Playing now"}
          {game.status === "installing" && "Installing..."}
          {game.status === "error" && "Error"}
        </p>
      </div>
    </div>
  );
}
