# Mobile Applications (Placeholder)

This directory is reserved for future mobile applications (iOS, Android, React Native, or Flutter) that connect to the Mealie Firebase Sync Bridge.

## Mobile Architecture Note
The mobile apps will utilize a **Hybrid Sync** strategy:
1. **Local LAN Mode (Primary)**: When connected to the home network, communicate directly with the Mealie API at `http://<server-ip>:9925` to download recipes, synchronize data, and access media assets.
2. **Cloud Mode (Fallback)**: When away from home, query and write light updates (such as checking items on the shopping list or modifying meal plans) using the **Google Firestore** cloud cache.
