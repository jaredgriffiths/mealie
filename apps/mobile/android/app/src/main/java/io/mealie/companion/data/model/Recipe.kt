package io.mealie.companion.data.model

import com.google.gson.annotations.SerializedName

data class Recipe(
    val id: String,
    val name: String,
    val description: String?,
    @SerializedName("recipeIngredient") val ingredients: List<Ingredient>?,
    @SerializedName("recipeInstructions") val instructions: List<Instruction>?,
    val updatedAt: String?
)

data class Ingredient(
    val note: String
)

data class Instruction(
    val text: String
)
