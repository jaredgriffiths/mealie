import { recipesRepository, shoppingListsRepository } from './repositories';
import type { Recipe, ShoppingList } from './repositories';

export class Result<T> {
  private readonly value: T | null;
  private readonly error: Error | null;

  private constructor(value: T | null, error: Error | null) {
    this.value = value;
    this.error = error;
  }

  public static success<T>(value: T): Result<T> {
    return new Result(value, null);
  }

  public static failure<T>(error: Error): Result<T> {
    return new Result<T>(null, error);
  }

  public get isSuccess(): boolean {
    return this.error === null;
  }

  public get isFailure(): boolean {
    return this.error !== null;
  }

  public exceptionOrNull(): Error | null {
    return this.error;
  }

  public getOrNull(): T | null {
    return this.value;
  }
}

export class SyncEngine {
  private getHeaders(): HeadersInit {
    const token = localStorage.getItem('mealie_token');
    return {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    };
  }

  private getHost(): string {
    return localStorage.getItem('mealie_host') || 'http://localhost:9091';
  }

  public async syncRecipes(): Promise<boolean> {
    const host = this.getHost();
    try {
      const response = await fetch(`${host}/api/recipes?page=1&perPage=50`, {
        headers: this.getHeaders()
      });

      if (!response.ok) throw new Error('Failed to fetch recipes list');

      const data = await response.json();
      const remoteRecipes: Recipe[] = data.items || [];

      // For each recipe, preserve detailed ingredients/instructions if already in IndexedDB
      const localRecipes = await recipesRepository.getAll();
      const localMap = new Map(localRecipes.map(r => [r.id, r]));

      const recipesToSave: Recipe[] = [];

      for (const remote of remoteRecipes) {
        const local = localMap.get(remote.id);
        
        // If local version has detail instructions, preserve them
        if (local && local.recipeIngredient && local.recipeIngredient.length > 0) {
          recipesToSave.push({
            ...remote,
            recipeIngredient: local.recipeIngredient,
            recipeInstructions: local.recipeInstructions,
            tags: local.tags
          });
        } else {
          // Fetch full recipe detail from Mealie API to get ingredients and instructions
          try {
            const detailResponse = await fetch(`${host}/api/recipes/${remote.id}`, {
              headers: this.getHeaders()
            });
            if (detailResponse.ok) {
              const detail = await detailResponse.json();
              recipesToSave.push(detail);
            } else {
              recipesToSave.push(remote);
            }
          } catch {
            recipesToSave.push(remote);
          }
        }
      }

      await recipesRepository.saveAll(recipesToSave);
      return true;
    } catch (err) {
      console.error('[SyncEngine] Recipe sync failed:', err);
      return false;
    }
  }

  public async syncShoppingLists(): Promise<boolean> {
    const host = this.getHost();
    try {
      const response = await fetch(`${host}/api/households/shopping/lists?page=1&perPage=50`, {
        headers: this.getHeaders()
      });

      if (!response.ok) throw new Error('Failed to fetch shopping lists');

      const data = await response.json();
      const remoteLists: any[] = data.items || [];

      // Fetch items details for each list
      const listsToSave: ShoppingList[] = [];

      for (const remote of remoteLists) {
        try {
          const detailResponse = await fetch(`${host}/api/households/shopping/lists/${remote.id}`, {
            headers: this.getHeaders()
          });
          if (detailResponse.ok) {
            const detail = await detailResponse.json();
            // Map API list_items to local items key
            detail.items = (detail.list_items || []).map((item: any) => ({
              id: item.id,
              title: item.display || item.note || item.food?.name || 'Unlabeled Item',
              checked: item.checked || false
            }));
            listsToSave.push(detail);
          } else {
            remote.items = [];
            listsToSave.push(remote);
          }
        } catch {
          remote.items = [];
          listsToSave.push(remote);
        }
      }

      await shoppingListsRepository.saveAll(listsToSave);
      return true;
    } catch (err) {
      console.error('[SyncEngine] Shopping lists sync failed:', err);
      return false;
    }
  }

  public async updateShoppingListRemote(list: ShoppingList): Promise<Result<ShoppingList>> {
    const host = this.getHost();
    try {
      // Map local items to API list_items layout expected by backend
      const payload = {
        id: list.id,
        name: list.name,
        group_id: list.group || undefined,
        list_items: list.items.map(item => ({
          id: item.id,
          shopping_list_id: list.id,
          checked: item.checked,
          note: item.title,
          display: item.title
        }))
      };

      const response = await fetch(`${host}/api/households/shopping/lists/${list.id}`, {
        method: 'PUT',
        headers: this.getHeaders(),
        body: JSON.stringify(payload)
      });

      if (!response.ok) {
        throw new Error(`Server returned HTTP ${response.status} Error`);
      }

      const updatedList = await response.json();
      // Map backend response fields to local database fields
      updatedList.items = (updatedList.list_items || []).map((item: any) => ({
        id: item.id,
        title: item.display || item.note || 'Item',
        checked: item.checked || false
      }));

      return Result.success(updatedList);
    } catch (err: any) {
      console.warn('[SyncEngine] Remote checklist update failed:', err);
      return Result.failure(err);
    }
  }
}

export const syncEngine = new SyncEngine();
