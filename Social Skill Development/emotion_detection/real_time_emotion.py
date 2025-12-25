import cv2
import torch
import numpy as np
from transformers import AutoImageProcessor, AutoModelForImageClassification
from PIL import Image


class EngagementEstimator:
    """Estimates student engagement level from video frames"""
    
    def __init__(self):
        """Initialize the engagement estimator"""
        try:
            model_name = "trpakov/vit-face-expression"
            self.processor = AutoImageProcessor.from_pretrained(model_name)
            self.model = AutoModelForImageClassification.from_pretrained(model_name)
            self.initialized = True
            print("✅ EngagementEstimator initialized")
        except Exception as e:
            print(f"⚠️ EngagementEstimator init failed: {e}")
            self.initialized = False
    
    def analyze_frame(self, frame):
        """
        Analyze a video frame for engagement metrics
        
        Args:
            frame: OpenCV frame (BGR format)
            
        Returns:
            dict with engagement_level and engagement_score
        """
        if not self.initialized:
            return {"engagement_level": None, "engagement_score": None}
        
        try:
            # Convert frame to PIL Image
            img = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
            inputs = self.processor(images=img, return_tensors="pt")
            
            with torch.no_grad():
                outputs = self.model(**inputs)
                probs = torch.softmax(outputs.logits, dim=1)[0].numpy()
            
            labels = self.model.config.id2label
            top_idx = np.argmax(probs)
            emotion = labels[top_idx]
            confidence = float(probs[top_idx])
            
            # Map emotions to engagement levels
            engagement_mapping = {
                "happy": "High",
                "surprise": "High",
                "neutral": "Medium",
                "sad": "Low",
                "fear": "Low",
                "disgust": "Low",
                "anger": "Low"
            }
            
            # Calculate engagement score (0-100)
            emotion_lower = emotion.lower()
            engagement_level = engagement_mapping.get(emotion_lower, "Medium")
            
            # Score based on emotion and confidence
            if engagement_level == "High":
                engagement_score = 70 + (confidence * 30)
            elif engagement_level == "Medium":
                engagement_score = 40 + (confidence * 30)
            else:  # Low
                engagement_score = confidence * 40
            
            return {
                "engagement_level": engagement_level,
                "engagement_score": round(engagement_score, 2),
                "emotion": emotion,
                "confidence": round(confidence, 2)
            }
            
        except Exception as e:
            print(f"⚠️ Frame analysis error: {e}")
            return {"engagement_level": None, "engagement_score": None}
    
    def close(self):
        """Clean up resources"""
        pass


def start_emotion_detection(duration=None):
    """
    Start real-time emotion detection
    
    Args:
        duration: Optional duration in seconds to run detection. If None, runs until 'q' is pressed.
    """
    import time
    
    model_name = "trpakov/vit-face-expression"
    processor = AutoImageProcessor.from_pretrained(model_name)
    model = AutoModelForImageClassification.from_pretrained(model_name)

    cap = cv2.VideoCapture(0)

    if not cap.isOpened():
        print("❌ Camera not detected")
        return

    print(f"📷 Emotion Detection Started (Press Q to quit camera{' or wait ' + str(duration) + 's' if duration else ''})")

    start_time = time.time() if duration else None

    while True:
        # Check duration timeout if specified
        if duration and start_time and (time.time() - start_time) >= duration:
            print(f"⏱️  Duration of {duration}s reached, stopping emotion detection")
            break
            
        ret, frame = cap.read()
        if not ret:
            break

        img = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
        inputs = processor(images=img, return_tensors="pt")

        with torch.no_grad():
            outputs = model(**inputs)
            probs = torch.softmax(outputs.logits, dim=1)[0].numpy()

        labels = model.config.id2label
        top_idx = np.argmax(probs)
        emotion = labels[top_idx]

        cv2.putText(frame, emotion, (20, 40),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0,255,0), 2)

        cv2.imshow("Emotion Detection", frame)

        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

    cap.release()
    cv2.destroyAllWindows()
