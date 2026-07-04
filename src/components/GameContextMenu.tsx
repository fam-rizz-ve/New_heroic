import { useEffect, useRef } from "react";
import type { GameResponse } from "@/lib/api";

interface GameContextMenuProps {
  game: GameResponse;
  x: number;
  y: number;
  onClose: () => void;
  onPlay: (gameId: string) => void;
  onInstall: (gameId: string) => void;
  onSettings: (gameId: string) => void;
  onRemove: (gameId: string) => void;
  onToggleFavorite: (gameId: string) => void;
  onOpenFolder: (gameId: string) => void;
}

function stopPropagation(e: React.MouseEvent) {
  e.stopPropagation();
}

export default function GameContextMenu({
  game,
  x,
  y,
  onClose,
  onPlay,
  onInstall,
  onSettings,
  onRemove,
  onToggleFavorite,
  onOpenFolder,
}: GameContextMenuProps) {
  const menuRef = useRef<HTMLDivElement>(null);

  const isInstalled = game.status === "installed";
  const isRunning = game.status === "running";
  const isInstalling = game.status === "installing";
  const isNotInstalled = game.status === "not_installed" || game.status === "error";

  useEffect(() => {
    // Close on click outside
    const handleClickOutside = (e: MouseEvent) => {
      if (menuRef.current && !menuRef.current.contains(e.target as Node)) {
        onClose();
      }
    };

    // Close on Escape key
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape") {
        onClose();
      }
    };

    // Use a small delay to avoid the same click that opened the menu from closing it
    const timeoutId = setTimeout(() => {
      document.addEventListener("mousedown", handleClickOutside, { capture: true });
      document.addEventListener("keydown", handleKeyDown);
    }, 0);

    return () => {
      clearTimeout(timeoutId);
      document.removeEventListener("mousedown", handleClickOutside, { capture: true });
      document.removeEventListener("keydown", handleKeyDown);
    };
  }, [onClose]);

  return (
    <div
      ref={menuRef}
      className="fixed z-50 animate-fadeIn"
      style={{ left: x, top: y }}
      onMouseDown={stopPropagation}
      onClick={stopPropagation}
      onContextMenu={(e) => e.preventDefault()}
    >
      <div className="min-w-[200px] rounded-xl border border-zinc-700/60 bg-zinc-900 py-1 shadow-2xl shadow-black/50">
        {/* Primary action — Install/Play/Resume based on status */}
        {isNotInstalled && !isInstalling && (
          <button
            onClick={() => onInstall(game.id)}
            className="flex w-full items-center gap-3 px-3 py-2.5 text-sm text-zinc-300 transition-colors hover:bg-zinc-800"
          >
            <svg className="h-4 w-4 text-emerald-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
            </svg>
            Install
          </button>
        )}
        {isInstalled && !isRunning && (
          <button
            onClick={() => onPlay(game.id)}
            className="flex w-full items-center gap-3 px-3 py-2.5 text-sm text-zinc-300 transition-colors hover:bg-zinc-800"
          >
            <svg className="h-4 w-4 text-emerald-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z" />
            </svg>
            Play
          </button>
        )}
        {isRunning && (
          <button
            onClick={() => onPlay(game.id)}
            className="flex w-full items-center gap-3 px-3 py-2.5 text-sm text-zinc-300 transition-colors hover:bg-zinc-800"
          >
            <svg className="h-4 w-4 text-emerald-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v16h16V4H4z" />
            </svg>
            Resume
          </button>
        )}
        {isInstalling && (
          <div className="flex items-center gap-3 px-3 py-2.5 text-sm text-zinc-500 opacity-50">
            <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            Installing...
          </div>
        )}

        {/* Separator */}
        <div className="mx-2 my-1 border-t border-zinc-700/40" />

        {/* Settings */}
        <button
          onClick={() => onSettings(game.id)}
          className="flex w-full items-center gap-3 px-3 py-2.5 text-sm text-zinc-300 transition-colors hover:bg-zinc-800"
        >
          <svg className="h-4 w-4 text-zinc-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.066 2.573c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.573 1.066c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.066-2.573c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
          </svg>
          Settings
        </button>

        {/* Add/Remove Favorites */}
        {game.is_favorite ? (
          <button
            onClick={() => onToggleFavorite(game.id)}
            className="flex w-full items-center gap-3 px-3 py-2.5 text-sm text-amber-400 transition-colors hover:bg-zinc-800"
          >
            <svg className="h-4 w-4" fill="currentColor" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11.049 2.927c.3-.921 1.603-.921 1.902 0l1.519 4.674a1 1 0 00.95.69h4.915c.969 0 1.371 1.24.588 1.81l-3.976 2.888a1 1 0 00-.363 1.118l1.518 4.674c.3.922-.755 1.688-1.538 1.118l-3.976-2.888a1 1 0 00-1.176 0l-3.976 2.888c-.783.57-1.838-.197-1.538-1.118l1.518-4.674a1 1 0 00-.363-1.118l-3.976-2.888c-.784-.57-.38-1.81.588-1.81h4.914a1 1 0 00.951-.69l1.519-4.674z" />
            </svg>
            Remove from Favorites
          </button>
        ) : (
          <button
            onClick={() => onToggleFavorite(game.id)}
            className="flex w-full items-center gap-3 px-3 py-2.5 text-sm text-zinc-300 transition-colors hover:bg-zinc-800"
          >
            <svg className="h-4 w-4 text-amber-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11.049 2.927c.3-.921 1.603-.921 1.902 0l1.519 4.674a1 1 0 00.95.69h4.915c.969 0 1.371 1.24.588 1.81l-3.976 2.888a1 1 0 00-.363 1.118l1.518 4.674c.3.922-.755 1.688-1.538 1.118l-3.976-2.888a1 1 0 00-1.176 0l-3.976 2.888c-.783.57-1.838-.197-1.538-1.118l1.518-4.674a1 1 0 00-.363-1.118l-3.976-2.888c-.784-.57-.38-1.81.588-1.81h4.914a1 1 0 00.951-.69l1.519-4.674z" />
            </svg>
            Add to Favorites
          </button>
        )}

        {/* Separator */}
        <div className="mx-2 my-1 border-t border-zinc-700/40" />

        {/* Open Game Folder — only if installed */}
        {game.install_path && (
          <>
            <button
              onClick={() => onOpenFolder(game.id)}
              className="flex w-full items-center gap-3 px-3 py-2.5 text-sm text-zinc-300 transition-colors hover:bg-zinc-800"
            >
              <svg className="h-4 w-4 text-zinc-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-6l-2-2H5a2 2 0 00-2 2z" />
              </svg>
              Open Game Folder
            </button>
            <div className="mx-2 my-1 border-t border-zinc-700/40" />
          </>
        )}

        {/* View on SteamGridDB */}
        <a
          href={`https://www.steamgriddb.com/search/grids?term=${encodeURIComponent(game.title)}`}
          target="_blank"
          rel="noopener noreferrer"
          onClick={onClose}
          className="flex w-full items-center gap-3 px-3 py-2.5 text-sm text-zinc-300 transition-colors hover:bg-zinc-800"
        >
          <svg className="h-4 w-4 text-zinc-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
          </svg>
          View on SteamGridDB
        </a>

        {/* Separator */}
        <div className="mx-2 my-1 border-t border-zinc-700/40" />

        {/* Remove / Uninstall */}
        <button
          onClick={() => onRemove(game.id)}
          className="flex w-full items-center gap-3 px-3 py-2.5 text-sm text-red-400 transition-colors hover:bg-zinc-800"
        >
          <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
          </svg>
          {game.status === "installed" ? "Uninstall" : "Remove from Library"}
        </button>
      </div>
    </div>
  );
}
