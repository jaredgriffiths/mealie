import { recipesRepository, shoppingListsRepository } from '../data/repositories';
import { router } from '../router';

export async function renderDashboardView(): Promise<string> {
  const [recipeCount, recipes, shoppingLists] = await Promise.all([
    recipesRepository.count(),
    recipesRepository.getAll(),
    shoppingListsRepository.getAll()
  ]);

  // Today's Meal Plan (N/A) Carousel
  const mealPlanHtml = `
    <div style="display: flex; flex-direction: column; gap: 8px;">
      <h3 style="font-size: 1rem; font-weight: 700; margin-left: 4px;">Meal Plan (Today)</h3>
      <div style="display: flex; gap: 12px; overflow-x: auto; padding: 4px; -webkit-overflow-scrolling: touch; scrollbar-width: none;">
        ${['Breakfast', 'Lunch', 'Dinner'].map(mealType => `
          <div class="card" style="min-width: 200px; max-width: 200px; flex-shrink: 0; flex-direction: row; align-items: center; gap: 12px; padding: 12px; height: 80px;">
            <div style="width: 36px; height: 36px; border-radius: 8px; background: var(--primary-container); display: flex; align-items: center; justify-content: center; color: var(--primary-color);">
              <svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 2v20M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"/></svg>
            </div>
            <div>
              <div style="font-size: 0.75rem; font-weight: 700; color: var(--primary-color);">${mealType}:</div>
              <div style="font-size: 0.875rem; font-weight: 700; color: var(--text-color);">N/A</div>
              <div style="font-size: 0.75rem; color: var(--text-secondary);">⏰ N/A</div>
            </div>
          </div>
        `).join('')}
      </div>
    </div>
  `;

  // Top 3 Recipes Section
  const topRecipes = recipes.slice(0, 3);
  const recipesCardHtml = `
    <div class="card" id="recipes-dashboard-card" style="cursor: pointer;">
      <div style="display: flex; justify-content: space-between; align-items: center;">
        <h3 class="card-title">Browse Recipes</h3>
        <span style="font-size: 0.875rem; color: var(--primary-color); font-weight: 600;">${recipeCount} Total</span>
      </div>
      
      ${topRecipes.length === 0 ? `
        <p style="font-size: 0.875rem; color: var(--text-secondary);">No recipes cached yet. Tap here to view the recipes catalog.</p>
      ` : `
        <div style="display: flex; flex-direction: column; gap: 8px;">
          ${topRecipes.map(recipe => `
            <div style="display: flex; justify-content: space-between; align-items: center; padding: 8px 0; border-bottom: 1px solid rgba(148, 163, 184, 0.1);">
              <div>
                <div style="font-size: 0.875rem; font-weight: 600;">${recipe.name}</div>
                <div style="font-size: 0.75rem; color: var(--text-secondary);">${recipe.description || 'No description available'}</div>
              </div>
              <span style="font-size: 0.75rem; color: var(--text-secondary);">⏰ ${recipe.totalTime || 'N/A'}</span>
            </div>
          `).join('')}
        </div>
      `}
    </div>
  `;

  // Active Lists Progress Card
  const activeList = shoppingLists[0];
  let listsCardHtml = '';

  if (!activeList) {
    listsCardHtml = `
      <div class="card" id="lists-dashboard-card" style="cursor: pointer;">
        <h3 class="card-title">Active Lists</h3>
        <p style="font-size: 0.875rem; color: var(--text-secondary);">No active shopping lists found. Tap here to create or load lists.</p>
      </div>
    `;
  } else {
    const items = activeList.items || [];
    const totalItems = items.length;
    const checkedItems = items.filter(i => i.checked).length;
    const progressPercent = totalItems > 0 ? Math.round((checkedItems / totalItems) * 100) : 0;

    listsCardHtml = `
      <div class="card" id="lists-dashboard-card" style="cursor: pointer;">
        <div style="display: flex; justify-content: space-between; align-items: center;">
          <h3 class="card-title">${activeList.name}</h3>
          <span style="font-size: 0.875rem; color: var(--primary-color); font-weight: 600;">${progressPercent}%</span>
        </div>
        <div style="display: flex; justify-content: space-between; font-size: 0.875rem; color: var(--text-secondary);">
          <span>Groceries</span>
          <span>${checkedItems}/${totalItems} Items Checked</span>
        </div>
        <!-- Progress Bar -->
        <div style="width: 100%; height: 8px; background: var(--surface-variant); border-radius: 4px; overflow: hidden; margin-top: 4px;">
          <div style="width: ${progressPercent}%; height: 100%; background: var(--primary-color); border-radius: 4px; transition: width 0.3s ease;"></div>
        </div>
      </div>
    `;
  }

  // Setup/Settings shortcut Card
  const settingsShortcutHtml = `
    <div class="card" id="settings-dashboard-card" style="cursor: pointer; flex-direction: row; align-items: center; justify-content: space-between; padding: 12px 16px;">
      <div style="display: flex; align-items: center; gap: 12px;">
        <div style="width: 32px; height: 32px; border-radius: 8px; background: rgba(148, 163, 184, 0.1); display: flex; align-items: center; justify-content: center; color: var(--text-secondary);">
          <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 1 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-4 0v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 1 1-2.83-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1 0-4h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 1 1 2.83-2.83l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 1 1 2.83 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1z"/></svg>
        </div>
        <span style="font-size: 0.875rem; font-weight: 600;">Configure Settings</span>
      </div>
      <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="color: var(--text-secondary);"><polyline points="9 18 15 12 9 6"/></svg>
    </div>
  `;

  return `
    ${mealPlanHtml}
    ${recipesCardHtml}
    ${listsCardHtml}
    ${settingsShortcutHtml}
  `;
}

export function attachDashboardListeners() {
  document.getElementById('recipes-dashboard-card')?.addEventListener('click', () => {
    router.navigate('recipes');
  });

  document.getElementById('lists-dashboard-card')?.addEventListener('click', () => {
    router.navigate('lists');
  });

  document.getElementById('settings-dashboard-card')?.addEventListener('click', () => {
    router.navigate('settings');
  });
}
