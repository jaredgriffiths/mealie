package io.mealie.companion.data.remote

import io.mealie.companion.data.model.Recipe
import io.mealie.companion.data.model.ShoppingList
import retrofit2.http.Body
import retrofit2.http.GET
import retrofit2.http.PUT
import retrofit2.http.Path
import retrofit2.http.Query
import retrofit2.http.POST
import retrofit2.http.Field
import retrofit2.http.FormUrlEncoded

interface MealieApiService {
    @GET("api/recipes")
    suspend fun getRecipes(
        @Query("page") page: Int = 1,
        @Query("perPage") perPage: Int = 50
    ): RecipePaginationResponse

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

    @GET("api/households/shopping/lists/{id}")
    suspend fun getShoppingListById(
        @Path("id") id: String
    ): ShoppingList

    @POST("api/auth/token")
    @FormUrlEncoded
    suspend fun getAccessToken(
        @Field("username") username: String,
        @Field("password") password: String
    ): MealieAuthToken
}

data class ShoppingListPaginationResponse(
    val items: List<ShoppingList>
)

data class RecipePaginationResponse(
    val items: List<Recipe>
)

data class MealieAuthToken(
    val access_token: String,
    val token_type: String
)
