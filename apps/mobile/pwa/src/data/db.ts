const DB_NAME = 'mealie_companion_db';
const DB_VERSION = 1;

export class LocalDatabase {
  private db: IDBDatabase | null = null;

  public open(): Promise<IDBDatabase> {
    return new Promise((resolve, reject) => {
      if (this.db) {
        resolve(this.db);
        return;
      }

      const request = indexedDB.open(DB_NAME, DB_VERSION);

      request.onerror = () => {
        reject(new Error('Failed to open local database'));
      };

      request.onsuccess = (event) => {
        this.db = (event.target as IDBOpenDBRequest).result;
        resolve(this.db);
      };

      request.onupgradeneeded = (event) => {
        const db = (event.target as IDBOpenDBRequest).result;

        if (!db.objectStoreNames.contains('recipes')) {
          db.createObjectStore('recipes', { keyPath: 'id' });
        }

        if (!db.objectStoreNames.contains('shopping_lists')) {
          db.createObjectStore('shopping_lists', { keyPath: 'id' });
        }
      };
    });
  }

  public async getStore(storeName: 'recipes' | 'shopping_lists', mode: IDBTransactionMode = 'readonly'): Promise<IDBObjectStore> {
    const db = await this.open();
    const transaction = db.transaction(storeName, mode);
    return transaction.objectStore(storeName);
  }
}

export const localDb = new LocalDatabase();
