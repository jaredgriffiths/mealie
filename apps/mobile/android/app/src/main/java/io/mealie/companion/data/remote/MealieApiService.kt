package io.mealie.companion.data.remote

import io.mealie.companion.data.model.Recipe
import io.mealie.companion.data.model.ShoppingList
import retrofit2.http.Body
import retrofit2.http.GET
import retrofit2.http.PUT
import retrofit2.http.Path
import retrofit2.http.Query

interface MealieApiService {
    @GET("api/recipes")
    suspend fun getRecipes(
        @Query("page") page: Int = 1,
        @Query("perPage") perPage: Int = 50
    ): List<Recipe>

    @GET("api/recipes/{id}")
    suspend fun getRecipeById(
        @Path("id") id: String
    ): Recipe

    @GET("api/households/shopping/lists")
    suspend fun getShoppingLists(
        @Query("page") page: Int = 1,
        @Query("perPage") perPage: Int = 50
    ): ShoppingListPaginationResponse

    @PUT("api/households/shopping/lists/{id}")
    suspend fun updateShoppingList(
        @Path("id") id: String,
        @Body list: ShoppingList
    ): ShoppingList
}

data class ShoppingListPaginationResponse(
    val items: List<ShoppingList>
)
