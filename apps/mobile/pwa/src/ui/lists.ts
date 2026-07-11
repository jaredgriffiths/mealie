import { shoppingListsRepository } from '../data/repositories';
import { syncEngine } from '../data/sync';

let selectedListId: string | null = null;
let syncError: string | null = null;

export async function renderListsView(): Promise<string> {
  if (selectedListId) {
    return renderListDetailView(selectedListId);
  }

  const lists = await shoppingListsRepository.getAll();

  const headerHtml = `
    <div style="display: flex; justify-content: space-between; align-items: center; width: 100%;">
      <h2 style="font-size: 1.25rem; font-weight: 800;">Shopping Lists</h2>
      <button id="lists-sync-btn" class="btn" style="padding: 8px 12px; font-size: 0.875rem;">
        Sync Lists
      </button>
    </div>
  `;

  if (lists.length === 0) {
    return `
      ${headerHtml}
      <div class="card" style="text-align: center; padding: 32px 16px;">
        <p style="color: var(--text-secondary); margin-bottom: 12px;">No shopping lists cached.</p>
        <button id="lists-sync-empty-btn" class="btn">Sync from Mealie</button>
      </div>
    `;
  }

  return `
    ${headerHtml}
    <div style="display: flex; flex-direction: column; gap: 12px;">
      ${lists.map(list => {
        const items = list.items || [];
        const totalItems = items.length;
        const checkedItems = items.filter(i => i.checked).length;
        const progressPercent = totalItems > 0 ? Math.round((checkedItems / totalItems) * 100) : 0;

        return `
          <div class="card list-item-card" data-id="${list.id}" style="cursor: pointer; gap: 8px;">
            <div style="display: flex; justify-content: space-between; align-items: center;">
              <h3 style="font-size: 1rem; font-weight: 700; color: var(--text-color);">${list.name}</h3>
              <span style="font-size: 0.875rem; color: var(--primary-color); font-weight: 600;">${progressPercent}%</span>
            </div>
            <div style="display: flex; justify-content: space-between; font-size: 0.825rem; color: var(--text-secondary);">
              <span>${checkedItems}/${totalItems} Items Checked</span>
              <span>Group: ${list.group || 'Default'}</span>
            </div>
            <div style="width: 100%; height: 6px; background: var(--surface-variant); border-radius: 3px; overflow: hidden;">
              <div style="width: ${progressPercent}%; height: 100%; background: var(--primary-color); border-radius: 3px; transition: width 0.3s ease;"></div>
            </div>
          </div>
        `;
      }).join('')}
    </div>
  `;
}

async function renderListDetailView(id: string): Promise<string> {
  const list = await shoppingListsRepository.get(id);
  if (!list) {
    selectedListId = null;
    return 'List not found';
  }

  const items = list.items || [];
  const totalItems = items.length;
  const checkedItems = items.filter(i => i.checked).length;
  const progressPercent = totalItems > 0 ? Math.round((checkedItems / totalItems) * 100) : 0;

  const errorHtml = syncError ? `
    <div class="error-alert" style="margin-bottom: 12px; display: flex; justify-content: space-between; align-items: center;">
      <span>⚠️ Sync Error: ${syncError}</span>
      <button id="clear-sync-error" style="background:none; border:none; color:inherit; cursor:pointer; font-weight:700;">×</button>
    </div>
  ` : '';

  return `
    <div style="display: flex; flex-direction: column; gap: 16px;">
      <!-- Back Button -->
      <button id="list-back-btn" class="btn" style="background: var(--surface-color); border: 1px solid var(--border-color); align-self: flex-start; padding: 8px 12px; font-size: 0.875rem;">
        ← Back to Lists
      </button>

      ${errorHtml}

      <!-- Progress Header -->
      <div class="card" style="gap: 8px; padding: 16px;">
        <div style="display: flex; justify-content: space-between; align-items: center;">
          <h2 style="font-size: 1.25rem; font-weight: 800;">${list.name}</h2>
          <span id="detail-progress-percent" style="font-weight: 800; color: var(--primary-color); font-size: 1.125rem;">${progressPercent}%</span>
        </div>
        <div style="width: 100%; height: 8px; background: var(--surface-variant); border-radius: 4px; overflow: hidden; margin-top: 4px;">
          <div id="detail-progress-bar" style="width: ${progressPercent}%; height: 100%; background: var(--primary-color); border-radius: 4px; transition: width 0.3s ease;"></div>
        </div>
        <div style="font-size: 0.75rem; color: var(--text-secondary); text-align: right; margin-top: 2px;">
          <span id="detail-checked-count">${checkedItems}</span> of ${totalItems} items completed
        </div>
      </div>

      <!-- Checklist Items -->
      <div class="card" style="gap: 4px; padding: 12px 16px;">
        ${items.length === 0 ? `
          <p style="color: var(--text-secondary); font-size: 0.875rem; text-align: center; padding: 16px 0;">No items on this list.</p>
        ` : items.map(item => `
          <label style="display: flex; align-items: center; gap: 12px; padding: 12px 0; border-bottom: 1px solid rgba(148, 163, 184, 0.05); cursor: pointer;">
            <input type="checkbox" class="list-item-checkbox" data-item-id="${item.id}" ${item.checked ? 'checked' : ''} style="width: 18px; height: 18px; accent-color: var(--primary-color); cursor: pointer;" />
            <span style="font-size: 0.95rem; color: ${item.checked ? 'var(--text-secondary)' : 'var(--text-color)'}; text-decoration: ${item.checked ? 'line-through' : 'none'}; transition: color 0.2s, text-decoration 0.2s;">
              ${item.title}
            </span>
          </label>
        `).join('')}
      </div>
    </div>
  `;
}

export function attachListsListeners(onRefresh: () => void) {
  // Back button
  document.getElementById('list-back-btn')?.addEventListener('click', () => {
    selectedListId = null;
    syncError = null;
    onRefresh();
  });

  // Clear sync error
  document.getElementById('clear-sync-error')?.addEventListener('click', () => {
    syncError = null;
    onRefresh();
  });

  // Click shopping list item card
  document.querySelectorAll('.list-item-card').forEach((card) => {
    card.addEventListener('click', () => {
      selectedListId = card.getAttribute('data-id');
      onRefresh();
    });
  });

  // Item checkboxes (Optimistic update + sync outbox trigger)
  document.querySelectorAll('.list-item-checkbox').forEach((checkbox) => {
    checkbox.addEventListener('change', async (e) => {
      if (!selectedListId) return;

      const target = e.target as HTMLInputElement;
      const itemId = target.getAttribute('data-item-id')!;
      const checked = target.checked;

      // 1. Fetch current list
      const list = await shoppingListsRepository.get(selectedListId);
      if (!list) return;

      // Save previous state for rollback
      const previousItems = JSON.parse(JSON.stringify(list.items));

      // 2. Perform Optimistic Update locally
      list.items = list.items.map(item => {
        if (item.id === itemId) {
          return { ...item, checked };
        }
        return item;
      });

      // Write instantly to IndexedDB cache
      await shoppingListsRepository.save(list);

      // Instantly update UI progress indicator (safe/fast visual response)
      const total = list.items.length;
      const checkedCount = list.items.filter(i => i.checked).length;
      const newPercent = total > 0 ? Math.round((checkedCount / total) * 100) : 0;

      const progressSpan = document.getElementById('detail-progress-percent');
      const progressBar = document.getElementById('detail-progress-bar');
      const checkedSpan = document.getElementById('detail-checked-count');

      if (progressSpan) progressSpan.textContent = `${newPercent}%`;
      if (progressBar) (progressBar as HTMLElement).style.width = `${newPercent}%`;
      if (checkedSpan) checkedSpan.textContent = `${checkedCount}`;

      // Cross out text styles
      const labelText = target.nextElementSibling as HTMLSpanElement;
      if (labelText) {
        labelText.style.color = checked ? 'var(--text-secondary)' : 'var(--text-color)';
        labelText.style.textDecoration = checked ? 'line-through' : 'none';
      }

      // 3. Dispatch Network Sync outbox mutation
      const syncResult = await syncEngine.updateShoppingListRemote(list);
      if (syncResult.isFailure) {
        // Rollback on failure
        list.items = previousItems;
        await shoppingListsRepository.save(list);
        syncError = syncResult.exceptionOrNull()?.message || 'Failed to update remote list';
        onRefresh(); // Trigger full refresh to restore checkbox checked states
      } else {
        syncError = null;
      }
    });
  });

  // Sync button handlers
  const handleSync = async (btn: HTMLButtonElement) => {
    btn.disabled = true;
    const oldHtml = btn.innerHTML;
    btn.textContent = 'Syncing...';

    const success = await syncEngine.syncShoppingLists();
    if (success) {
      alert('Lists synced successfully!');
    } else {
      alert('Sync failed. Please check connection diagnostics.');
    }

    btn.disabled = false;
    btn.innerHTML = oldHtml;
    onRefresh();
  };

  const syncBtn = document.getElementById('lists-sync-btn') as HTMLButtonElement;
  syncBtn?.addEventListener('click', () => handleSync(syncBtn));

  const emptySyncBtn = document.getElementById('lists-sync-empty-btn') as HTMLButtonElement;
  emptySyncBtn?.addEventListener('click', () => handleSync(emptySyncBtn));
}

// Reset selection on tab changes
export function resetListsSelection() {
  selectedListId = null;
  syncError = null;
}
