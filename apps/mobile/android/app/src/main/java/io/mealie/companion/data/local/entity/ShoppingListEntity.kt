package io.mealie.companion.data.local.entity

import androidx.room.Entity
import androidx.room.PrimaryKey

@Entity(tableName = "shopping_lists")
data class ShoppingListEntity(
    @PrimaryKey val id: String,
    val name: String,
    val itemsJson: String, // Serialized list of ShoppingListItem
    val updatedAt: String
)
