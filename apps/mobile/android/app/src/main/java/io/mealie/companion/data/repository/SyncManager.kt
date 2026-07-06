package io.mealie.companion.data.repository

import com.google.firebase.firestore.FirebaseFirestore
import com.google.gson.Gson
import com.google.gson.reflect.TypeToken
import io.mealie.companion.data.local.dao.RecipeDao
import io.mealie.companion.data.local.dao.ShoppingListDao
import io.mealie.companion.data.local.entity.RecipeEntity
import io.mealie.companion.data.local.entity.ShoppingListEntity
import io.mealie.companion.data.model.ShoppingList
import io.mealie.companion.data.model.ShoppingListItem
import io.mealie.companion.data.remote.MealieApiService
import io.mealie.companion.data.remote.NetworkObserver
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.tasks.await
import kotlinx.coroutines.withContext
import javax.inject.Inject
import javax.inject.Singleton

@Singleton
class SyncManager @Inject constructor(
    private val recipeDao: RecipeDao,
    private val shoppingListDao: ShoppingListDao,
    private val mealieApiService: MealieApiService,
    private val networkObserver: NetworkObserver
) {
    private val firestore = FirebaseFirestore.getInstance()
    private val gson = Gson()

    // =======================================================================
    // Recipes Sync
    // =======================================================================

    fun getCachedRecipesFlow(): Flow<List<RecipeEntity>> = recipeDao.getAllRecipesFlow()

    suspend fun refreshRecipes(): Result<Unit> = withContext(Dispatchers.IO) {
        try {
            if (networkObserver.isLANReachable.value) {
                val recipes = mealieApiService.getRecipes(1, 100)
                val entities = recipes.map { recipe ->
                    RecipeEntity(
                        id = recipe.id,
                        name = recipe.name,
                        description = recipe.description ?: "",
                        ingredientsJson = recipe.ingredients?.joinToString("\n") { it.note } ?: "",
                        instructionsJson = recipe.instructions?.joinToString("\n") { it.text } ?: "",
                        updatedAt = recipe.updatedAt ?: ""
                    )
                }
                recipeDao.insertRecipes(entities)
                Result.success(Unit)
            } else {
                val snapshot = firestore.collection("recipes").get().await()
                val entities = snapshot.documents.mapNotNull { doc ->
                    val name = doc.getString("name") ?: return@mapNotNull null
                    val description = doc.getString("description") ?: ""
                    val ingredients = doc.get("ingredients") as? List<String> ?: emptyList()
                    val steps = doc.get("steps") as? List<String> ?: emptyList()
                    val updatedAt = doc.getString("updated_at") ?: ""
                    
                    RecipeEntity(
                        id = doc.id,
                        name = name,
                        description = description,
                        ingredientsJson = ingredients.joinToString("\n"),
                        instructionsJson = steps.joinToString("\n"),
                        updatedAt = updatedAt
                    )
                }
                recipeDao.insertRecipes(entities)
                Result.success(Unit)
            }
        } catch (e: Exception) {
            Result.failure(e)
        }
    }

    // =======================================================================
    // Shopping Lists Sync & Pushes
    // =======================================================================

    fun getCachedShoppingListsFlow(): Flow<List<ShoppingListEntity>> = shoppingListDao.getAllShoppingListsFlow()

    fun deserializeItems(json: String): List<ShoppingListItem> {
        val type = object : TypeToken<List<ShoppingListItem>>() {}.type
        return gson.fromJson(json, type) ?: emptyList()
    }

    suspend fun refreshShoppingLists(): Result<Unit> = withContext(Dispatchers.IO) {
        try {
            if (networkObserver.isLANReachable.value) {
                val response = mealieApiService.getShoppingLists(1, 50)
                val entities = response.items.map { list ->
                    ShoppingListEntity(
                        id = list.id,
                        name = list.name,
                        itemsJson = gson.toJson(list.items ?: emptyList<ShoppingListItem>()),
                        updatedAt = list.updatedAt ?: ""
                    )
                }
                shoppingListDao.insertShoppingLists(entities)
                Result.success(Unit)
            } else {
                val snapshot = firestore.collection("shopping_lists").get().await()
                val entities = snapshot.documents.mapNotNull { doc ->
                    val name = doc.getString("name") ?: return@mapNotNull null
                    val items = doc.get("items") as? List<Map<String, Any>> ?: emptyList()
                    val updatedAt = doc.getString("updated_at") ?: ""
                    
                    val listItems = items.map { item ->
                        ShoppingListItem(
                            id = item["id"] as? String ?: "",
                            title = item["title"] as? String ?: "",
                            checked = item["checked"] as? Boolean ?: false
                        )
                    }

                    ShoppingListEntity(
                        id = doc.id,
                        name = name,
                        itemsJson = gson.toJson(listItems),
                        updatedAt = updatedAt
                    )
                }
                shoppingListDao.insertShoppingLists(entities)
                Result.success(Unit)
            }
        } catch (e: Exception) {
            Result.failure(e)
        }
    }

    suspend fun updateShoppingList(list: ShoppingList): Result<Unit> = withContext(Dispatchers.IO) {
        try {
            // Write to Room immediately
            val entity = ShoppingListEntity(
                id = list.id,
                name = list.name,
                itemsJson = gson.toJson(list.items ?: emptyList<ShoppingListItem>()),
                updatedAt = java.text.SimpleDateFormat("yyyy-MM-dd'T'HH:mm:ss'Z'", java.util.Locale.US).format(java.util.Date())
            )
            shoppingListDao.insertShoppingLists(listOf(entity))

            if (networkObserver.isLANReachable.value) {
                // LAN Push
                mealieApiService.updateShoppingList(list.id, list)
                Result.success(Unit)
            } else {
                // Cloud Firestore Push (Write Transaction)
                val docRef = firestore.collection("shopping_lists").document(list.id)
                val itemsMap = list.items?.map { item ->
                    mapOf(
                        "id" to item.id,
                        "title" to item.title,
                        "checked" to item.checked
                    )
                } ?: emptyList()

                firestore.runTransaction { transaction ->
                    transaction.update(docRef, "items", itemsMap)
                    transaction.update(docRef, "updated_at", entity.updatedAt)
                    transaction.update(docRef, "updated_by", "mobile_app")
                }.await()
                Result.success(Unit)
            }
        } catch (e: Exception) {
            Result.failure(e)
        }
    }
}
