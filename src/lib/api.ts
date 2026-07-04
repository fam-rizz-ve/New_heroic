/// API client for the New Heroic backend.

const BACKEND_URL = import.meta.env.VITE_BACKEND_URL ?? "http://localhost:1430";

// === Types ===

export interface HealthResponse {
  status: string;
  version: string;
  app_name: string;
}

export interface GameResponse {
  id: string;
  title: string;
  store: string;
  runner: string;
  status: string;
  description: string;
  cover_art_url: string;
  install_path: string | null;
  executable_path: string | null;
  last_played: string | null;
  total_play_time_seconds: number;
  is_favorite: boolean;
  created_at: string;
  updated_at: string;
}

export interface LibraryResponse {
  id: string;
  name: string;
  store_source: string;
  game_count: number;
  created_at: string;
  updated_at: string;
}

export interface GameCreate {
  title: string;
  store: string;
  runner: string;
  description?: string;
  cover_art_url?: string;
}

export interface LibraryCreate {
  name: string;
  store_source: string;
}

export interface StoreInfo {
  name: string;
  display_name: string;
}

export interface StoreGameSchema {
  store_id: string;
  title: string;
  description: string;
  cover_art_url: string;
  developer: string;
  publisher: string;
  release_date: string | null;
  genres: string[];
}

export interface RunnerInfo {
  name: string;
  display_name: string;
  version: string;
  path: string | null;
  is_installed: boolean;
  config: Record<string, unknown>;
  error?: string;
}

export interface InstallerInfo {
  name: string;
  game_slug: string;
  version: string;
  runner: string;
  year: string;
  description: string;
  steps: number;
}

export interface ApiError {
  message: string;
  status?: number;
}

export interface WineVersionResponse {
  name: string;
  version: string;
  source: string;
  url: string | null;
  filename: string | null;
  release_date: string | null;
  is_installed: boolean;
  install_path: string | null;
}

export interface GameSettingsResponse {
  game_id: string;
  runner: string;
  wine_version: string | null;
  wine_prefix: string | null;
  wine_arch: string;
  arguments: string;
  env_vars: Record<string, string>;
  dxvk: boolean;
  vkd3d: boolean;
  fsr: boolean;
  fsr_quality: string;
  use_steam_runtime: boolean;
  game_mode: boolean;
  mangohud: boolean;
  pre_launch_command: string;
  post_exit_command: string;
}

export interface StoreAuthUrlResponse {
  auth_url: string;
  instructions: string;
  store_name: string;
}

export interface StoreStatusResponse {
  name: string;
  display_name: string;
  is_authenticated: boolean;
  is_installed: boolean;
}

export interface WineProgressResponse {
  percentage: number;
  downloaded_mb: number;
  total_mb: number;
  speed_mbps: number;
}

// === API Client ===

class ApiClient {
  private baseUrl: string;

  constructor(baseUrl: string = BACKEND_URL) {
    this.baseUrl = baseUrl;
  }

  private async request<T>(path: string, options?: RequestInit): Promise<T> {
    const response = await fetch(`${this.baseUrl}${path}`, {
      headers: { "Content-Type": "application/json" },
      ...options,
    });

    if (!response.ok) {
      let detail = `HTTP ${response.status}: ${response.statusText}`;
      try {
        const body = await response.json();
        if (body?.detail) detail = body.detail;
      } catch {
        /* ignore parse failures */
      }
      const error: ApiError = { message: detail, status: response.status };
      throw error;
    }

    return response.json() as Promise<T>;
  }

  // Health
  async health(): Promise<HealthResponse> {
    return this.request<HealthResponse>("/api/health");
  }

  // Libraries
  async listLibraries(): Promise<LibraryResponse[]> {
    return this.request<LibraryResponse[]>("/api/libraries");
  }

  async createLibrary(data: LibraryCreate): Promise<LibraryResponse> {
    return this.request<LibraryResponse>("/api/libraries", {
      method: "POST",
      body: JSON.stringify(data),
    });
  }

  // Unified library (Heroic-style)
  async listUnifiedGames(
    params?: { store?: string; status?: string; search?: string }
  ): Promise<GameResponse[]> {
    const query = new URLSearchParams();
    if (params?.store) query.set("store", params.store);
    if (params?.status) query.set("status", params.status);
    if (params?.search) query.set("search", params.search);
    const qs = query.toString();
    return this.request<GameResponse[]>(
      `/api/library/games${qs ? `?${qs}` : ""}`
    );
  }

  // Games (supports both unified and per-library)
  async listGames(libraryId: string): Promise<GameResponse[]> {
    if (libraryId === "all" || libraryId === "default") {
      return this.request<GameResponse[]>("/api/library/games");
    }
    return this.request<GameResponse[]>(`/api/libraries/${libraryId}/games`);
  }

  async addGame(libraryId: string, data: GameCreate): Promise<GameResponse> {
    if (libraryId === "default") {
      return this.request<GameResponse>("/api/library/games", {
        method: "POST",
        body: JSON.stringify(data),
      });
    }
    return this.request<GameResponse>(`/api/libraries/${libraryId}/games`, {
      method: "POST",
      body: JSON.stringify(data),
    });
  }

  async getGame(gameId: string): Promise<GameResponse> {
    return this.request<GameResponse>(`/api/library/games/${gameId}`);
  }

  async installGame(gameId: string): Promise<{ message: string; game: GameResponse }> {
    return this.request(`/api/library/games/${gameId}/install`, { method: "POST" });
  }

  async uninstallGame(gameId: string): Promise<{ message: string; game: GameResponse }> {
    return this.request(`/api/library/games/${gameId}/uninstall`, { method: "POST" });
  }

  async launchGame(gameId: string): Promise<{ message: string; game: GameResponse }> {
    return this.request(`/api/library/games/${gameId}/launch`, { method: "POST" });
  }

  async closeGame(gameId: string): Promise<{ message: string; game: GameResponse }> {
    return this.request(`/api/library/games/${gameId}/close`, { method: "POST" });
  }

  async toggleFavorite(gameId: string): Promise<GameResponse> {
    return this.request<GameResponse>(`/api/library/games/${gameId}/favorite`, { method: "POST" });
  }

  // Stores
  async listStores(): Promise<StoreInfo[]> {
    return this.request<StoreInfo[]>("/api/stores");
  }

  async listStoreGames(storeName: string): Promise<StoreGameSchema[]> {
    return this.request<StoreGameSchema[]>(`/api/stores/${storeName}/games`);
  }

  // Store auth
  async getStoreAuthUrl(storeName: string): Promise<StoreAuthUrlResponse> {
    return this.request<StoreAuthUrlResponse>(`/api/stores/${storeName}/auth-url`);
  }

  async getStoreStatus(storeName: string): Promise<StoreStatusResponse> {
    return this.request<StoreStatusResponse>(`/api/stores/${storeName}/status`);
  }

  async connectStore(storeName: string, code: string): Promise<{ message: string }> {
    return this.request(`/api/stores/${storeName}/auth`, {
      method: "POST",
      body: JSON.stringify({ code }),
    });
  }

  async browserAuth(storeName: string): Promise<{ message: string }> {
    return this.request(`/api/stores/${storeName}/auth/browser`, {
      method: "POST",
    });
  }

  async syncStore(storeName: string): Promise<{ message: string }> {
    return this.request(`/api/stores/${storeName}/sync`, { method: "POST" });
  }

  async startBackgroundSync(storeName: string): Promise<{ task_id: string }> {
    return this.request(`/api/sync/${storeName}`, { method: "POST" });
  }

  async getSyncStatus(taskId: string): Promise<{
    status: string;
    store: string;
    progress?: { current?: number; total?: number };
    result?: { imported?: number; errors?: string[]; total?: number };
    error?: string;
  }> {
    return this.request(`/api/sync/${taskId}`);
  }

  // Runners
  async listRunners(): Promise<RunnerInfo[]> {
    return this.request<RunnerInfo[]>("/api/runners");
  }

  async detectRunners(): Promise<RunnerInfo[]> {
    return this.request<RunnerInfo[]>("/api/runners/detect");
  }

  // Installer
  async parseInstaller(yaml: string): Promise<InstallerInfo> {
    return this.request<InstallerInfo>("/api/installer/parse", {
      method: "POST",
      body: JSON.stringify({ manifest_yaml: yaml, game_dir: "/tmp" }),
    });
  }

  // Wine Manager
  async listAvailableWineVersions(source?: string): Promise<WineVersionResponse[]> {
    const qs = source ? `?source=${source}` : "";
    return this.request<WineVersionResponse[]>(`/api/wine/versions${qs}`);
  }

  async listInstalledWineVersions(): Promise<WineVersionResponse[]> {
    return this.request<WineVersionResponse[]>("/api/wine/installed");
  }

  async installWineVersion(versionName: string, versionUrl: string): Promise<{ path: string }> {
    return this.request("/api/wine/install", {
      method: "POST",
      body: JSON.stringify({ version_name: versionName, version_url: versionUrl }),
    });
  }

  async getWineDownloadProgress(versionName: string): Promise<WineProgressResponse> {
    return this.request<WineProgressResponse>(`/api/wine/downloads/${versionName}`);
  }

  async deleteWineVersion(versionName: string): Promise<{ status: string }> {
    return this.request(`/api/wine/versions/${encodeURIComponent(versionName)}`, { method: "DELETE" });
  }

  // Per-Game Settings
  async getGameSettings(gameId: string): Promise<GameSettingsResponse> {
    return this.request<GameSettingsResponse>(`/api/games/${gameId}/settings`);
  }

  async updateGameSettings(gameId: string, settings: Partial<GameSettingsResponse>): Promise<GameSettingsResponse> {
    return this.request<GameSettingsResponse>(`/api/games/${gameId}/settings`, {
      method: "PUT",
      body: JSON.stringify(settings),
    });
  }

  // Open Game Folder
  async openGameFolder(gameId: string): Promise<{ status: string; path: string }> {
    return this.request(`/api/library/games/${gameId}/open-folder`, { method: "POST" });
  }

  // Cover Art
  async refreshAllCovers(): Promise<{ refreshed: number; failed: number; total_checked: number }> {
    return this.request("/api/covers/refresh-all", { method: "POST" });
  }

  async refreshGameCover(gameId: string): Promise<{ game_id: string; title: string; cover_art_url: string | null; updated: boolean }> {
    return this.request(`/api/covers/games/${gameId}/refresh`, { method: "POST" });
  }
}

export const api = new ApiClient();
