"""
Multimodal Analyzer - Analyze images and videos from posts using real AI/ML models
"""

from typing import Dict
from PIL import Image
import requests
from io import BytesIO
import os
import tempfile

# Optional imports - will be imported when needed
try:
    import torch
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False

try:
    from transformers import CLIPProcessor, CLIPModel, BlipProcessor, BlipForConditionalGeneration
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False

# Note: DeepFace and EasyOCR removed due to dependency conflicts
# Future versions can integrate them in separate environment if needed

IMPORTS_AVAILABLE = TORCH_AVAILABLE and TRANSFORMERS_AVAILABLE


class MultimodalAnalyzer:
    """
    Analyzes images and videos to extract emotional content using AI/ML models
    """

    def __init__(self):
        if not IMPORTS_AVAILABLE:
            self.enabled = False
            print("⚠ Multimodal analysis disabled - AI/ML packages not available")
            self.clip_model = None
            self.clip_processor = None
            self.blip_processor = None
            self.blip_model = None
            return

        self.enabled = True  # Enable real AI models
        print("🤖 Initializing multimodal AI models (CLIP + BLIP)...")

        # Emotion texts for CLIP analysis
        self.emotion_texts = [
            "a happy person", "a sad person", "an angry person",
            "a fearful person", "a surprised person", "a neutral person"
        ]

        # Initialize CLIP for image-text alignment
        try:
            self.clip_model = CLIPModel.from_pretrained("openai/clip-vit-base-patch32")
            self.clip_processor = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch32")
            print("✓ CLIP model loaded")
        except Exception as e:
            print(f"⚠ CLIP model failed to load: {e}")
            self.clip_model = None
            self.clip_processor = None

        # Initialize BLIP for image captioning
        try:
            self.blip_processor = BlipProcessor.from_pretrained("Salesforce/blip-image-captioning-base")
            self.blip_model = BlipForConditionalGeneration.from_pretrained("Salesforce/blip-image-captioning-base")
            print("✓ BLIP model loaded")
        except Exception as e:
            print(f"⚠ BLIP model failed to load: {e}")
            self.blip_processor = None
            self.blip_model = None

        # Check if we have at least basic multimodal capabilities
        if self.clip_model or self.blip_model:
            print("✓ Basic multimodal analysis available (CLIP/BLIP)")
        else:
            print("⚠ No multimodal models available - text-only analysis")

    def analyze_image(self, image_url: str) -> Dict:
        """
        Analyze emotion from image using CLIP, BLIP, and facial recognition
        """
        if not self.enabled:
            return self._placeholder_response()

        try:
            # Download image
            response = requests.get(image_url, timeout=10)
            response.raise_for_status()
            img = Image.open(BytesIO(response.content))

            results = {
                'has_image': True,
                'emotion': 'neutral',
                'confidence': 0.0,
                'objects_detected': [],
                'text_extracted': '',
                'scene_description': '',
                'facial_emotions': [],
                'analysis_methods': []
            }

            # 1. CLIP emotion analysis
            if self.clip_model and self.clip_processor:
                try:
                    clip_result = self._analyze_with_clip(img)
                    results['emotion'] = clip_result['emotion']
                    results['confidence'] = clip_result['confidence']
                    results['analysis_methods'].append('clip')
                    print(f"✓ CLIP analysis: {clip_result['emotion']} ({clip_result['confidence']:.2f})")
                except Exception as e:
                    print(f"CLIP analysis failed: {e}")

            # 2. BLIP image captioning
            if self.blip_model and self.blip_processor:
                try:
                    caption = self._generate_caption(img)
                    results['scene_description'] = caption
                    results['analysis_methods'].append('blip')
                    print(f"✓ BLIP caption: {caption}")
                except Exception as e:
                    print(f"BLIP captioning failed: {e}")

            return results

        except Exception as e:
            print(f"Error analyzing image {image_url}: {e}")
            return self._placeholder_response()

    def analyze_video(self, video_url: str) -> Dict:
        """
        Video analysis disabled - use CLIP on key frames instead
        """
        print("Video Analysis: Not available (requires OpenCV)")
        return self._placeholder_video_response()

    def _analyze_with_clip(self, image: Image.Image) -> Dict:
        """Analyze image emotion using CLIP"""
        inputs = self.clip_processor(
            text=self.emotion_texts,
            images=image,
            return_tensors="pt",
            padding=True
        )

        with torch.no_grad():
            outputs = self.clip_model(**inputs)
            logits_per_image = outputs.logits_per_image
            probs = logits_per_image.softmax(dim=1)

        # Get the emotion with highest probability
        max_prob_idx = torch.argmax(probs[0]).item()
        confidence = probs[0][max_prob_idx].item()

        emotion_map = {
            0: 'joy',
            1: 'sadness',
            2: 'anger',
            3: 'fear',
            4: 'surprise',
            5: 'neutral'
        }

        return {
            'emotion': emotion_map[max_prob_idx],
            'confidence': confidence
        }

    def _generate_caption(self, image: Image.Image) -> str:
        """Generate image caption using BLIP"""
        inputs = self.blip_processor(image, return_tensors="pt")
        out = self.blip_model.generate(**inputs, max_length=50)
        caption = self.blip_processor.decode(out[0], skip_special_tokens=True)
        return caption

    def _placeholder_response(self) -> Dict:
        """Fallback response when analysis fails"""
        return {
            'emotion': 'neutral',
            'confidence': 0.0,
            'objects_detected': [],
            'text_extracted': '',
            'scene_description': 'Analysis failed',
            'facial_emotions': [],
            'analysis_methods': []
        }

    def _placeholder_video_response(self) -> Dict:
        """Fallback video response"""
        return {
            'emotion': 'neutral',
            'confidence': 0.0,
            'frames_analyzed': 0,
            'duration': 0,
            'key_moments': [],
            'analysis_methods': []
        }

    def extract_text_from_image(self, image_url: str) -> str:
        """Text extraction removed - use CLIP caption instead"""
        return ""

    def analyze_reddit_media(self, post_data: Dict) -> Dict:
        """
        Analyze media from Reddit post using AI models
        """
        results = {
            'has_media': False,
            'media_type': None,
            'analysis': None
        }

        # Check for media
        if 'url' in post_data:
            url = post_data['url']

            # Image
            if any(ext in url for ext in ['.jpg', '.jpeg', '.png', '.gif', '.webp']):
                results['has_media'] = True
                results['media_type'] = 'image'
                results['analysis'] = self.analyze_image(url)

            # Video
            elif any(ext in url for ext in ['.mp4', '.webm', '.mov', '.avi']):
                results['has_media'] = True
                results['media_type'] = 'video'
                results['analysis'] = self.analyze_video(url)

        return results


# Future integration guide
INTEGRATION_GUIDE = """
# Multimodal Analysis Integration Guide (CLIP + BLIP Only)

## Models Integrated:

### 1. CLIP (OpenAI)
- Image-text alignment
- Zero-shot image classification
- Emotion detection from images

### 2. BLIP (Salesforce)
- Image captioning
- Scene understanding
- Extract context from images

## Installation:
```bash
pip install transformers torch pillow
```

## Usage in app_enhanced.py:
```python
from multimodal_analyzer import MultimodalAnalyzer

multimodal = MultimodalAnalyzer()

# In post processing:
if post.get('has_media'):
    media_analysis = multimodal.analyze_reddit_media(post)
    post['media_emotion'] = media_analysis['analysis']['emotion']
```

## Future Enhancements:
- Video frame sampling with CLIP
- Advanced scene understanding
- Cross-modal emotion fusion
"""


# Test
if __name__ == '__main__':
    analyzer = MultimodalAnalyzer()

    print("\n📸 Multimodal Analyzer - Placeholder Mode\n")
    print("This module is ready for integration with:")
    print("  • CLIP for image understanding")
    print("  • BLIP for image captioning")
    print("  • DeepFace for facial emotion detection")
    print("  • EasyOCR for text extraction")
    print("  • Video frame analysis")
    print("\nSee integration guide in source code for details.")

    # Test placeholder
    result = analyzer.analyze_image("https://example.com/image.jpg")
    print(f"\nPlaceholder analysis result: {result}")
