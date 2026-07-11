package io.mealie.companion.data.model

import com.google.gson.annotations.SerializedName

data class ShoppingList(
    val id: String,
    val name: String,
    @SerializedName("list_items")
    val items: List<ShoppingListItem>?,
    val updatedAt: String?
)

data class ShoppingListItem(
    val id: String,
    @SerializedName("display")
    val title: String,
    val checked: Boolean
)
