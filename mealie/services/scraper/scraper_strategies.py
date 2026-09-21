import asyncio
import functools
import json
import re
from abc import ABC, abstractmethod
from collections.abc import Awaitable, Callable
from pathlib import Path
from typing import Any, TypedDict

import bs4
import extruct
import yt_dlp
from fastapi import HTTPException, status
from recipe_scrapers import NoSchemaFoundInWildMode, SchemaScraperFactory, scrape_html
from slugify import slugify
from w3lib.html import get_base_url
from yt_dlp.extractor.generic import GenericIE

from mealie.core import exceptions
from mealie.core.dependencies.dependencies import get_temporary_path
from mealie.core.root_logger import get_logger
from mealie.lang.providers import Translator
from mealie.pkgs import safehttp
from mealie.repos.repository_factory import AllRepositories
from mealie.schema.openai.general import OpenAIText
from mealie.schema.openai.recipe import OpenAIRecipe
from mealie.schema.recipe.recipe import Recipe, RecipeStep
from mealie.schema.recipe.recipe_ingredient import RecipeIngredient
from mealie.schema.recipe.recipe_notes import RecipeNote
from mealie.services.openai import OpenAIService
from mealie.services.scraper.scraped_extras import ScrapedExtras

from . import cleaner

SCRAPER_TIMEOUT = 15

BROWSER_IMPERSONATIONS: list[str | None] = [
    None,
    "chrome110",
    "chrome120",
    "firefox110",
    "chrome",
    "firefox",
]

REALISTIC_BROWSER_HEADERS = {
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Sec-Ch-Ua": '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
    "Sec-Ch-Ua-Mobile": "?0",
    "Sec-Ch-Ua-Platform": '"Windows"',
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "none",
    "Sec-Fetch-User": "?1",
    "Upgrade-Insecure-Requests": "1",
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    ),
}

ANTI_BOT_BLOCK_SIGNATURES = [
    "pardon our interruption",
    "cf-browser-verification",
    "challenge-running",
    "attention required! | cloudflare",
    "access denied",
    "security check to access",
    "datadome",
]

logger = get_logger()


@functools.cache
def _get_yt_dlp_extractors() -> list:
    """Build and cache the yt-dlp extractor list once per process lifetime."""
    return [ie for ie in yt_dlp.extractor.gen_extractors() if ie.working() and not isinstance(ie, GenericIE)]


class ForceTimeoutException(Exception):
    pass


async def safe_scrape_html(url: str) -> str:
    """
    Scrapes the html from a url using resilient browser impersonation rotation,
    configured outbound proxies, and optional FlareSolverr challenge escalation.
    """
    result = await safehttp.resilient_fetch(url)
    if not result:
        return ""
    return result.text


class ABCScraperStrategy(ABC):
    """
    Abstract class for all recipe parsers.
    """

    url: str

    def __init__(
        self,
        url: str,
        translator: Translator,
        repos: AllRepositories,
        raw_html: str | None = None,
    ) -> None:
        self.logger = get_logger()
        self.url = url
        self.raw_html = raw_html
        self.translator = translator
        self.repos = repos

    @abstractmethod
    def can_scrape(self) -> bool: ...

    @abstractmethod
    async def get_html(self, url: str) -> str: ...

    @abstractmethod
    async def parse(
        self, on_progress: Callable[[str], Awaitable[None]] | None = None
    ) -> tuple[Recipe, ScrapedExtras] | tuple[None, None]:
        """Parse a recipe from a web URL.

        Args:
            recipe_url (str): Full URL of the recipe to scrape.

        Returns:
            Recipe: Recipe object.
        """
        ...


class RecipeScraperPackage(ABCScraperStrategy):
    def can_scrape(self) -> bool:
        return bool(self.url or self.raw_html)

    @staticmethod
    def ld_json_to_html(ld_json: str) -> str:
        return (
            "<!DOCTYPE html><html><head>"
            f'<script type="application/ld+json">{ld_json}</script>'
            "</head><body></body></html>"
        )

    async def get_html(self, url: str) -> str:
        return self.raw_html or await safe_scrape_html(url)

    def clean_scraper(self, scraped_data: SchemaScraperFactory.SchemaScraper, url: str) -> tuple[Recipe, ScrapedExtras]:
        def try_get_default(
            func_call: Callable | None,
            get_attr: str,
            default: Any,
            clean_func=None,
            **clean_func_kwargs,
        ):
            value = default

            if func_call:
                try:
                    value = func_call()
                except Exception:
                    self.logger.error(f"Error parsing recipe func_call for '{get_attr}'")

            if value == default:
                try:
                    value = scraped_data.schema.data.get(get_attr)
                except Exception:
                    self.logger.error(f"Error parsing recipe attribute '{get_attr}'")

            if clean_func:
                value = clean_func(value, **clean_func_kwargs)

            return value

        def get_instructions() -> list[RecipeStep]:
            instruction_as_text = try_get_default(
                scraped_data.instructions,
                "recipeInstructions",
                ["No Instructions Found"],
            )

            self.logger.debug(f"Scraped Instructions: (Type: {type(instruction_as_text)}) \n {instruction_as_text}")

            instruction_as_text = cleaner.clean_instructions(instruction_as_text)

            self.logger.debug(f"Cleaned Instructions: (Type: {type(instruction_as_text)}) \n {instruction_as_text}")

            try:
                return [RecipeStep(title="", text=x.get("text")) for x in instruction_as_text]
            except TypeError:
                return []

        def get_notes() -> list[RecipeNote]:
            """Extract notes from schema.org recipe data and convert to RecipeNote objects"""
            notes_data = try_get_default(None, "notes", None)

            if not notes_data or not isinstance(notes_data, list):
                return []

            cleaned_notes = []
            for note in notes_data:
                if not isinstance(note, dict):
                    continue

                if text := note.get("text"):
                    cleaned_notes.append(
                        RecipeNote(
                            title=cleaner.clean_string(note.get("title", "")),
                            text=cleaner.clean_string(text),
                        )
                    )

            return cleaned_notes

        cook_time = try_get_default(
            None, "performTime", None, cleaner.clean_time, translator=self.translator
        ) or try_get_default(scraped_data.cook_time, "cookTime", None, cleaner.clean_time, translator=self.translator)

        extras = ScrapedExtras()

        extras.set_tags(try_get_default(scraped_data.keywords, "keywords", "", cleaner.clean_tags))
        extras.set_categories(try_get_default(scraped_data.category, "recipeCategory", "", cleaner.clean_categories))

        recipe = Recipe(
            name=try_get_default(scraped_data.title, "name", "No Name Found", cleaner.clean_string),
            slug="",
            image=try_get_default(scraped_data.image, "image", None, cleaner.clean_image),
            description=try_get_default(scraped_data.description, "description", "", cleaner.clean_string),
            nutrition=try_get_default(scraped_data.nutrients, "nutrition", None, cleaner.clean_nutrition),
            recipe_yield=try_get_default(scraped_data.yields, "recipeYield", "1", cleaner.clean_string),
            recipe_ingredient=try_get_default(
                scraped_data.ingredients,
                "recipeIngredient",
                [""],
                cleaner.clean_ingredients,
            ),
            recipe_instructions=get_instructions(),
            total_time=try_get_default(
                scraped_data.total_time, "totalTime", None, cleaner.clean_time, translator=self.translator
            ),
            prep_time=try_get_default(
                scraped_data.prep_time, "prepTime", None, cleaner.clean_time, translator=self.translator
            ),
            perform_time=cook_time,
            org_url=url or try_get_default(None, "url", None, cleaner.clean_string),
            notes=get_notes(),
        )

        return recipe, extras

    async def scrape_url(self) -> SchemaScraperFactory.SchemaScraper | Any | None:
        recipe_html = await self.get_html(self.url)

        try:
            # scrape_html requires a URL, but we might not have one, so we default to a dummy URL
            scraped_schema = scrape_html(recipe_html, org_url=self.url or "https://example.com", supported_only=False)
        except (NoSchemaFoundInWildMode, AttributeError):
            self.logger.error(f"Recipe Scraper was unable to extract a recipe from {self.url}")
            return None

        except ConnectionError as e:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, {"details": "CONNECTION_ERROR"}) from e

        # Check to see if the recipe is valid
        try:
            ingredients = scraped_schema.ingredients()
        except Exception:
            ingredients = []

        try:
            instruct: list | str = scraped_schema.instructions()
        except Exception:
            instruct = []

        if instruct or ingredients:
            return scraped_schema

        self.logger.debug(f"Recipe Scraper [Package] was unable to extract a recipe from {self.url}")
        return None

    async def parse(self, on_progress: Callable[[str], Awaitable[None]] | None = None):
        """
        Parse a recipe from a given url.
        """

        if on_progress:
            await on_progress(self.translator.t("recipe.create-progress.extracting-recipe-data"))

        scraped_data = await self.scrape_url()

        if scraped_data is None:
            return None

        return self.clean_scraper(scraped_data, self.url)


class RecipeScraperOpenAI(RecipeScraperPackage):
    """
    A wrapper around the `RecipeScraperPackage` class that uses OpenAI to extract the recipe from the URL,
    rather than trying to scrape it directly.
    """

    def can_scrape(self) -> bool:
        settings = self.repos.group_ai_provider_settings.get_one(self.repos.group_id)
        return bool(settings and settings.ai_enabled and super().can_scrape())

    def extract_json_ld_data_from_html(self, soup: bs4.BeautifulSoup) -> str:
        data_parts: list[str] = []
        for script in soup.find_all("script", type="application/ld+json"):
            try:
                script_data = script.string
                if script_data:
                    data_parts.append(str(script_data))
            except AttributeError:
                pass

        return "\n\n".join(data_parts)

    def find_image(self, soup: bs4.BeautifulSoup) -> str | None:
        # find the open graph image tag
        og_image = soup.find("meta", property="og:image")
        if og_image and og_image.get("content"):
            return og_image["content"]

        # find the largest image on the page
        largest_img = None
        max_size = 0
        for img in soup.find_all("img"):
            width = img.get("width", 0)
            height = img.get("height", 0)
            if not width or not height:
                continue

            try:
                size = int(width) * int(height)
            except (ValueError, TypeError):
                size = 1
            if size > max_size:
                max_size = size
                largest_img = img

        if largest_img:
            return largest_img.get("src")

        return None

    def format_html_to_text(self, html: str) -> str:
        soup = bs4.BeautifulSoup(html, "lxml")

        text = soup.get_text(separator="\n", strip=True)
        text += self.extract_json_ld_data_from_html(soup)
        if not text:
            raise Exception("No text or ld+json data found in HTML")

        try:
            image = self.find_image(soup)
        except Exception:
            image = None

        components = [f"Convert this content to JSON: {text}"]
        if image:
            components.append(f"Recipe Image: {image}")
        return "\n".join(components)

    async def get_html(self, url: str) -> str:
        service = OpenAIService(self.repos)
        html = self.raw_html or await safe_scrape_html(url)
        text = self.format_html_to_text(html)
        try:
            prompt = service.get_prompt("recipes.scrape-recipe")

            response = await service.get_response(prompt, text, response_schema=OpenAIText)
            if not (response and response.text):
                raise Exception("OpenAI did not return any data")

            return self.ld_json_to_html(response.text)
        except Exception:
            self.logger.exception(f"OpenAI was unable to extract a recipe from {url}")
            return ""

    async def parse(self, on_progress: Callable[[str], Awaitable[None]] | None = None):
        if on_progress:
            await on_progress(self.translator.t("recipe.create-progress.creating-recipe-with-ai"))

        return await super().parse()


class TranscribedAudio(TypedDict):
    audio: Path
    subtitle: Path | None
    title: str
    description: str
    thumbnail_url: str | None
    transcription: str


class RecipeScraperOpenAITranscription(ABCScraperStrategy):
    SUBTITLE_LANGS = ["en", "fr", "es", "de", "it"]

    def can_scrape(self) -> bool:
        if not self.url:
            return False

        settings = self.repos.group_ai_provider_settings.get_one(self.repos.group_id)
        if not (settings and settings.audio_provider_enabled):
            return False

        # Check if we can actually download something to transcribe
        return any(ie.suitable(self.url) for ie in _get_yt_dlp_extractors())

    @staticmethod
    def _parse_subtitle_content(subtitle_content: str) -> str:
        # TODO: is there a better way to parse subtitles that's more efficient?

        lines = []
        for line in subtitle_content.split("\n"):
            if line.strip() and not line.startswith("WEBVTT") and "-->" not in line and not line.isdigit():
                lines.append(line.strip())

        raw_content = " ".join(lines)
        content = re.sub(r"<[^>]+>", "", raw_content)
        return content

    def _download_audio(self, temp_path: Path) -> TranscribedAudio:
        """Downloads audio and subtitles from the video URL."""
        output_template = temp_path / "mealie"  # No extension here

        ydl_opts = {
            "format": "bestaudio/best",
            "outtmpl": str(output_template) + ".%(ext)s",
            "quiet": True,
            "writesubtitles": True,
            "writeautomaticsub": True,
            "subtitleslangs": self.SUBTITLE_LANGS,
            "skip_download": False,
            "ignoreerrors": True,
            "postprocessors": [
                {
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": "mp3",
                    "preferredquality": "32",
                }
            ],
            "postprocessor_args": ["-ac", "1"],
        }

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(self.url, download=True)

                if info is None:
                    raise exceptions.VideoDownloadError(
                        "Failed to extract video information. The video may be unavailable or the URL is invalid."
                    )

                sub_path = None
                for lang in self.SUBTITLE_LANGS:
                    potential_path = output_template.with_suffix(f".{lang}.vtt")
                    if potential_path.exists():
                        sub_path = potential_path
                        break

                return {
                    "audio": output_template.with_suffix(".mp3"),
                    "subtitle": sub_path,
                    "title": info.get("title", ""),
                    "description": info.get("description", ""),
                    "thumbnail_url": info.get("thumbnail") or None,
                    "transcription": "",
                }
        except exceptions.VideoDownloadError:
            raise
        except Exception as e:
            raise exceptions.VideoDownloadError(f"Failed to download video: {e}") from e

    async def get_html(self, url: str) -> str:
        return self.raw_html or ""  # we don't use HTML with this scraper since we use ytdlp

    async def parse(
        self,
        on_progress: Callable[[str], Awaitable[None]] | None = None,
    ) -> tuple[Recipe, ScrapedExtras] | tuple[None, None]:
        openai_service = OpenAIService(self.repos)

        with get_temporary_path() as temp_path:
            if on_progress:
                await on_progress(self.translator.t("recipe.create-progress.downloading-video"))

            video_data = await asyncio.to_thread(self._download_audio, temp_path)

            if video_data["subtitle"]:
                try:
                    with open(video_data["subtitle"], encoding="utf-8") as f:
                        subtitle_content = f.read()
                    video_data["transcription"] = self._parse_subtitle_content(subtitle_content)
                    self.logger.info("Using subtitles from video instead of transcription")
                except Exception:
                    self.logger.exception("Failed to read subtitles, falling back to transcription")
                    video_data["transcription"] = ""

            if not video_data["transcription"]:
                if on_progress:
                    await on_progress(self.translator.t("recipe.create-progress.transcribing-audio-with-ai"))

                try:
                    transcription = await openai_service.transcribe_audio(video_data["audio"])
                except exceptions.RateLimitError:
                    raise
                except Exception as e:
                    raise exceptions.OpenAIServiceError(f"Failed to transcribe audio: {e}") from e
                if not transcription:
                    raise exceptions.OpenAIServiceError("No transcription returned from OpenAI")
                video_data["transcription"] = transcription

        if not video_data["transcription"]:
            self.logger.error("Could not extract a transcript (no data)")
            return None, None

        self.logger.debug(f"Transcription: {video_data['transcription'][:200]}...")
        prompt = openai_service.get_prompt("recipes.parse-recipe-video")

        message_parts = [
            f"Title: {video_data['title']}",
            f"Description: {video_data['description']}",
            f"Transcription: {video_data['transcription']}",
        ]

        if on_progress:
            await on_progress(self.translator.t("recipe.create-progress.creating-recipe-from-transcript-with-ai"))

        try:
            response = await openai_service.get_response(prompt, "\n".join(message_parts), response_schema=OpenAIRecipe)
        except exceptions.RateLimitError:
            raise
        except Exception as e:
            raise exceptions.OpenAIServiceError(f"Failed to extract recipe from video: {e}") from e

        if not response:
            raise exceptions.OpenAIServiceError("OpenAI returned an empty response when extracting recipe")

        recipe = Recipe(
            name=response.name,
            slug="",
            description=response.description,
            recipe_yield=response.recipe_yield,
            total_time=response.total_time,
            prep_time=response.prep_time,
            perform_time=response.perform_time,
            recipe_ingredient=[
                RecipeIngredient(title=ingredient.title, note=ingredient.text)
                for ingredient in response.ingredients
                if ingredient.text
            ],
            recipe_instructions=[
                RecipeStep(title=instruction.title, text=instruction.text)
                for instruction in response.instructions
                if instruction.text
            ],
            notes=[RecipeNote(title=note.title or "", text=note.text) for note in response.notes if note.text],
            image=video_data["thumbnail_url"] or None,
            org_url=self.url,
        )

        self.logger.info(f"Successfully extracted recipe from video: {video_data['title']}")
        return recipe, ScrapedExtras()


class RecipeScraperOpenGraph(ABCScraperStrategy):
    def can_scrape(self) -> bool:
        return bool(self.url or self.raw_html)

    async def get_html(self, url: str) -> str:
        return self.raw_html or await safe_scrape_html(url)

    def get_recipe_fields(self, html) -> dict | None:
        """
        Get the recipe fields from the Open Graph data.
        """

        def og_field(properties: dict, field_name: str) -> str:
            return next((val for name, val in properties if name == field_name), "")

        def og_fields(properties: list[tuple[str, str]], field_name: str) -> list[str]:
            return list({val for name, val in properties if name == field_name})

        base_url = get_base_url(html, self.url)
        data = extruct.extract(html, base_url=base_url, errors="log")
        try:
            properties = data["opengraph"][0]["properties"]
        except Exception:
            return None

        return {
            "name": og_field(properties, "og:title"),
            "description": og_field(properties, "og:description"),
            "image": og_field(properties, "og:image"),
            "recipeYield": "",
            "recipeIngredient": ["Could not detect ingredients"],
            "recipeInstructions": [{"text": "Could not detect instructions"}],
            "slug": slugify(og_field(properties, "og:title")),
            "orgURL": self.url or og_field(properties, "og:url"),
            "categories": [],
            "tags": og_fields(properties, "og:article:tag"),
            "dateAdded": None,
            "notes": [],
            "extras": [],
        }

    async def parse(
        self,
        on_progress: Callable[[str], Awaitable[None]] | None = None,
    ):
        """
        Parse a recipe from a given url.
        """

        if on_progress:
            await on_progress(self.translator.t("recipe.create-progress.creating-recipe-from-webpage-data"))

        html = await self.get_html(self.url)

        og_data = self.get_recipe_fields(html)

        if og_data is None:
            return None

        return Recipe(**og_data), ScrapedExtras()


class RecipeScraperColes(ABCScraperStrategy):
    """Custom Scraper Strategy for Coles Supermarkets Australia (coles.com.au).

    Coles embeds recipe data within Adobe Experience Manager (AEM) JSON blocks
    (`coles-onesite/components/...`) rather than standard Schema.org ld+json tags.

    GUIDE FOR FUTURE EXTENSION:
    To add support for another site using proprietary JSON (e.g. Woolworths or custom AEM sites):
    1. Inherit from ABCScraperStrategy.
    2. Match the target domain in `can_scrape()`.
    3. Extract and parse the embedded script tag in `parse()`.
    """

    def can_scrape(self) -> bool:
        if not self.url:
            return False
        return "coles.com.au" in self.url

    async def get_html(self, url: str) -> str:
        return self.raw_html or await safe_scrape_html(url)

    async def parse(  # noqa: C901
        self,
        on_progress: Callable[[str], Awaitable[None]] | None = None,
    ) -> tuple[Recipe, ScrapedExtras] | tuple[None, None]:
        if on_progress:
            await on_progress(self.translator.t("recipe.create-progress.extracting-recipe-data"))

        html = await self.get_html(self.url)
        if not html:
            return None, None

        soup = bs4.BeautifulSoup(html, "html.parser")
        script_data: dict[str, Any] | None = None

        for script in soup.find_all("script"):
            content = (script.string or script.get_text() or "").strip()
            if "coles-onesite" in content:
                try:
                    script_data = json.loads(content)
                    break
                except Exception:
                    pass

        if not script_data:
            self.logger.debug(f"Coles Scraper: No AEM JSON component found for {self.url}")
            return None, None

        def find_by_type(d: Any, target_type: str):
            if isinstance(d, dict):
                if d.get(":type") == target_type:
                    yield d
                for _k, v in d.items():
                    yield from find_by_type(v, target_type)
            elif isinstance(d, list):
                for item in d:
                    yield from find_by_type(item, target_type)

        # Extract Title
        title = "Coles Recipe"
        for comp in find_by_type(script_data, "coles-onesite/components/reciperemotepagenext"):
            if t := comp.get("title"):
                title = t
                break

        # Extract Ingredients with Categories
        ingredients: list[str] = []
        for comp in find_by_type(script_data, "coles-onesite/components/recipeingredients"):
            for category in comp.get("ingredientCategoryList", []):
                heading = category.get("heading", "").strip()
                if heading:
                    ingredients.append(f"[{heading}]")
                for ing in category.get("ingredients", []):
                    if isinstance(ing, str) and ing.strip():
                        ingredients.append(ing.strip())

        # Extract Method Steps
        steps: list[RecipeStep] = []
        for comp in find_by_type(script_data, "coles-onesite/components/recipemethod"):
            for step in comp.get("steps", []):
                if isinstance(step, dict) and (desc := step.get("description")):
                    steps.append(RecipeStep(title="", text=cleaner.clean_string(desc)))

        # Extract Prep / Cook Times & Yield
        prep_time = None
        cook_time = None
        servings = "1"
        for comp in find_by_type(script_data, "coles-onesite/components/recipedetails"):
            if prep_mins := comp.get("prepTimeAsMinutes"):
                prep_time = f"PT{prep_mins}M"
            if cook_mins := comp.get("cookTimeAsMinutes"):
                cook_time = f"PT{cook_mins}M"
            if s := comp.get("amountNumber"):
                servings = str(s)

        # Extract Description & Hero Image
        description = ""
        image_url = None
        og_desc = soup.find("meta", property="og:description")
        if og_desc and og_desc.get("content"):
            description = str(og_desc["content"])

        # Extract hero image from AEM JSON components
        for comp in find_by_type(script_data, "coles-onesite/components/imageComponent"):
            if img_path := comp.get("image"):
                image_url = img_path if img_path.startswith("http") else f"https://www.coles.com.au{img_path}"
                break

        if not image_url:
            for comp in find_by_type(script_data, "coles-onesite/components/recipesummary"):
                if img_path := comp.get("image"):
                    image_url = img_path if img_path.startswith("http") else f"https://www.coles.com.au{img_path}"
                    break

        if not image_url:
            og_img = soup.find("meta", property="og:image") or soup.find("meta", attrs={"name": "twitter:image"})
            if og_img and og_img.get("content"):
                img_val = str(og_img["content"])
                image_url = img_val if img_val.startswith("http") else f"https://www.coles.com.au{img_val}"

        if not ingredients and not steps:
            return None, None

        recipe = Recipe(
            name=cleaner.clean_string(title),
            slug=slugify(title),
            image=image_url,
            description=cleaner.clean_string(description),
            recipe_yield=servings,
            recipe_ingredient=cleaner.clean_ingredients(ingredients),
            recipe_instructions=steps,
            prep_time=prep_time,
            perform_time=cook_time,
            org_url=self.url,
        )

        return recipe, ScrapedExtras()


class RecipeScraperABC(ABCScraperStrategy):
    """Custom Scraper Strategy for ABC News Australia (abc.net.au).

    ABC News recipes are delivered via a Next.js application that embeds
    structured recipe payloads inside `<script id="__NEXT_DATA__">`, rather
    than traditional schema.org ld+json script tags.

    A secondary semantic HTML DOM fallback is included to parse
    `<section data-component="RecipeIngredients">` checkboxes and method steps
    if the Next.js payload format ever varies.
    """

    def can_scrape(self) -> bool:
        """Determines if the scraper strategy can handle the given URL."""
        if not self.url:
            return False
        return "abc.net.au" in self.url

    async def get_html(self, url: str) -> str:
        """Fetch HTML content safely, respecting rate limits and timeouts."""
        return self.raw_html or await safe_scrape_html(url)

    @staticmethod
    def _parse_time_string(time_str: str | None) -> str | None:
        """Convert time string representations (e.g. '15m', '40 minutes', '1 hour') to ISO-8601 duration."""
        if not time_str:
            return None
        time_lower = time_str.lower()
        hours = 0
        minutes = 0

        # Match patterns like '1 hour', '1h', '2 hours'
        if hr_match := re.search(r"(\d+)\s*(?:h|hr|hour)", time_lower):
            hours = int(hr_match.group(1))

        # Match patterns like '15m', '15 min', '15 minutes'
        if min_match := re.search(r"(\d+)\s*(?:m|min|minute)", time_lower):
            minutes = int(min_match.group(1))

        if hours > 0 and minutes > 0:
            return f"PT{hours}H{minutes}M"
        if hours > 0:
            return f"PT{hours}H"
        if minutes > 0:
            return f"PT{minutes}M"

        return None

    @staticmethod
    def _extract_text_nodes(node: Any) -> list[str]:
        """Recursively collect plain text content from ABC Next.js rich text descriptor objects."""
        texts: list[str] = []
        if isinstance(node, dict):
            if node.get("type") == "text" and "content" in node:
                texts.append(str(node["content"]))
            for child in node.get("children", []):
                texts.extend(RecipeScraperABC._extract_text_nodes(child))
        elif isinstance(node, list):
            for item in node:
                texts.extend(RecipeScraperABC._extract_text_nodes(item))
        return texts

    @staticmethod
    def _extract_hero_image(recipe_data: dict[str, Any]) -> str | None:
        """Extract high-resolution image URL from featuredMedia payload."""
        for media in recipe_data.get("featuredMedia", []):
            if not isinstance(media, dict):
                continue
            for crop in media.get("picture", {}).get("cropInfo", []):
                for val in crop.get("value", []):
                    if url := val.get("url"):
                        return url
        return None

    def _extract_from_next_data(  # noqa: C901
        self, soup: bs4.BeautifulSoup
    ) -> tuple[dict[str, Any], list[str], list[RecipeStep]] | None:
        """Extract recipe fields from the Next.js __NEXT_DATA__ JSON script tag."""
        script_tag = soup.find("script", id="__NEXT_DATA__")
        if not script_tag:
            return None

        try:
            content = script_tag.string or script_tag.get_text() or ""
            data = json.loads(content)
        except Exception:
            self.logger.debug(f"ABC Scraper: Failed to parse __NEXT_DATA__ JSON from {self.url}")
            return None

        doc = data.get("props", {}).get("pageProps", {}).get("document", {})
        recipe_data = doc.get("loaders", {}).get("recipepage", {}).get("recipe")
        if not recipe_data or not isinstance(recipe_data, dict):
            return None

        title = recipe_data.get("name") or doc.get("title") or ""
        description = recipe_data.get("description") or doc.get("synopsis") or ""
        yield_str = str(recipe_data.get("recipeYield") or "")

        stats = recipe_data.get("recipeStatsPrepared", {})
        prep_raw = stats.get("prepTime", {}).get("accessible") or stats.get("prepTime", {}).get("visual")
        cook_raw = stats.get("cookTime", {}).get("accessible") or stats.get("cookTime", {}).get("visual")
        if not yield_str:
            yield_str = str(stats.get("recipeYield") or "")

        prep_time = self._parse_time_string(prep_raw)
        cook_time = self._parse_time_string(cook_raw)

        # Extract Ingredients
        ingredients: list[str] = []
        ing_prepared = recipe_data.get("recipeIngredientsPrepared", {})
        for group in ing_prepared.get("ingredients", []):
            if not isinstance(group, dict):
                continue
            heading = group.get("heading") or group.get("title")
            if heading and str(heading).strip():
                ingredients.append(f"[{str(heading).strip()}]")
            for item in group.get("ingredients", []):
                if isinstance(item, str) and item.strip():
                    ingredients.append(item.strip())

        # Extract Steps
        steps: list[RecipeStep] = []
        inst_prepared = recipe_data.get("recipeInstructionsPrepared", {}).get("instructions", {})
        if isinstance(inst_prepared, dict) and "descriptor" in inst_prepared:

            def find_li(n: Any) -> None:
                if isinstance(n, dict):
                    if n.get("key") == "li":
                        text = "".join(self._extract_text_nodes(n)).strip()
                        if text:
                            steps.append(RecipeStep(title="", text=cleaner.clean_string(text)))
                    for c in n.get("children", []):
                        find_li(c)
                elif isinstance(n, list):
                    for i in n:
                        find_li(i)

            find_li(inst_prepared["descriptor"])

        image_url = self._extract_hero_image(recipe_data)

        metadata = {
            "title": title,
            "description": description,
            "yield": yield_str,
            "prep_time": prep_time,
            "cook_time": cook_time,
            "image": image_url,
        }

        return metadata, ingredients, steps

    def _extract_from_dom(self, soup: bs4.BeautifulSoup) -> tuple[dict[str, Any], list[str], list[RecipeStep]]:
        """Fallback extraction using semantic HTML tags and components."""
        title = ""
        if h1 := soup.find("h1"):
            title = h1.get_text(strip=True)

        description = ""
        if og_desc := soup.find("meta", property="og:description"):
            description = str(og_desc.get("content") or "")

        # Extract ingredients from DOM checkbox inputs or list items
        ingredients: list[str] = []
        ing_section = soup.find(
            lambda t: t.name in ["section", "div"] and "recipeingredients" in "".join(t.get("class", [])).lower()
        )
        if not ing_section:
            ing_h2 = soup.find(lambda t: t.name in ["h2", "h3"] and "ingredient" in t.get_text().lower())
            if ing_h2 and ing_h2.parent:
                ing_section = ing_h2.parent

        if ing_section:
            for cb in ing_section.find_all("input", type="checkbox"):
                name_attr = cb.get("name")
                label_text = cb.find_next_sibling("label")
                val = name_attr or (label_text.get_text(strip=True) if label_text else "")
                if val and val.strip():
                    ingredients.append(val.strip())

        # Extract instructions from Method section
        steps: list[RecipeStep] = []
        method_h2 = soup.find(lambda t: t.name in ["h2", "h3"] and "method" in t.get_text().lower())
        if method_h2:
            next_tag = method_h2.find_next_sibling()
            while next_tag and next_tag.name not in ["h1", "h2", "h3"]:
                for li in next_tag.find_all("li"):
                    txt = li.get_text(strip=True)
                    if txt:
                        steps.append(RecipeStep(title="", text=cleaner.clean_string(txt)))
                next_tag = next_tag.find_next_sibling()

        metadata = {
            "title": title,
            "description": description,
            "yield": "1",
            "prep_time": None,
            "cook_time": None,
            "image": None,
        }

        return metadata, ingredients, steps

    async def parse(  # noqa: C901
        self,
        on_progress: Callable[[str], Awaitable[None]] | None = None,
    ) -> tuple[Recipe, ScrapedExtras] | tuple[None, None]:
        """Parse an ABC News recipe page into Mealie's Recipe schema.

        Args:
            on_progress: Optional async progress callback.

        Returns:
            A tuple of (Recipe, ScrapedExtras) or (None, None) if extraction fails.
        """
        if on_progress:
            await on_progress(self.translator.t("recipe.create-progress.extracting-recipe-data"))

        html = await self.get_html(self.url)
        if not html:
            return None, None

        soup = bs4.BeautifulSoup(html, "html.parser")

        # 1. Attempt primary extraction from Next.js payload
        extracted = self._extract_from_next_data(soup)

        # 2. Fallback to semantic DOM extraction if needed
        if not extracted or (not extracted[1] and not extracted[2]):
            metadata, ingredients, steps = self._extract_from_dom(soup)
        else:
            metadata, ingredients, steps = extracted

        if not ingredients and not steps:
            self.logger.debug(f"ABC Scraper: Unable to extract ingredients or steps from {self.url}")
            return None, None

        # Fallback image extraction from OpenGraph tags if not provided in JSON
        image_url = metadata.get("image")
        if not image_url:
            og_img = soup.find("meta", property="og:image") or soup.find("meta", attrs={"name": "twitter:image"})
            if og_img and og_img.get("content"):
                image_url = str(og_img["content"])

        title = metadata.get("title") or "ABC Recipe"

        recipe = Recipe(
            name=cleaner.clean_string(title),
            slug=slugify(title),
            image=image_url,
            description=cleaner.clean_string(metadata.get("description", "")),
            recipe_yield=metadata.get("yield") or "1",
            recipe_ingredient=cleaner.clean_ingredients(ingredients),
            recipe_instructions=steps,
            prep_time=metadata.get("prep_time"),
            perform_time=metadata.get("cook_time"),
            org_url=self.url,
        )

        return recipe, ScrapedExtras()
