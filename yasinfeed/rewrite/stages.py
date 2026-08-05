import re
from abc import ABC, abstractmethod
from typing import List
from yasinfeed.models import Article
from yasinfeed.rewrite.pipeline_providers import BaseProvider

class BaseStage(ABC):
    """
    Abstract base class for all processing stages in the Content Pipeline.
    """
    @abstractmethod
    def process(self, article: Article) -> Article:
        """
        Processes and potentially modifies the Article, then returns it.
        """
        pass


class SanitizationStage(BaseStage):
    """
    Removes HTML tags and normalizes whitespace/newlines from article title and content.
    """
    def process(self, article: Article) -> Article:
        # Regex to strip HTML tags
        html_re = re.compile(r'<[^>]+>')

        # Clean title
        if article.title:
            cleaned_title = html_re.sub('', article.title)
            # Normalize whitespace
            cleaned_title = ' '.join(cleaned_title.split())
            article.title = cleaned_title

        # Clean content
        if article.content:
            cleaned_content = html_re.sub('', article.content)
            # Standardize duplicate newlines and whitespace
            lines = [ ' '.join(line.split()) for line in cleaned_content.splitlines() ]
            cleaned_content = '\n'.join([ line for line in lines if line ])
            article.content = cleaned_content

        return article


class RewriteStage(BaseStage):
    """
    Uses the configured BaseProvider to perform content rewriting and summarization.
    Updates rewritten_content and sets rewrite_status to 'completed'.
    """
    def __init__(self, provider: BaseProvider):
        self.provider = provider

    def process(self, article: Article) -> Article:
        rewritten = self.provider.rewrite(article.title, article.content)
        article.rewritten_content = rewritten
        article.rewrite_status = "completed"
        return article


class TranslationStage(BaseStage):
    """
    Simulates content translation (e.g. into English/Persian).
    Appends a simulation tag or performs a mock translation if needed.
    """
    def __init__(self, target_lang: str = "en"):
        self.target_lang = target_lang

    def process(self, article: Article) -> Article:
        if article.rewritten_content:
            text = article.rewritten_content
            # Simulating translation by prefixing or appending target language information
            translated = f"[Translated to {self.target_lang.upper()}]:\n{text}"
            article.rewritten_content = translated
        return article


class MetadataTaggingStage(BaseStage):
    """
    Analyzes content to dynamically assign classifications or categories/tags.
    In standard Articles, tags are not an explicit first-class field, but we can append them
    or perform classification keywords lookup. We can store metadata if we extend model,
    or we can append them directly to the rewritten content as hash tags, or print metadata logs.
    Let's add generic keywords detection and append hashtags to the rewritten_content.
    """
    def __init__(self, keywords_map: dict = None):
        # Default keywords mapping
        self.keywords_map = keywords_map or {
            "ai": ["ai", "artificial intelligence", "machine learning", "llm", "ollama"],
            "tech": ["technology", "software", "development", "programming", "python"],
            "news": ["announcement", "release", "launch", "breaking"]
        }

    def process(self, article: Article) -> Article:
        text_to_analyze = f"{article.title} {article.content}".lower()
        extracted_tags = []
        for tag, keywords in self.keywords_map.items():
            for kw in keywords:
                if kw in text_to_analyze:
                    extracted_tags.append(tag)
                    break

        if extracted_tags and article.rewritten_content:
            hashtags = " ".join([f"#{t}" for t in extracted_tags])
            article.rewritten_content = f"{article.rewritten_content}\n\nTags: {hashtags}"

        return article
