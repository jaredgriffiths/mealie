import { diagnostics } from '../data/diagnostics';
import { recipesRepository, shoppingListsRepository } from '../data/repositories';

export async function renderSettingsView(): Promise<string> {
  const [recipeCount, shoppingListCount] = await Promise.all([
    recipesRepository.count(),
    shoppingListsRepository.count()
  ]);

  const isReachable = diagnostics.isLANReachable();
  const host = localStorage.getItem('mealie_host') || 'http://localhost:9091';

  return `
    <div style="display: flex; flex-direction: column; gap: 8px;">
      <h3 style="font-size: 0.875rem; font-weight: 700; color: var(--primary-color); text-transform: uppercase; letter-spacing: 0.05em; margin-left: 4px;">Connection Diagnostics</h3>
      <div class="card">
        <div style="display: flex; justify-content: space-between; align-items: center; font-size: 0.875rem;">
          <span>LAN Bridge Reachable:</span>
          <span id="settings-lan-status" style="font-weight: 700; color: ${isReachable ? 'var(--success-color)' : 'var(--error-color)'};">
            ${isReachable ? 'ONLINE' : 'OFFLINE (Firestore Mode)'}
          </span>
        </div>
        <div style="font-size: 0.75rem; color: var(--text-secondary); margin-top: -4px;">
          Endpoint: <span style="font-family: monospace;">${host}</span>
        </div>
        <button id="test-connection-btn" class="btn" style="width: 100%; margin-top: 4px;">Test Connection Status</button>
      </div>
    </div>

    <div style="display: flex; flex-direction: column; gap: 8px;">
      <h3 style="font-size: 0.875rem; font-weight: 700; color: var(--primary-color); text-transform: uppercase; letter-spacing: 0.05em; margin-left: 4px;">Local Cache Statistics</h3>
      <div style="display: flex; gap: 12px; width: 100%;">
        <div class="card" style="width: 50%; align-items: center; padding: 16px 8px; gap: 4px;">
          <span style="font-size: 0.875rem; font-weight: 700; color: var(--text-secondary);">Recipes</span>
          <span style="font-size: 1.5rem; font-weight: 800; color: var(--primary-color);">${recipeCount}</span>
        </div>
        <div class="card" style="width: 50%; align-items: center; padding: 16px 8px; gap: 4px;">
          <span style="font-size: 0.875rem; font-weight: 700; color: var(--text-secondary);">Lists</span>
          <span style="font-size: 1.5rem; font-weight: 800; color: var(--primary-color);">${shoppingListCount}</span>
        </div>
      </div>
    </div>

    <div class="card" style="margin-top: 8px; border-color: rgba(239, 68, 68, 0.2); gap: 16px;">
      <h3 class="card-title" style="color: var(--error-color);">Danger Zone</h3>
      <div style="display: flex; flex-direction: column; gap: 8px;">
        <button id="clear-cache-btn" class="btn" style="background: rgba(239, 68, 68, 0.1); border: 1px solid var(--error-color); color: #fca5a5; width: 100%;">Clear Local Cache</button>
        <button id="logout-btn" class="btn btn-error" style="width: 100%;">Log Out Session</button>
      </div>
    </div>
  `;
}

export function attachSettingsListeners(onRefresh: () => void) {
  // Test connection button
  const testBtn = document.getElementById('test-connection-btn') as HTMLButtonElement;
  testBtn?.addEventListener('click', async () => {
    testBtn.disabled = true;
    testBtn.textContent = 'Testing connection...';

    const reachable = await diagnostics.checkReachability();

    const statusSpan = document.getElementById('settings-lan-status') as HTMLSpanElement;
    if (statusSpan) {
      statusSpan.style.color = reachable ? 'var(--success-color)' : 'var(--error-color)';
      statusSpan.textContent = reachable ? 'ONLINE' : 'OFFLINE (Firestore Mode)';
    }

    testBtn.disabled = false;
    testBtn.textContent = 'Test Connection Status';
  });

  // Clear cache button
  document.getElementById('clear-cache-btn')?.addEventListener('click', async () => {
    if (confirm('Are you sure you want to clear the offline recipe and shopping list caches?')) {
      await Promise.all([
        recipesRepository.clear(),
        shoppingListsRepository.clear()
      ]);
      onRefresh();
    }
  });
}
