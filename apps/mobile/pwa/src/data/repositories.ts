import { localDb } from './db';

export interface Recipe {
  id: string;
  name: string;
  description?: string;
  recipeYield?: string;
  totalTime?: string;
  prepTime?: string;
  performTime?: string;
  recipeCategoryId?: string;
  image?: string;
  recipeIngredient?: { note?: string; display?: string }[];
  recipeInstructions?: { text: string }[];
  tags?: { id: string; name: string }[];
}

export interface ShoppingListItem {
  id: string;
  title: string;
  checked: boolean;
}

export interface ShoppingList {
  id: string;
  name: string;
  items: ShoppingListItem[];
  group?: string;
  updatedAt?: string;
}

export class BaseRepository<T extends { id: string }> {
  protected storeName: 'recipes' | 'shopping_lists';
  constructor(storeName: 'recipes' | 'shopping_lists') {
    this.storeName = storeName;
  }

  public async getAll(): Promise<T[]> {
    const store = await localDb.getStore(this.storeName);
    return new Promise((resolve, reject) => {
      const request = store.getAll();
      request.onsuccess = () => resolve(request.result as T[]);
      request.onerror = () => reject(request.error);
    });
  }

  public async get(id: string): Promise<T | null> {
    const store = await localDb.getStore(this.storeName);
    return new Promise((resolve, reject) => {
      const request = store.get(id);
      request.onsuccess = () => resolve(request.result as T || null);
      request.onerror = () => reject(request.error);
    });
  }

  public async save(item: T): Promise<void> {
    const store = await localDb.getStore(this.storeName, 'readwrite');
    return new Promise((resolve, reject) => {
      const request = store.put(item);
      request.onsuccess = () => resolve();
      request.onerror = () => reject(request.error);
    });
  }

  public async saveAll(items: T[]): Promise<void> {
    const db = await localDb.open();
    return new Promise((resolve, reject) => {
      const transaction = db.transaction(this.storeName, 'readwrite');
      const store = transaction.objectStore(this.storeName);

      transaction.oncomplete = () => resolve();
      transaction.onerror = () => reject(transaction.error);

      items.forEach((item) => {
        store.put(item);
      });
    });
  }

  public async count(): Promise<number> {
    const store = await localDb.getStore(this.storeName);
    return new Promise((resolve, reject) => {
      const request = store.count();
      request.onsuccess = () => resolve(request.result);
      request.onerror = () => reject(request.error);
    });
  }

  public async clear(): Promise<void> {
    const store = await localDb.getStore(this.storeName, 'readwrite');
    return new Promise((resolve, reject) => {
      const request = store.clear();
      request.onsuccess = () => resolve();
      request.onerror = () => reject(request.error);
    });
  }
}

export const recipesRepository = new BaseRepository<Recipe>('recipes');
export const shoppingListsRepository = new BaseRepository<ShoppingList>('shopping_lists');
