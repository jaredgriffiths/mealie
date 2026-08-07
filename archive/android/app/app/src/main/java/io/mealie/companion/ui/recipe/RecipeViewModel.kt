package io.mealie.companion.ui.recipe

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import dagger.hilt.android.lifecycle.HiltViewModel
import io.mealie.companion.data.local.entity.RecipeEntity
import io.mealie.companion.data.repository.SyncManager
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.SharingStarted
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.stateIn
import kotlinx.coroutines.launch
import javax.inject.Inject

@HiltViewModel
class RecipeViewModel @Inject constructor(
    private val syncManager: SyncManager
) : ViewModel() {

    val recipeList: StateFlow<List<RecipeEntity>> = syncManager.getCachedRecipesFlow()
        .stateIn(viewModelScope, SharingStarted.Lazily, emptyList())

    private val _isRefreshing = MutableStateFlow(false)
    val isRefreshing: StateFlow<Boolean> = _isRefreshing

    private val _syncError = MutableStateFlow<String?>(null)
    val syncError: StateFlow<String?> = _syncError

    fun refresh() {
        viewModelScope.launch {
            _isRefreshing.value = true
            _syncError.value = null
            val result = syncManager.refreshRecipes()
            if (result.isFailure) {
                _syncError.value = result.exceptionOrNull()?.message ?: "Unknown sync error"
            }
            _isRefreshing.value = false
        }
    }

    fun loadRecipeDetails(recipeId: String) {
        viewModelScope.launch {
            syncManager.refreshRecipeDetails(recipeId)
        }
    }
}
