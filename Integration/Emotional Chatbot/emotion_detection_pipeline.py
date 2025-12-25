from sequence_model_handler import SequenceModelHandler
from transformers import pipeline
import torch, json, os, re
from typing import Dict, Tuple, List
from logger import Logger
import warnings

warnings.filterwarnings("ignore")
logger = Logger(name="Enhanced Emotion Detection", log_file_needed=True, log_file='Logs/emotion_detection.log', level='DEV')

def _select_device(prefer_mps: bool = True) -> torch.device:
    force_cpu = os.getenv("FORCE_CPU", "0") == "1"
    if prefer_mps and not force_cpu and torch.backends.mps.is_available():
        return torch.device("mps")
    return torch.device("cpu")

class EmotionDetector:
    def __init__(self, model_name="out/deberta_v3_base_emotion", label_file_path=None, min_conf: float = 0.45, prefer_mps: bool = True):
        logger.debug(f"Initializing EnhancedEmotionDetector with model: {model_name}")
        try:
            self.device = _select_device(prefer_mps=prefer_mps)
            logger.debug(f"Using device: {self.device}")

            self.model_handler = SequenceModelHandler(model_name)
            loaded_model, corresponding_tokenizer = self.model_handler.load_sequence_model()

            self.emotion_classifier = pipeline(
                task="text-classification",
                model=loaded_model,
                tokenizer=corresponding_tokenizer,
                return_all_scores=True,
            )

            self.min_conf = float(min_conf)

            self.labels = None
            if label_file_path and os.path.exists(label_file_path):
                with open(label_file_path, "r") as f:
                    meta = json.load(f)
                id2label = meta.get("id2label")
                if isinstance(id2label, dict):
                    self.labels = [id2label.get(str(i), id2label.get(i)) for i in range(len(id2label))]
            if self.labels is None and hasattr(loaded_model, "config") and getattr(loaded_model.config, "id2label", None):
                id2label = loaded_model.config.id2label
                if isinstance(id2label, dict) and len(id2label) > 0:
                    self.labels = [id2label.get(i, id2label.get(str(i))) for i in range(len(id2label))]
            if self.labels:
                logger.debug(f"Loaded label set: {self.labels}")

            self.educational_patterns = {
                'frustration_learning': [
                    r"(?i)(can't|cannot|don't know|don't understand|too hard|difficult|confused|stuck)",
                    r"(?i)(hate|stupid|dumb|impossible|give up|quit)"
                ],
                'anxiety_learning': [
                    r"(?i)(worried|scared|nervous|afraid|anxious|test|exam|grade)",
                    r"(?i)(what if|don't want to|scared to try)"
                ],
                'confidence_low': [
                    r"(?i)(not good at|bad at|terrible at|can't do|not smart)",
                    r"(?i)(everyone else|better than me|not like others)"
                ],
                'engagement_positive': [
                    r"(?i)(love|like|fun|cool|awesome|amazing|interesting)",
                    r"(?i)(want to learn|excited|can't wait|show me)"
                ],
                'adhd_indicators': [
                    r"(?i)(bored|boring|restless|can't sit|need to move|distracted)",
                    r"(?i)(forgot|keep forgetting|lost focus|mind wandering)"
                ],
                'dyslexia_indicators': [
                    r"(?i)(words are|letters are|jumbled|mixed up|backwards|blurry)",
                    r"(?i)(hard to read|can't see|words moving|letters dancing)"
                ]
            }

            logger.debug("Enhanced emotion detection model loaded successfully")

        except Exception as e:
            logger.error(f"Failed to load enhanced emotion detection model: {str(e)}")
            raise

    def detect_educational_emotion(self, text: str, context: Dict = None) -> Dict:
        logger.debug(f"Starting enhanced emotion detection for text: '{text[:50]}...'")
        if not text or not text.strip():
            logger.warning("Empty text provided")
            return {
                'primary_emotion': 'neutral',
                'confidence': 0.0,
                'educational_context': 'unknown',
                'special_needs_indicators': [],
                'recommended_approach': 'standard'
            }
        try:
            base_emotion, confidence = self._detect_base_emotion(text)
            educational_context = self._analyze_educational_context(text)
            special_needs = self._detect_special_needs_indicators(text)
            result = {
                'primary_emotion': base_emotion,
                'confidence': confidence,
                'educational_context': educational_context,
                'special_needs_indicators': special_needs,
                'recommended_approach': self._get_recommended_approach(base_emotion, educational_context, special_needs),
                'context_factors': context or {}
            }
            logger.debug(f"Enhanced emotion analysis complete: {result}")
            return result
        except Exception as e:
            logger.error(f"Error in enhanced emotion detection: {str(e)}")
            return {
                'primary_emotion': 'neutral',
                'confidence': 0.0,
                'educational_context': 'error',
                'special_needs_indicators': [],
                'recommended_approach': 'supportive'
            }

    def _normalize_label(self, label: str) -> str:
        m = {
            "joy": "joy", "happiness": "joy", "happy": "joy",
            "sadness": "sadness", "sad": "sadness",
            "anger": "anger", "angry": "anger",
            "fear": "fear", "anxious": "fear", "anxiety": "fear",
            "surprise": "surprise", "surprised": "surprise",
            "disgust": "disgust", "disgusted": "disgust",
            "neutral": "neutral", "other": "neutral"
        }
        return m.get(label.lower(), label.lower())

    def _detect_base_emotion(self, text: str) -> Tuple[str, float]:
        preds = self.emotion_classifier(text)
        scores = preds[0] if isinstance(preds, list) and len(preds) > 0 and isinstance(preds[0], list) else preds
        if not isinstance(scores, list) or len(scores) == 0:
            return "neutral", 0.0
        best = max(scores, key=lambda x: x["score"])
        label = self._normalize_label(best["label"])
        score = float(best["score"])
        if score < self.min_conf:
            return "neutral", score
        return label, score

    def _analyze_educational_context(self, text: str) -> str:
        for context_type, patterns in self.educational_patterns.items():
            for pattern in patterns:
                if re.search(pattern, text):
                    logger.debug(f"Educational context detected: {context_type}")
                    return context_type
        return 'general'

    def _detect_special_needs_indicators(self, text: str) -> List[str]:
        indicators = []
        for pattern in self.educational_patterns['adhd_indicators']:
            if re.search(pattern, text):
                indicators.append('adhd_pattern'); break
        for pattern in self.educational_patterns['dyslexia_indicators']:
            if re.search(pattern, text):
                indicators.append('dyslexia_pattern'); break
        return indicators

    def _get_recommended_approach(self, emotion: str, context: str, indicators: List[str]) -> str:
        if 'dyslexia_pattern' in indicators:
            return 'dyslexia_supportive'
        elif 'adhd_pattern' in indicators:
            return 'adhd_supportive'
        elif context in ['frustration_learning', 'anxiety_learning']:
            return 'learning_supportive'
        elif context == 'confidence_low':
            return 'confidence_building'
        elif context == 'engagement_positive':
            return 'encouraging'
        else:
            return 'standard'

emotion_detector = EmotionDetector(
    model_name="out/deberta_v3_base_emotion",
    label_file_path=os.path.join("out/deberta_v3_base_emotion","labels.json"),
    min_conf=0.45,
    prefer_mps=True
)

def detect_enhanced_emotion(text: str, context: Dict = None) -> Dict:
    return emotion_detector.detect_educational_emotion(text, context)
