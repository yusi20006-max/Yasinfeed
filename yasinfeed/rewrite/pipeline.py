import logging
from typing import List
from yasinfeed.models import Article
from yasinfeed.rewrite.stages import BaseStage

import time
from datetime import datetime, timezone

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

        # Initialize pipeline metadata tracking
        if not hasattr(article, "pipeline_metadata") or article.pipeline_metadata is None:
            article.pipeline_metadata = {}

        stages_executed = []
        failures = []
        start_time = time.time()

        for stage in self.stages:
            stage_name = stage.__class__.__name__
            self.logger.debug("Executing stage: %s", stage_name)
            stages_executed.append(stage_name)
            try:
                article = stage.process(article)
            except Exception as e:
                critical = getattr(stage, "critical", True)
                err_msg = str(e)
                self.logger.warning("Error in stage %s (critical=%s): %s", stage_name, critical, err_msg)

                # Record failure details
                failures.append({
                    "stage": stage_name,
                    "error": err_msg,
                    "critical": critical
                })

                if critical:
                    self.logger.error("Critical stage %s failed. Aborting pipeline.", stage_name, exc_info=True)
                    article.rewrite_status = "failed"

                    # Store run metrics on failure
                    duration = time.time() - start_time
                    article.pipeline_metadata["pipeline_run"] = {
                        "stages_executed": stages_executed,
                        "failures": failures,
                        "duration_seconds": round(duration, 4),
                        "completed_at": datetime.now(timezone.utc).isoformat()
                    }
                    raise e
                else:
                    self.logger.info("Bypassing non-critical stage %s failure. Executing fallback.", stage_name)
                    try:
                        article = stage.fallback(article, e)
                    except Exception as fallback_err:
                        self.logger.error("Fallback for stage %s failed: %s", stage_name, fallback_err, exc_info=True)

        # Store run metrics on successful completion (or partial with bypassed stages)
        duration = time.time() - start_time
        article.pipeline_metadata["pipeline_run"] = {
            "stages_executed": stages_executed,
            "failures": failures,
            "duration_seconds": round(duration, 4),
            "completed_at": datetime.now(timezone.utc).isoformat()
        }

        self.logger.info("Pipeline processing completed for article: %s", article.id)
        return article
