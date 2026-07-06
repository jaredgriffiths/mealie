package io.mealie.companion.data.model

import com.google.gson.annotations.SerializedName

data class ShoppingList(
    val id: String,
    val name: String,
    val items: List<ShoppingListItem>?,
    val updatedAt: String?
)

data class ShoppingListItem(
    val id: String,
    val title: String,
    val checked: Boolean
)
