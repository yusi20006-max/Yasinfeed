# Content Pipeline & Content Intelligence Layer

This document details the architecture, capabilities, and extensibility of YasinFeed's advanced sequential content processing pipeline and the Content Intelligence Layer.

---

## 1. Sequential Processing Pipeline (`ContentPipeline`)

The **Content Pipeline Engine** (`yasinfeed/rewrite/pipeline.py`) implements a sequential, stage-based transformation pattern for articles. By separating concerns into self-contained processing steps subclassing `BaseStage`, the engine keeps content transformation clean, decoupled, and easy to extend.

### Default Processing Order
1. **`SanitizationStage`**: Strips raw HTML tags and normalizes whitespace/newlines to present a uniform text representation.
2. **`RewriteStage`**: Interacts with the configured AI or dummy provider to summarize and optimize the content.
3. **`TranslationStage`**: Translates/Localizes the summary text into target output languages (e.g., English, Persian).
4. **`ContentAnalysisStage`**: Executes advanced multi-metric pure-Python evaluations (sentiment, readability, topics) and populates `pipeline_metadata`.
5. **`MetadataTaggingStage`**: Detects and appends hash tags or custom classifications dynamically to enrich outputs.

---

## 2. Fault Tolerance & Data Flow Reliability

To prevent auxiliary or external stages (like translation or third-party sentiment APIs) from interrupting the core polling flow, we implement **stage failure isolation**:

### The `critical` Flag
- Each processing stage subclasses `BaseStage` and exposes a `critical` boolean property (defaults to `True`).
- Core stages (e.g. `SanitizationStage`, `RewriteStage`) are marked `critical=True`. If they throw an exception, the pipeline fails, sets the article status to `failed`, and propagates the error.
- Enrichment or external stages (e.g. `TranslationStage`, `ContentAnalysisStage`, `MetadataTaggingStage`) are marked `critical=False`.
- If a non-critical stage encounters an unexpected exception, the pipeline catches the error, logs a detailed warning, records the failure context in the article's execution metadata, and continues safely executing subsequent stages.

### Custom Stage Fallbacks
- Stages can override `fallback(self, article, exception)` to gracefully roll back or substitute attributes when a stage processing error occurs.

---

## 3. Content Intelligence Layer

The Content Intelligence Layer (`yasinfeed/rewrite/intelligence.py`) provides zero-dependency, pure-Python semantic evaluation and classification of articles. It generates structured indicators designed for consumer PWAs and automated `Yasin-Agent` decision-making workflows.

### Analytics Capabilities

#### A. Lexicon-Based Sentiment Analysis
- Uses an embedded, optimized lexicon mapping positive and negative terms.
- Produces a continuous sentiment score normalized between `-1.0` (extremely negative) and `1.0` (extremely positive).
- Categorizes sentiment into `"positive"`, `"neutral"`, or `"negative"`.

#### B. Readability & Complexity Profiling
- Counts characters, words, and sentences.
- Calculates complexity indices (e.g., average word length, sentence density).
- Estimates Reading Time assuming a standard reading speed of 200 words-per-minute (wpm).

#### C. TF-IDF-Based Keyword & Topic Extraction
- Strips a comprehensive, predefined set of common stop words (e.g., "the", "and", "but").
- Evaluates word frequencies to identify and rank top terms representing the article's core themes.

#### D. Language Checking
- Detects whether the predominant content is English, Persian/Arabic, or other based on alphabet distributions and stop word matching.

#### E. Yasin-Agent Signals & Decision Markers
- **Urgency / Priority Score (0.0 to 1.0):** Dynamically computed based on presence of breaking-news keywords, extreme sentiment, or topic significance.
- **Dispatch Route Recommendation:** Suggests whether the article should be automatically published (high-confidence match), routed for human review, or ignored.

---

## 4. Execution Metrics & Metadata Schema

Pipeline execution stats and intelligence metrics are preserved inside the article's `pipeline_metadata` field, which is fully exposed via the `/api/articles` REST endpoints.

### Example JSON Payload:
```json
"pipeline_metadata": {
  "pipeline_run": {
    "stages_executed": ["SanitizationStage", "RewriteStage", "TranslationStage", "ContentAnalysisStage", "MetadataTaggingStage"],
    "failures": [],
    "duration_seconds": 0.045,
    "completed_at": "2026-08-07T12:00:00.123456"
  },
  "intelligence": {
    "language": "en",
    "sentiment": {
      "score": 0.45,
      "label": "positive"
    },
    "readability": {
      "words_count": 120,
      "sentences_count": 6,
      "avg_word_length": 5.4,
      "estimated_reading_time_seconds": 36
    },
    "topics": ["artificial intelligence", "python", "backend"],
    "agent_signals": {
      "priority": 0.85,
      "dispatch_route": "publish_immediately",
      "relevance_score": 0.92
    }
  }
}
```
This telemetry ensures that any orchestrating system or future agent workflow has complete visibility into processed content semantics.
