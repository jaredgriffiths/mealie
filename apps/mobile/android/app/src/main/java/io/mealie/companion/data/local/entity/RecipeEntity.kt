package io.mealie.companion.data.local.entity

import androidx.room.Entity
import androidx.room.PrimaryKey

@Entity(tableName = "recipes")
data class RecipeEntity(
    @PrimaryKey val id: String,
    val name: String,
    val description: String,
    val ingredientsJson: String,  // Serialized list of ingredients
    val instructionsJson: String, // Serialized list of steps
    val updatedAt: String
)
