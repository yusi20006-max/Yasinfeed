import re
from typing import Dict, Any, List

class ContentIntelligenceEngine:
    """
    A pure-Python, provider-agnostic, zero-dependency Content Intelligence Engine.
    Exclusively produces structured analysis (metadata, language, readability,
    sentiment, keywords, categories, and agent recommendations) without rewriting content.
    """
    def __init__(self):
        # Curated standard sentiment word lists
        self.positive_words = {
            "amazing", "great", "excellent", "awesome", "good", "beautiful", "successful",
            "improve", "innovative", "excited", "progress", "advance", "breakthrough",
            "launch", "release", "win", "achievement", "benefit", "powerful", "growth",
            "high", "positive", "strong", "optimize", "robust", "healthy"
        }
        self.negative_words = {
            "bad", "fail", "error", "broken", "critical", "severe", "issue", "crash",
            "bug", "terrible", "poor", "worse", "decrease", "decline", "unsuccessful",
            "harmful", "negative", "weak", "disaster", "vulnerability", "risk", "danger",
            "loss", "failed", "unstable", "warning"
        }

        # Integrated stop words for topic extraction
        self.en_stop_words = {
            "the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for", "with",
            "by", "of", "from", "is", "are", "was", "were", "be", "been", "this", "that",
            "it", "its", "they", "them", "their", "we", "us", "our", "you", "your", "i",
            "my", "me", "he", "him", "his", "she", "her", "has", "have", "had", "do",
            "does", "did", "as", "if", "then", "else", "not", "no", "about", "which",
            "there", "there's", "hasn't", "haven't", "can", "can't", "will", "would",
            "should", "could", "all", "any", "both", "each", "few", "more", "most", "other",
            "some", "such", "than", "too", "very", "s", "t", "just", "now", "new"
        }
        self.fa_stop_words = {
            "از", "به", "با", "در", "تا", "که", "این", "آن", "یک", "را", "و", "یا", "اما",
            "برای", "شد", "بود", "است", "هست", "می", "کند", "کنند", "کرد", "کردند", "شدن",
            "داشت", "دارد", "هم", "همه", "روی", "زیر", "بین", "پیش", "پس", "چون", "اگر",
            "حتی", "باید", "شاید", "بنابر", "بنابراین", "دیگر", "بر", "خود", "وی", "آنها"
        }

        # Urgency/Priority signal words
        self.urgency_weights = {
            "breaking": 0.4,
            "critical": 0.5,
            "vulnerability": 0.6,
            "breakthrough": 0.3,
            "alert": 0.4,
            "urgent": 0.5,
            "security": 0.3,
            "exploit": 0.5,
            "warning": 0.3,
            "hotfix": 0.4,
            "emergency": 0.6
        }

    def detect_language(self, text: str) -> str:
        """
        Detects primary language based on character distribution and stop words.
        Returns 'fa' for Persian/Arabic, and 'en' for English/other.
        """
        if not text:
            return "en"

        # Check for Persian/Arabic alphabet characters
        persian_char_re = re.compile(r'[\u0600-\u06FF\u0750-\u077F\uFB50-\uFDFF\uFE70-\uFEFF]')
        persian_chars = len(persian_char_re.findall(text))
        total_chars = len(text)

        if total_chars > 0 and (persian_chars / total_chars) > 0.15:
            return "fa"

        # Fallback check based on stop words count
        words = [w.strip().lower() for w in re.split(r'\W+', text) if w]
        fa_hits = sum(1 for w in words if w in self.fa_stop_words)
        en_hits = sum(1 for w in words if w in self.en_stop_words)

        if fa_hits > en_hits:
            return "fa"
        return "en"

    def analyze_sentiment(self, text: str) -> Dict[str, Any]:
        """
        Calculates a continuous lexicon-based sentiment score and maps to a label.
        Score is in range [-1.0, 1.0].
        """
        if not text:
            return {"score": 0.0, "label": "neutral"}

        words = [w.strip().lower() for w in re.split(r'\W+', text) if w]
        if not words:
            return {"score": 0.0, "label": "neutral"}

        pos_count = sum(1 for w in words if w in self.positive_words)
        neg_count = sum(1 for w in words if w in self.negative_words)

        diff = pos_count - neg_count
        total = pos_count + neg_count

        if total == 0:
            score = 0.0
        else:
            # Normalized score based on difference
            score = diff / total

        if score > 0.15:
            label = "positive"
        elif score < -0.15:
            label = "negative"
        else:
            label = "neutral"

        return {
            "score": round(score, 2),
            "label": label,
            "details": {
                "positive_hits": pos_count,
                "negative_hits": neg_count
            }
        }

    def analyze_readability(self, text: str) -> Dict[str, Any]:
        """
        Calculates word counts, sentence counts, and estimated reading time.
        """
        if not text:
            return {
                "words_count": 0,
                "sentences_count": 0,
                "avg_word_length": 0.0,
                "estimated_reading_time_seconds": 0
            }

        words = [w.strip() for w in re.split(r'\s+', text) if w]
        words_count = len(words)

        # Splitting by common sentence ending marks
        sentences = [s.strip() for s in re.split(r'[.!?\u06D4]', text) if s.strip()]
        sentences_count = max(len(sentences), 1 if words_count > 0 else 0)

        total_word_len = sum(len(w) for w in words)
        avg_word_length = round(total_word_len / words_count, 1) if words_count > 0 else 0.0

        # Assuming average adult reading speed of 200 words per minute (wpm)
        reading_time_seconds = int((words_count / 200) * 60)
        # Ensure minimum 1 second reading time if there are words
        if words_count > 0 and reading_time_seconds == 0:
            reading_time_seconds = 1

        return {
            "words_count": words_count,
            "sentences_count": sentences_count,
            "avg_word_length": avg_word_length,
            "estimated_reading_time_seconds": reading_time_seconds
        }

    def extract_topics(self, text: str, lang: str = "en", limit: int = 5) -> List[str]:
        """
        Extracts high-quality topics/keywords by filtering stop words and ranking term frequency.
        """
        if not text:
            return []

        # Remove numbers and convert to lower case
        clean_text = text.lower()
        words = [w.strip() for w in re.split(r'\W+', clean_text) if w and not w.isdigit()]

        stop_words = self.fa_stop_words if lang == "fa" else self.en_stop_words

        # Filter out stop words and short terms
        filtered_words = [w for w in words if w not in stop_words and len(w) > 2]

        # Count frequencies
        freq: Dict[str, int] = {}
        for w in filtered_words:
            freq[w] = freq.get(w, 0) + 1

        # Sort by frequency descending
        sorted_topics = sorted(freq.items(), key=lambda x: x[1], reverse=True)
        return [topic for topic, _ in sorted_topics[:limit]]

    def evaluate_agent_signals(self, text: str, sentiment_score: float) -> Dict[str, Any]:
        """
        Computes priority level and recommends agent dispatch action.
        Priority is range [0.0, 1.0].
        """
        if not text:
            return {
                "priority": 0.0,
                "relevance_score": 0.0,
                "dispatch_route": "standard_processing"
            }

        text_lower = text.lower()
        base_priority = 0.2

        # 1. Add weights based on urgency triggers
        urgency_score = 0.0
        matched_triggers = []
        for word, weight in self.urgency_weights.items():
            if word in text_lower:
                urgency_score += weight
                matched_triggers.append(word)

        # Cap urgency score impact
        urgency_score = min(urgency_score, 0.5)

        # 2. Impact of extreme sentiment
        sentiment_impact = abs(sentiment_score) * 0.2

        priority = base_priority + urgency_score + sentiment_impact
        priority = round(min(priority, 1.0), 2)

        # Recommending dispatch action
        if priority >= 0.7:
            dispatch_route = "publish_immediately"
        elif priority >= 0.4:
            dispatch_route = "review_required"
        else:
            dispatch_route = "standard_processing"

        # Basic confidence calculation based on matching attributes
        confidence = round(0.5 + (urgency_score * 0.5) + (sentiment_impact * 0.5), 2)

        return {
            "priority": priority,
            "relevance_score": round(min(0.3 + urgency_score + sentiment_impact, 1.0), 2),
            "dispatch_route": dispatch_route,
            "confidence": confidence,
            "matched_triggers": matched_triggers
        }

    def analyze(self, title: str, content: str) -> Dict[str, Any]:
        """
        Run the complete semantic analysis and returns structured metadata.
        """
        full_text = f"{title or ''} {content or ''}"
        lang = self.detect_language(full_text)
        sentiment = self.analyze_sentiment(full_text)
        readability = self.analyze_readability(full_text)
        topics = self.extract_topics(full_text, lang=lang)
        agent_signals = self.evaluate_agent_signals(full_text, sentiment["score"])

        return {
            "language": lang,
            "sentiment": sentiment,
            "readability": readability,
            "topics": topics,
            "agent_signals": agent_signals
        }
