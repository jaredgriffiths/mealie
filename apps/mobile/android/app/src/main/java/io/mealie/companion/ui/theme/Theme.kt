package io.mealie.companion.ui.theme

import android.os.Build
import androidx.compose.foundation.isSystemInDarkTheme
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.darkColorScheme
import androidx.compose.material3.dynamicDarkColorScheme
import androidx.compose.material3.dynamicLightColorScheme
import androidx.compose.material3.lightColorScheme
import androidx.compose.runtime.Composable
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.LocalContext

private val MealieOrange = Color(0xFFE58325)
private val MealieAccentTeal = Color(0xFF007A99)
private val MealieSecondaryBurgundy = Color(0xFF973542)

private val DarkColorScheme = darkColorScheme(
    primary = MealieOrange,
    secondary = MealieSecondaryBurgundy,
    tertiary = MealieAccentTeal,
    background = Color(0xFF121212),
    surface = Color(0xFF1E1E1E),
    onPrimary = Color.White,
    onSecondary = Color.White,
    onTertiary = Color.White,
    onBackground = Color(0xFFE2E2E2),
    onSurface = Color(0xFFE2E2E2),
    primaryContainer = Color(0xFF4E2C00),
    onPrimaryContainer = Color(0xFFFFDDBB)
)

private val LightColorScheme = lightColorScheme(
    primary = MealieOrange,
    secondary = MealieSecondaryBurgundy,
    tertiary = MealieAccentTeal,
    background = Color(0xFFFFFBF7), // Warm light background
    surface = Color.White,
    onPrimary = Color.White,
    onSecondary = Color.White,
    onTertiary = Color.White,
    onBackground = Color(0xFF1C1B1F),
    onSurface = Color(0xFF1C1B1F),
    primaryContainer = Color(0xFFFFDDBB),
    onPrimaryContainer = Color(0xFF311400),
    surfaceVariant = Color(0xFFF4EBE1),
    onSurfaceVariant = Color(0xFF4F4539)
)

@Composable
fun MealieCompanionTheme(
    darkTheme: Boolean = isSystemInDarkTheme(),
    dynamicColor: Boolean = false, // Set default to false to prioritize Mealie brand colors
    content: @Composable () -> Unit
) {
    val colorScheme = when {
        dynamicColor && Build.VERSION.SDK_INT >= Build.VERSION_CODES.S -> {
            val context = LocalContext.current
            if (darkTheme) dynamicDarkColorScheme(context) else dynamicLightColorScheme(context)
        }
        darkTheme -> DarkColorScheme
        else -> LightColorScheme
    }

    MaterialTheme(
        colorScheme = colorScheme,
        content = content
    )
}
