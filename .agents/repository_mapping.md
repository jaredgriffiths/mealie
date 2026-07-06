# SQLAlchemy Model to Repository Mappings

This index documents the correct mappings between SQLAlchemy models and the attributes available on Mealie's repository factory wrapper `AllRepositories` (instantiated as `self.repos`).

## Repository Map

| Domain Model / Context | Repository Instance Attribute | Source Class File |
|---|---|---|
| **Recipes** | `self.repos.recipes` | `mealie/repos/repository_recipes.py` |
| **Shopping Lists** | `self.repos.group_shopping_lists` | `mealie/repos/repository_shopping_list.py` |
| **Meal Plans** | `self.repos.meals` | `mealie/repos/repository_meals.py` |
| **Users** | `self.repos.users` | `mealie/repos/repository_users.py` |
| **Groups** | `self.repos.groups` | `mealie/repos/repository_group.py` |
| **Households** | `self.repos.households` | `mealie/repos/repository_household.py` |
| **AI Providers** | `self.repos.group_ai_providers` | `mealie/repos/repository_ai_provider.py` |
| **Cookbooks** | `self.repos.cookbooks` | `mealie/repos/repository_cookbooks.py` |

> [!WARNING]
> **Common Pitfall**: Do **NOT** use `self.repos.shopping_lists` or `self.repos.meal_plans`. Doing so will raise an `AttributeError` at runtime. Refer to the mapping above.
