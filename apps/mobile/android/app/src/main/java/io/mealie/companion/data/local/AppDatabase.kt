package io.mealie.companion.data.local

import androidx.room.Database
import androidx.room.RoomDatabase
import io.mealie.companion.data.local.dao.RecipeDao
import io.mealie.companion.data.local.dao.ShoppingListDao
import io.mealie.companion.data.local.entity.RecipeEntity
import io.mealie.companion.data.local.entity.ShoppingListEntity

@Database(entities = [RecipeEntity::class, ShoppingListEntity::class], version = 3, exportSchema = false)
abstract class AppDatabase : RoomDatabase() {
    abstract fun recipeDao(): RecipeDao
    abstract fun shoppingListDao(): ShoppingListDao
}
