package io.mealie.companion.ui.settings

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import dagger.hilt.android.lifecycle.HiltViewModel
import io.mealie.companion.data.local.dao.RecipeDao
import io.mealie.companion.data.local.dao.ShoppingListDao
import io.mealie.companion.data.remote.NetworkObserver
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.SharingStarted
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.combine
import kotlinx.coroutines.flow.stateIn
import kotlinx.coroutines.launch
import javax.inject.Inject

@HiltViewModel
class SettingsViewModel @Inject constructor(
    private val networkObserver: NetworkObserver,
    private val recipeDao: RecipeDao,
    private val shoppingListDao: ShoppingListDao
) : ViewModel() {

    val isLANReachable: StateFlow<Boolean> = networkObserver.isLANReachable

    private val _recipeCount = MutableStateFlow(0)
    val recipeCount: StateFlow<Int> = _recipeCount

    private val _shoppingListCount = MutableStateFlow(0)
    val shoppingListCount: StateFlow<Int> = _shoppingListCount

    init {
        // Collect DB updates and calculate metrics
        viewModelScope.launch {
            recipeDao.getAllRecipesFlow().collect { list ->
                _recipeCount.value = list.size
            }
        }
        viewModelScope.launch {
            shoppingListDao.getAllShoppingListsFlow().collect { list ->
                _shoppingListCount.value = list.size
            }
        }
    }

    fun triggerConnectionCheck() {
        networkObserver.checkMealieReachability()
    }
}
