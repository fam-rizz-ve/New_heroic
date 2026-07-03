import { useState } from "react";
import { BackendStatus } from "@/components/BackendStatus";
import Dashboard from "@/pages/Dashboard";
import SettingsPage from "@/pages/SettingsPage";
import GameDetailPage from "@/pages/GameDetailPage";

function App() {
  const [page, setPage] = useState<"library" | "settings">("library");
  const [selectedGameId, setSelectedGameId] = useState<string | null>(null);

  const handleNavLibrary = () => {
    setPage("library");
    setSelectedGameId(null);
  };

  return (
    <div className="flex h-screen bg-zinc-950 text-zinc-100 overflow-hidden">
      {/* Left Sidebar — Minimal, icon-based like Heroic */}
      <aside className="flex w-16 shrink-0 flex-col items-center border-r border-zinc-800/50 bg-zinc-900/50 py-4">
        {/* App logo */}
        <button
          onClick={handleNavLibrary}
          className="mb-8 flex h-10 w-10 items-center justify-center rounded-xl bg-emerald-600 text-lg font-bold text-white"
        >
          N
        </button>

        {/* Nav items */}
        <nav className="flex flex-col items-center gap-3">
          <button
            onClick={handleNavLibrary}
            className={`flex h-10 w-10 items-center justify-center rounded-xl transition-all ${
              page === "library" && selectedGameId === null
                ? "bg-emerald-900/40 text-emerald-400 shadow-lg shadow-emerald-900/20"
                : "text-zinc-500 hover:bg-zinc-800 hover:text-zinc-300"
            }`}
            title="Library"
          >
            <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
            </svg>
          </button>

          <button
            onClick={() => { setPage("settings"); setSelectedGameId(null); }}
            className={`flex h-10 w-10 items-center justify-center rounded-xl transition-all ${
              page === "settings"
                ? "bg-emerald-900/40 text-emerald-400 shadow-lg shadow-emerald-900/20"
                : "text-zinc-500 hover:bg-zinc-800 hover:text-zinc-300"
            }`}
            title="Settings"
          >
            <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.066 2.573c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.573 1.066c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.066-2.573c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
            </svg>
          </button>
        </nav>

        {/* Spacer + version indicator */}
        <div className="mt-auto flex flex-col items-center gap-2">
          <span className="h-6 w-[1px] bg-zinc-800" />
          <span className="text-[8px] font-mono text-zinc-700">v0.1</span>
        </div>
      </aside>

      {/* Main content area */}
      <div className="flex flex-1 flex-col overflow-hidden">
        {page === "library" && selectedGameId === null && (
          <Dashboard onGameSelect={(id) => setSelectedGameId(id)} />
        )}
        {page === "library" && selectedGameId !== null && (
          <GameDetailPage
            gameId={selectedGameId}
            onBack={handleNavLibrary}
          />
        )}
        {page === "settings" && <SettingsPage />}
      </div>

      <BackendStatus />
    </div>
  );
}

export default App;
