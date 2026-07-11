import { recipesRepository } from '../data/repositories';
import { syncEngine } from '../data/sync';

let selectedRecipeId: string | null = null;
let searchQuery = '';

export async function renderRecipesListView(): Promise<string> {
  if (selectedRecipeId) {
    return renderRecipeDetailView(selectedRecipeId);
  }

  const recipes = await recipesRepository.getAll();
  const filtered = recipes.filter(r => 
    r.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
    (r.description && r.description.toLowerCase().includes(searchQuery.toLowerCase()))
  );

  const headerHtml = `
    <div style="display: flex; gap: 8px; width: 100%;">
      <input id="recipes-search-input" class="form-input" style="flex: 1;" type="text" placeholder="Search recipes..." value="${searchQuery}" />
      <button id="recipes-sync-btn" class="btn" style="padding: 12px 16px;">
        <svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21.5 2v6h-6M21.34 15.57a10 10 0 1 1-.57-8.38l5.67-5.67"/></svg>
      </button>
    </div>
  `;

  if (filtered.length === 0) {
    return `
      ${headerHtml}
      <div class="card" style="text-align: center; padding: 32px 16px;">
        <p style="color: var(--text-secondary); margin-bottom: 12px;">No recipes found.</p>
        <button id="recipes-sync-empty-btn" class="btn">Sync from Mealie</button>
      </div>
    `;
  }

  const listHtml = `
    <div style="display: grid; grid-template-columns: 1fr; gap: 12px;">
      ${filtered.map(recipe => {
        const imageSrc = recipe.image ? `${localStorage.getItem('mealie_host') || 'http://localhost:9091'}/api/media/recipes/${recipe.id}/images/min-original.webp` : '';
        return `
          <div class="card recipe-item-card" data-id="${recipe.id}" style="cursor: pointer; flex-direction: row; gap: 16px; align-items: center; padding: 12px;">
            ${imageSrc ? `
              <img src="${imageSrc}" style="width: 60px; height: 60px; border-radius: 8px; object-fit: cover;" onerror="this.style.display='none';" />
            ` : `
              <div style="width: 60px; height: 60px; border-radius: 8px; background: var(--surface-variant); display: flex; align-items: center; justify-content: center; color: var(--text-secondary);">
                <svg viewBox="0 0 24 24" width="24" height="24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 2v20M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"/></svg>
              </div>
            `}
            <div style="flex: 1; min-width: 0;">
              <h3 style="font-size: 0.95rem; font-weight: 700; color: var(--text-color); margin-bottom: 2px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">${recipe.name}</h3>
              <p style="font-size: 0.75rem; color: var(--text-secondary); white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">${recipe.description || 'No description available'}</p>
              <div style="display: flex; gap: 8px; margin-top: 4px;">
                <span style="font-size: 0.7rem; color: var(--primary-color); background: var(--primary-container); padding: 2px 6px; border-radius: 4px; font-weight: 600;">⏰ ${recipe.totalTime || 'N/A'}</span>
              </div>
            </div>
            <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="color: var(--text-secondary);"><polyline points="9 18 15 12 9 6"/></svg>
          </div>
        `;
      }).join('')}
    </div>
  `;

  return `
    ${headerHtml}
    ${listHtml}
  `;
}

async function renderRecipeDetailView(id: string): Promise<string> {
  const recipe = await recipesRepository.get(id);
  if (!recipe) {
    selectedRecipeId = null;
    return 'Recipe not found';
  }

  const imageSrc = recipe.image ? `${localStorage.getItem('mealie_host') || 'http://localhost:9091'}/api/media/recipes/${recipe.id}/images/min-original.webp` : '';

  return `
    <div style="display: flex; flex-direction: column; gap: 16px;">
      <!-- Back Button -->
      <button id="recipe-back-btn" class="btn" style="background: var(--surface-color); border: 1px solid var(--border-color); align-self: flex-start; padding: 8px 12px; font-size: 0.875rem;">
        ← Back to Recipes
      </button>

      <!-- Hero Details -->
      <div class="card" style="gap: 16px; padding: 20px;">
        ${imageSrc ? `
          <img src="${imageSrc}" style="width: 100%; height: 180px; border-radius: 12px; object-fit: cover;" onerror="this.style.display='none';" />
        ` : ''}
        <div>
          <h2 style="font-size: 1.5rem; font-weight: 800; letter-spacing: -0.025em; margin-bottom: 6px;">${recipe.name}</h2>
          <p style="color: var(--text-secondary); font-size: 0.875rem; line-height: 1.5;">${recipe.description || 'No description available'}</p>
        </div>

        <div style="display: flex; gap: 8px; flex-wrap: wrap;">
          ${recipe.totalTime ? `<span style="font-size: 0.75rem; font-weight: 700; color: var(--primary-color); background: var(--primary-container); padding: 4px 8px; border-radius: 6px;">⏰ Total: ${recipe.totalTime}</span>` : ''}
          ${recipe.recipeYield ? `<span style="font-size: 0.75rem; font-weight: 700; color: var(--success-color); background: rgba(16, 185, 129, 0.15); padding: 4px 8px; border-radius: 6px;">🍳 Servings: ${recipe.recipeYield}</span>` : ''}
        </div>
      </div>

      <!-- Ingredients Section -->
      <div class="card" style="gap: 12px;">
        <h3 class="card-title">Ingredients</h3>
        ${!recipe.recipeIngredient || recipe.recipeIngredient.length === 0 ? `
          <p style="font-size: 0.875rem; color: var(--text-secondary);">No ingredients specified.</p>
        ` : `
          <ul style="list-style-type: none; display: flex; flex-direction: column; gap: 8px;">
            ${recipe.recipeIngredient.map(ing => `
              <li style="font-size: 0.875rem; color: var(--text-color); border-bottom: 1px solid rgba(148, 163, 184, 0.05); padding-bottom: 6px; display: flex; gap: 8px;">
                <span style="color: var(--primary-color);">•</span>
                <span>${ing.display || ing.note || ''}</span>
              </li>
            `).join('')}
          </ul>
        `}
      </div>

      <!-- Instructions Section -->
      <div class="card" style="gap: 12px;">
        <h3 class="card-title">Instructions</h3>
        ${!recipe.recipeInstructions || recipe.recipeInstructions.length === 0 ? `
          <p style="font-size: 0.875rem; color: var(--text-secondary);">No instructions specified.</p>
        ` : `
          <ol style="display: flex; flex-direction: column; gap: 12px; padding-left: 16px;">
            ${recipe.recipeInstructions.map(step => `
              <li style="font-size: 0.875rem; color: var(--text-color); line-height: 1.5; padding-left: 4px;">
                ${step.text}
              </li>
            `).join('')}
          </ol>
        `}
      </div>
    </div>
  `;
}

export function attachRecipesListeners(onRefresh: () => void) {
  // Back button in details
  document.getElementById('recipe-back-btn')?.addEventListener('click', () => {
    selectedRecipeId = null;
    onRefresh();
  });

  // Search input
  const searchInput = document.getElementById('recipes-search-input') as HTMLInputElement;
  if (searchInput) {
    searchInput.addEventListener('input', (e) => {
      searchQuery = (e.target as HTMLInputElement).value;
      // Re-render local catalog view without full page reload
      renderRecipesListView().then(html => {
        const main = document.querySelector('main');
        if (main && !selectedRecipeId) {
          main.innerHTML = html.substring(html.indexOf('</button>') + 9); // Preserve search bar
          attachRecipesListeners(onRefresh);
        }
      });
    });
  }

  // Click recipe item
  document.querySelectorAll('.recipe-item-card').forEach((card) => {
    card.addEventListener('click', () => {
      selectedRecipeId = card.getAttribute('data-id');
      onRefresh();
    });
  });

  // Sync button handlers
  const handleSync = async (btn: HTMLButtonElement) => {
    btn.disabled = true;
    const oldHtml = btn.innerHTML;
    btn.textContent = 'Syncing...';

    const success = await syncEngine.syncRecipes();
    if (success) {
      alert('Recipes synced successfully!');
    } else {
      alert('Sync failed. Please verify connection.');
    }

    btn.disabled = false;
    btn.innerHTML = oldHtml;
    onRefresh();
  };

  const syncBtn = document.getElementById('recipes-sync-btn') as HTMLButtonElement;
  syncBtn?.addEventListener('click', () => handleSync(syncBtn));

  const emptySyncBtn = document.getElementById('recipes-sync-empty-btn') as HTMLButtonElement;
  emptySyncBtn?.addEventListener('click', () => handleSync(emptySyncBtn));
}

// Reset selection on tab changes
export function resetRecipeSelection() {
  selectedRecipeId = null;
}
