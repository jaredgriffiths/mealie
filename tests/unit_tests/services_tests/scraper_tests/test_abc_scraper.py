import pytest

from mealie.lang.providers import get_locale_provider
from mealie.services.scraper.scraper_strategies import RecipeScraperABC

ABC_SAMPLE_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>Easy lemon ravioli with baby spinach and cheese - ABC News</title>
    <meta property="og:description" content="A simple dinner with just three steps." />
    <meta property="og:image" content="https://live-production.wcms.abc-cdn.net.au/sample-ravioli.jpg" />
</head>
<body>
    <script id="__NEXT_DATA__" type="application/json">
    {
      "props": {
        "pageProps": {
          "document": {
            "title": "Easy lemon ravioli with baby spinach and cheese",
            "loaders": {
              "recipepage": {
                "recipe": {
                  "name": "Easy lemon ravioli with baby spinach and cheese",
                  "description": "A simple dinner with just three steps.",
                  "recipeYield": "4",
                  "recipeStatsPrepared": {
                    "prepTime": {"visual": "10m", "accessible": "10 minutes"},
                    "cookTime": {"visual": "15m", "accessible": "15 minutes"},
                    "recipeYield": "4"
                  },
                  "recipeIngredientsPrepared": {
                    "ingredients": [
                      {
                        "heading": "",
                        "ingredients": [
                          "625g ravioli",
                          "2 to 3 tablespoons olive oil",
                          "3 garlic cloves, finely chopped"
                        ]
                      },
                      {
                        "heading": "To serve",
                        "ingredients": [
                          "Extra parmesan",
                          "Black pepper"
                        ]
                      }
                    ]
                  },
                  "recipeInstructionsPrepared": {
                    "instructions": {
                      "descriptor": {
                        "type": "tagname",
                        "key": "ol",
                        "children": [
                          {
                            "type": "tagname",
                            "key": "li",
                            "children": [
                              {"type": "text", "content": "Bring a large pot of salted water to the boil."}
                            ]
                          },
                          {
                            "type": "tagname",
                            "key": "li",
                            "children": [
                              {"type": "text", "content": "Cook ravioli and toss with garlic and olive oil."}
                            ]
                          }
                        ]
                      }
                    }
                  },
                  "featuredMedia": [
                    {
                      "picture": {
                        "cropInfo": [
                          {
                            "key": "large",
                            "value": [
                              {"url": "https://live-production.wcms.abc-cdn.net.au/sample-ravioli.jpg"}
                            ]
                          }
                        ]
                      }
                    }
                  ]
                }
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

ABC_FALLBACK_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>Cheesy lemon ravioli - ABC News</title>
    <meta property="og:description" content="Quick pasta dish." />
</head>
<body>
    <h1>Cheesy lemon ravioli</h1>
    <section class="Recipe_recipeIngredients__KJ_ef" data-component="RecipeIngredients">
        <h2>Ingredients</h2>
        <fieldset data-component="Fieldset">
            <div>
                <input type="checkbox" name="500g pasta" />
                <label>500g pasta</label>
            </div>
            <div>
                <input type="checkbox" name="1 lemon, zested" />
                <label>1 lemon, zested</label>
            </div>
        </fieldset>
    </section>
    <h2>Method</h2>
    <div>
        <ol>
            <li>Boil the pasta in salted water.</li>
            <li>Drain and stir in lemon zest.</li>
        </ol>
    </div>
</body>
</html>
"""


@pytest.mark.asyncio
async def test_abc_scraper_can_scrape():
    translator = get_locale_provider("en-US")
    url = "https://www.abc.net.au/news/2025-10-04/easy-lemon-ravioli-with-baby-spinach-cheese/105534228"
    scraper = RecipeScraperABC(url, translator, repos=None)
    assert scraper.can_scrape() is True

    other_url = "https://www.taste.com.au/recipes/ravioli"
    other_scraper = RecipeScraperABC(other_url, translator, repos=None)
    assert other_scraper.can_scrape() is False


@pytest.mark.asyncio
async def test_abc_scraper_parse_next_data():
    url = "https://www.abc.net.au/news/2025-10-04/easy-lemon-ravioli-with-baby-spinach-cheese/105534228"
    translator = get_locale_provider("en-US")

    scraper = RecipeScraperABC(url, translator, repos=None, raw_html=ABC_SAMPLE_HTML)
    recipe, extras = await scraper.parse()

    assert recipe is not None
    assert recipe.name == "Easy lemon ravioli with baby spinach and cheese"
    assert recipe.recipe_yield == "4"
    assert recipe.prep_time == "PT10M"
    assert recipe.perform_time == "PT15M"
    assert recipe.image == "https://live-production.wcms.abc-cdn.net.au/sample-ravioli.jpg"

    # Verify ingredients (including category header)
    ingredients = [i.note for i in recipe.recipe_ingredient]
    assert "625g ravioli" in ingredients
    assert "2 to 3 tablespoons olive oil" in ingredients
    assert "[To serve]" in ingredients
    assert "Extra parmesan" in ingredients

    # Verify instructions
    instructions = [s.text for s in recipe.recipe_instructions]
    assert len(instructions) == 2
    assert "Bring a large pot of salted water to the boil." in instructions[0]
    assert "Cook ravioli and toss with garlic and olive oil." in instructions[1]


@pytest.mark.asyncio
async def test_abc_scraper_fallback_dom():
    url = "https://www.abc.net.au/news/2025-10-04/sample-recipe/105534228"
    translator = get_locale_provider("en-US")

    scraper = RecipeScraperABC(url, translator, repos=None, raw_html=ABC_FALLBACK_HTML)
    recipe, extras = await scraper.parse()

    assert recipe is not None
    assert recipe.name == "Cheesy lemon ravioli"
    ingredients = [i.note for i in recipe.recipe_ingredient]
    assert "500g pasta" in ingredients
    assert "1 lemon, zested" in ingredients

    instructions = [s.text for s in recipe.recipe_instructions]
    assert len(instructions) == 2
    assert "Boil the pasta in salted water." in instructions[0]
