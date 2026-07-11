export class DiagnosticsManager {
  private isReachable = false;
  private reachabilityListeners: ((reachable: boolean) => void)[] = [];

  constructor() {
    // Listen to browser network changes
    window.addEventListener('online', () => this.checkReachability());
    window.addEventListener('offline', () => {
      this.isReachable = false;
      this.notifyListeners();
    });
  }

  public async requestPersistence(): Promise<boolean> {
    if (navigator.storage && navigator.storage.persist) {
      try {
        const persisted = await navigator.storage.persist();
        console.log(`[PWA Diagnostics] Persistent storage status: ${persisted ? 'GRANTED' : 'DENIED'}`);
        return persisted;
      } catch (err) {
        console.warn('[PWA Diagnostics] Failed to request storage persistence:', err);
      }
    }
    return false;
  }

  public isLANReachable(): boolean {
    return this.isReachable;
  }

  public onReachabilityChanged(listener: (reachable: boolean) => void) {
    this.reachabilityListeners.push(listener);
    listener(this.isReachable);
  }

  public async checkReachability(): Promise<boolean> {
    const host = localStorage.getItem('mealie_host');
    if (!host) {
      this.isReachable = false;
      this.notifyListeners();
      return false;
    }

    try {
      // Perform a lightweight fetch (cache-busted HEAD request)
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 3000);

      await fetch(`${host}/`, {
        method: 'HEAD',
        mode: 'no-cors', // Avoid CORS errors blocks reachability checks
        signal: controller.signal
      });

      clearTimeout(timeoutId);
      // Under no-cors, any successful request or response indicates reachability
      this.isReachable = true;
    } catch (err) {
      this.isReachable = false;
    }

    this.notifyListeners();
    return this.isReachable;
  }

  private notifyListeners() {
    this.reachabilityListeners.forEach((listener) => listener(this.isReachable));
  }
}

export const diagnostics = new DiagnosticsManager();
