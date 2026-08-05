import logging
from typing import List
from yasinfeed.models import Article
from yasinfeed.rewrite.stages import BaseStage

class ContentPipeline:
    """
    Orchestrates the sequential execution of processing stages on an Article.
    Provides logging and stage management interfaces.
    """
    def __init__(self, stages: List[BaseStage] = None):
        self.stages: List[BaseStage] = stages or []
        self.logger = logging.getLogger("yasinfeed.rewrite.pipeline")

    def add_stage(self, stage: BaseStage) -> None:
        """Adds a processing stage to the pipeline."""
        self.stages.append(stage)
        self.logger.debug("Added stage: %s", stage.__class__.__name__)

    def process(self, article: Article) -> Article:
        """Runs the article through all registered processing stages in order."""
        self.logger.info("Executing Content Pipeline on article: %s (ID: %s)", article.title, article.id)
        for stage in self.stages:
            stage_name = stage.__class__.__name__
            self.logger.debug("Executing stage: %s", stage_name)
            try:
                article = stage.process(article)
            except Exception as e:
                self.logger.error("Error executing stage %s: %s", stage_name, e, exc_info=True)
                # We can either raise the error, fail/skip, or continue.
                # Continuing lets other non-dependent stages run, but rewrite stage failure is critical.
                # To be robust, let's set rewrite_status to 'failed' and propagate the exception.
                article.rewrite_status = "failed"
                raise e
        self.logger.info("Pipeline processing completed for article: %s", article.id)
        return article
