package io.mealie.companion.ui.shopping

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import dagger.hilt.android.lifecycle.HiltViewModel
import io.mealie.companion.data.local.entity.ShoppingListEntity
import io.mealie.companion.data.model.ShoppingList
import io.mealie.companion.data.model.ShoppingListItem
import io.mealie.companion.data.repository.SyncManager
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.SharingStarted
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.stateIn
import kotlinx.coroutines.launch
import javax.inject.Inject

@HiltViewModel
class ShoppingListViewModel @Inject constructor(
    private val syncManager: SyncManager
) : ViewModel() {

    val shoppingLists: StateFlow<List<ShoppingListEntity>> = syncManager.getCachedShoppingListsFlow()
        .stateIn(viewModelScope, SharingStarted.Lazily, emptyList())

    private val _isRefreshing = MutableStateFlow(false)
    val isRefreshing: StateFlow<Boolean> = _isRefreshing

    private val _syncError = MutableStateFlow<String?>(null)
    val syncError: StateFlow<String?> = _syncError

    fun refresh() {
        viewModelScope.launch {
            _isRefreshing.value = true
            _syncError.value = null
            val result = syncManager.refreshShoppingLists()
            if (result.isFailure) {
                _syncError.value = result.exceptionOrNull()?.message ?: "Sync failed"
            }
            _isRefreshing.value = false
        }
    }

    fun toggleItemChecked(listEntity: ShoppingListEntity, itemId: String, currentChecked: Boolean) {
        viewModelScope.launch {
            val currentItems = syncManager.deserializeItems(listEntity.itemsJson)
            
            // 1. Optimistic Update: Immediately toggle locally
            val updatedItems = currentItems.map { item ->
                if (item.id == itemId) item.copy(checked = !currentChecked) else item
            }
            val optimisticList = ShoppingList(
                id = listEntity.id,
                name = listEntity.name,
                items = updatedItems,
                updatedAt = listEntity.updatedAt
            )
            
            // Apply optimistic update in local database
            syncManager.updateShoppingList(optimisticList)

            // 2. Perform Network / Cloud push
            val pushResult = syncManager.updateShoppingList(optimisticList)
            if (pushResult.isFailure) {
                // Rollback if push fails
                val rollbackList = ShoppingList(
                    id = listEntity.id,
                    name = listEntity.name,
                    items = currentItems,
                    updatedAt = listEntity.updatedAt
                )
                syncManager.updateShoppingList(rollbackList)
                _syncError.value = "Failed to update item checked state. Changes reverted."
            }
        }
    }

    fun getListItems(listEntity: ShoppingListEntity): List<ShoppingListItem> {
        return syncManager.deserializeItems(listEntity.itemsJson)
    }
}
