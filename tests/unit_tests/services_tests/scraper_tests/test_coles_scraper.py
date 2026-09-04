import pytest

from mealie.lang.providers import get_locale_provider
from mealie.services.scraper.scraper_strategies import RecipeScraperColes

COLES_SAMPLE_HTML = """
<!DOCTYPE html>
<html>
<head>
    <meta property="og:description"
          content="A delicious Moroccan style slow cooker soup with tender lamb and lentils." />
    <meta property="og:image" content="https://images.coles.com.au/lamb-soup.jpg" />
</head>
<body>
    <script type="application/json">
    {
      "props": {
        "pageProps": {
          "data": {
            ":type": "coles-onesite/components/reciperemotepagenext",
            "title": "Slow cooker Moroccan-style lamb and lentil soup",
            ":items": {
              "recipeingredients": {
                ":type": "coles-onesite/components/recipeingredients",
                "ingredientCategoryList": [
                  {
                    "heading": "",
                    "ingredients": [
                      "1 tbs olive oil",
                      "2 Coles Australian Lamb Shanks"
                    ]
                  },
                  {
                    "heading": "Gremolata",
                    "ingredients": [
                      "1/4 cup mint leaves",
                      "1 tbs lemon zest"
                    ]
                  }
                ]
              },
              "recipemethod": {
                ":type": "coles-onesite/components/recipemethod",
                "steps": [
                  {"stepNumber": "1", "description": "Brown the lamb shanks in a pan."},
                  {"stepNumber": "2", "description": "Transfer to slow cooker with spices and stock."}
                ]
              },
              "recipedetails": {
                ":type": "coles-onesite/components/recipedetails",
                "amountNumber": 4,
                "prepTimeAsMinutes": 15,
                "cookTimeAsMinutes": 255
              }
            }
          }
        }
      }
    }
    </script>
</body>
</html>
"""


@pytest.mark.asyncio
async def test_coles_scraper_parse():
    url = "https://www.coles.com.au/recipes-inspiration/recipes/slow-cooker-moroccan-style-lamb-and-lentil-soup"
    translator = get_locale_provider("en-US")

    scraper = RecipeScraperColes(url, translator, repos=None, raw_html=COLES_SAMPLE_HTML)
    assert scraper.can_scrape() is True

    recipe, extras = await scraper.parse()
    assert recipe is not None
    assert recipe.name == "Slow cooker Moroccan-style lamb and lentil soup"
    assert recipe.recipe_yield == "4"
    assert recipe.prep_time == "PT15M"
    assert recipe.perform_time == "PT255M"

    # Check ingredients with category header
    ingredients = [i.note for i in recipe.recipe_ingredient]
    assert "[Gremolata]" in ingredients
    assert "1 tbs olive oil" in ingredients
    assert "1/4 cup mint leaves" in ingredients

    # Check instruction steps
    instructions = [s.text for s in recipe.recipe_instructions]
    assert len(instructions) == 2
    assert "Brown the lamb shanks in a pan." in instructions[0]
