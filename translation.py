import requests
import os
from typing import Optional
import logging

logger = logging.getLogger(__name__)

class TranslationService:
    """Service for translating text between languages."""
    
    def __init__(self):
        # Using Google Translate API (free tier)
        self.api_url = "https://translation.googleapis.com/language/translate/v2"
        self.api_key = os.getenv("GOOGLE_TRANSLATE_API_KEY")
        
        # Language mappings
        self.language_map = {
            'en': 'en',
            'hi': 'hi',
            'mr': 'mr'
        }
        
        # Fallback translations for common medical terms
        self.fallback_translations = {
            'hi': {
                'headache': 'सिरदर्द',
                'fever': 'बुखार',
                'cough': 'खांसी',
                'pain': 'दर्द',
                'nausea': 'मतली',
                'fatigue': 'थकान',
                'dizziness': 'चक्कर आना',
                'chest pain': 'सीने में दर्द',
                'stomach pain': 'पेट दर्द',
                'breathing': 'सांस लेना',
                'symptoms': 'लक्षण',
                'causes': 'कारण',
                'precautions': 'सावधानियां',
                'treatment': 'इलाज',
                'severity': 'गंभीरता',
                'duration': 'अवधि',
                'mild': 'हल्का',
                'moderate': 'मध्यम',
                'severe': 'गंभीर',
                'doctor': 'डॉक्टर',
                'medicine': 'दवा',
                'rest': 'आराम',
                'water': 'पानी',
                'food': 'भोजन'
            },
            'mr': {
                'headache': 'डोकेदुखी',
                'fever': 'ताप',
                'cough': 'खोकली',
                'pain': 'दुखी',
                'nausea': 'मळमळ',
                'fatigue': 'थकवा',
                'dizziness': 'चक्कर येणे',
                'chest pain': 'छातीत दुखी',
                'stomach pain': 'पोटात दुखी',
                'breathing': 'श्वास घेणे',
                'symptoms': 'लक्षणे',
                'causes': 'कारणे',
                'precautions': 'खबरदारी',
                'treatment': 'उपचार',
                'severity': 'गंभीरता',
                'duration': 'कालावधी',
                'mild': 'कमी',
                'moderate': 'मध्यम',
                'severe': 'गंभीर',
                'doctor': 'डॉक्टर',
                'medicine': 'औषध',
                'rest': 'विश्रांती',
                'water': 'पाणी',
                'food': 'अन्न'
            }
        }

    def translate_text(self, text: str, target_language: str, source_language: str = 'en') -> str:
        """Translate text to target language."""
        
        if target_language == source_language:
            return text
            
        target_code = self.language_map.get(target_language)
        source_code = self.language_map.get(source_language)
        
        if not target_code:
            logger.warning(f"Unsupported target language: {target_language}")
            return text
            
        try:
            # Try Google Translate API if API key is available
            if self.api_key:
                return self._translate_with_google(text, target_code, source_code)
            else:
                # Use fallback translation
                return self._fallback_translate(text, target_language)
                
        except Exception as e:
            logger.error(f"Translation failed: {e}")
            return self._fallback_translate(text, target_language)

    def _translate_with_google(self, text: str, target_code: str, source_code: str) -> str:
        """Translate using Google Translate API."""
        
        params = {
            'key': self.api_key,
            'q': text,
            'source': source_code,
            'target': target_code,
            'format': 'text'
        }
        
        response = requests.post(self.api_url, params=params)
        
        if response.status_code == 200:
            data = response.json()
            if 'data' in data and 'translations' in data['data']:
                return data['data']['translations'][0]['translatedText']
        
        raise Exception(f"Google Translate API error: {response.status_code}")

    def _fallback_translate(self, text: str, target_language: str) -> str:
        """Fallback translation using word mapping."""
        
        if target_language not in self.fallback_translations:
            return text
            
        translations = self.fallback_translations[target_language]
        
        # Simple word replacement
        translated_text = text.lower()
        for english_term, translated_term in translations.items():
            translated_text = translated_text.replace(english_term, translated_term)
            
        # Preserve original capitalization and structure
        return translated_text

    def get_medical_disclaimer(self, language: str) -> str:
        """Get medical disclaimer in specified language."""
        
        disclaimers = {
            'en': "⚠️ Important: This AI assistant provides general information and is not a substitute for professional medical care. Always consult with a qualified healthcare provider for medical concerns.",
            'hi': "⚠️ महत्वपूर्ण: यह AI सहायक सामान्य जानकारी प्रदान करता है और पेशेवर चिकित्सा देखभाल का विकल्प नहीं है। चिकित्सा संबंधी चिंताओं के लिए हमेशा योग्य स्वास्थ्य देखभाल प्रदाता से परामर्श करें।",
            'mr': "⚠️ महत्त्वाचे: हे AI सहायक सामान्य माहिती प्रदान करते आणि व्यावसायिक वैद्यकीय देखभालीचा पर्याय नाही. वैद्यकीय चिंता आणि गोष्टींसाठी नेहमी पात्र आरोग्य देखभाल प्रदात्यांशी सल्ला करा."
        }
        
        return disclaimers.get(language, disclaimers['en'])

# Global translation service instance
translation_service = TranslationService()
