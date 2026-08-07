package io.mealie.companion.data.model

import com.google.gson.annotations.SerializedName

data class Recipe(
    val id: String,
    val name: String,
    val description: String?,
    val image: String?,
    val tags: List<RecipeTag>?,
    @SerializedName("recipeIngredient") val ingredients: List<Ingredient>?,
    @SerializedName("recipeInstructions") val instructions: List<Instruction>?,
    val updatedAt: String?
)

data class RecipeTag(
    val id: String,
    val name: String,
    val slug: String
)

data class Ingredient(
    val note: String?,
    val display: String?
)

data class Instruction(
    val text: String
)
