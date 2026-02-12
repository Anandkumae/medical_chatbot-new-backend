from typing import Dict, List, Optional, Tuple
from pydantic import BaseModel
from enum import Enum
import re
import logging

logger = logging.getLogger(__name__)

class SeverityLevel(str, Enum):
    MILD = "mild"
    MODERATE = "moderate"
    SEVERE = "severe"
    VERY_SEVERE = "very_severe"

class AssessmentStep(str, Enum):
    SYMPTOM = "symptom"
    DURATION = "duration"
    SEVERITY = "severity"
    ADDITIONAL_SYMPTOMS = "additional_symptoms"
    MEDICAL_HISTORY = "medical_history"
    COMPLETE = "complete"

class SymptomAssessment(BaseModel):
    step: AssessmentStep
    primary_symptom: Optional[str] = None
    duration: Optional[str] = None
    severity: Optional[SeverityLevel] = None
    additional_symptoms: List[str] = []
    medical_history: Optional[str] = None
    responses: Dict[str, str] = {}

class SymptomExtractor:
    """Extract symptoms and medical information from user responses."""
    
    def __init__(self):
        self.symptom_keywords = {
            'headache': ['headache', 'head pain', 'migraine', 'head is hurting'],
            'fever': ['fever', 'temperature', 'hot', 'chills', 'feverish'],
            'cough': ['cough', 'coughing', 'chesty cough', 'dry cough'],
            'fatigue': ['fatigue', 'tired', 'exhausted', 'weak', 'no energy'],
            'nausea': ['nausea', 'queasy', 'sick to stomach', 'vomiting'],
            'pain': ['pain', 'ache', 'hurt', 'sore', 'uncomfortable'],
            'breathing': ['breathing', 'breath', 'shortness of breath', 'difficulty breathing'],
            'dizziness': ['dizzy', 'lightheaded', 'vertigo', 'spinning'],
            'chest pain': ['chest pain', 'chest tightness', 'chest pressure'],
            'stomach pain': ['stomach pain', 'abdominal pain', 'belly pain'],
        }
        
        self.duration_patterns = [
            r'(\d+)\s*(day|days|week|weeks|month|months|year|years)',
            r'(a few|several|some)\s*(day|days|week|weeks)',
            r'(since|for)\s+(yesterday|today|this morning|last week)',
            r'(just|recently|suddenly)'
        ]
        
        self.severity_keywords = {
            SeverityLevel.MILD: ['mild', 'slight', 'minor', 'low', '1-2', '1 out of 10', '2 out of 10'],
            SeverityLevel.MODERATE: ['moderate', 'medium', 'some', '3-6', '5 out of 10', '6 out of 10'],
            SeverityLevel.SEVERE: ['severe', 'bad', 'terrible', 'high', '7-8', '8 out of 10'],
            SeverityLevel.VERY_SEVERE: ['very severe', 'extreme', 'unbearable', 'worst', '9-10', '10 out of 10']
        }

    def extract_symptom(self, text: str) -> Optional[str]:
        """Extract primary symptom from user text."""
        text_lower = text.lower()
        
        for symptom, keywords in self.symptom_keywords.items():
            for keyword in keywords:
                if keyword in text_lower:
                    return symptom
        
        # Fallback: try to extract any pain/discomfort related term
        if any(word in text_lower for word in ['pain', 'ache', 'hurt', 'discomfort', 'symptom']):
            # Extract the location/type of pain
            words = text_lower.split()
            for i, word in enumerate(words):
                if word in ['pain', 'ache', 'hurt'] and i > 0:
                    return f"{words[i-1]} {word}"
        
        return None

    def extract_duration(self, text: str) -> Optional[str]:
        """Extract duration from user text."""
        text_lower = text.lower()
        
        for pattern in self.duration_patterns:
            match = re.search(pattern, text_lower)
            if match:
                return match.group(0)
        
        return None

    def extract_severity(self, text: str) -> Optional[SeverityLevel]:
        """Extract severity level from user text."""
        text_lower = text.lower()
        
        for severity, keywords in self.severity_keywords.items():
            for keyword in keywords:
                if keyword in text_lower:
                    return severity
        
        # Check for numeric scales (1-10)
        number_match = re.search(r'(\d+)\s*(out of\s*)?10', text_lower)
        if number_match:
            num = int(number_match.group(1))
            if num <= 3:
                return SeverityLevel.MILD
            elif num <= 6:
                return SeverityLevel.MODERATE
            elif num <= 8:
                return SeverityLevel.SEVERE
            else:
                return SeverityLevel.VERY_SEVERE
        
        return None

class DiseasePredictor:
    """Simple rule-based disease prediction based on symptoms."""
    
    def __init__(self):
        self.disease_patterns = {
            'Common Cold': {
                'symptoms': ['cough', 'sore throat', 'runny nose', 'sneezing'],
                'duration': '1-2 weeks',
                'severity': 'mild to moderate'
            },
            'Influenza (Flu)': {
                'symptoms': ['fever', 'body aches', 'headache', 'fatigue', 'cough'],
                'duration': '1-2 weeks',
                'severity': 'moderate to severe'
            },
            'COVID-19': {
                'symptoms': ['fever', 'dry cough', 'fatigue', 'loss of taste', 'breathing difficulty'],
                'duration': '2-6 weeks',
                'severity': 'mild to severe'
            },
            'Migraine': {
                'symptoms': ['headache', 'nausea', 'light sensitivity', 'vision changes'],
                'duration': '4-72 hours',
                'severity': 'moderate to severe'
            },
            'Gastroenteritis': {
                'symptoms': ['stomach pain', 'nausea', 'vomiting', 'diarrhea'],
                'duration': '1-3 days',
                'severity': 'moderate'
            }
        }

    def predict_diseases(self, symptoms: List[str]) -> List[Tuple[str, float]]:
        """Predict possible diseases based on symptoms."""
        predictions = []
        
        for disease, pattern in self.disease_patterns.items():
            symptom_matches = 0
            total_symptoms = len(pattern['symptoms'])
            
            for symptom in symptoms:
                if any(symptom.lower() in s.lower() for s in pattern['symptoms']):
                    symptom_matches += 1
            
            if symptom_matches > 0:
                confidence = symptom_matches / total_symptoms
                predictions.append((disease, confidence))
        
        # Sort by confidence
        predictions.sort(key=lambda x: x[1], reverse=True)
        return predictions

class AssessmentManager:
    """Manages the guided symptom assessment flow."""
    
    def __init__(self):
        self.extractor = SymptomExtractor()
        self.predictor = DiseasePredictor()
        self.assessments: Dict[str, SymptomAssessment] = {}

    def get_next_question(self, session_id: str, current_assessment: SymptomAssessment) -> Dict:
        """Get the next question based on current assessment step."""
        
        if current_assessment.step == AssessmentStep.SYMPTOM:
            return {
                "question": "What symptom are you experiencing? Please describe it in detail.",
                "type": "text",
                "step": "symptom",
                "examples": ["headache", "fever", "cough", "stomach pain", "fatigue"]
            }
        
        elif current_assessment.step == AssessmentStep.DURATION:
            return {
                "question": f"How long have you been experiencing {current_assessment.primary_symptom}?",
                "type": "text",
                "step": "duration",
                "examples": ["2 days", "since yesterday", "about a week", "just started"]
            }
        
        elif current_assessment.step == AssessmentStep.SEVERITY:
            return {
                "question": f"On a scale of 1 to 10, how severe is your {current_assessment.primary_symptom}? (1 = mild, 10 = very severe)",
                "type": "scale",
                "step": "severity",
                "examples": ["mild", "moderate", "severe", "5 out of 10", "7 out of 10"]
            }
        
        elif current_assessment.step == AssessmentStep.ADDITIONAL_SYMPTOMS:
            return {
                "question": "Are you experiencing any other symptoms? Please list them.",
                "type": "text",
                "step": "additional_symptoms",
                "examples": ["no", "also have fever", "nausea and fatigue", "body aches"]
            }
        
        elif current_assessment.step == AssessmentStep.MEDICAL_HISTORY:
            return {
                "question": "Do you have any relevant medical history or pre-existing conditions?",
                "type": "text",
                "step": "medical_history",
                "examples": ["no", "asthma", "diabetes", "high blood pressure", "none relevant"]
            }
        
        else:
            return self.generate_assessment_summary(current_assessment)

    def process_response(self, session_id: str, response: str, current_assessment: SymptomAssessment) -> SymptomAssessment:
        """Process user response and update assessment."""
        
        if current_assessment.step == AssessmentStep.SYMPTOM:
            symptom = self.extractor.extract_symptom(response)
            if symptom:
                current_assessment.primary_symptom = symptom
            else:
                current_assessment.primary_symptom = response.strip()
            current_assessment.responses['symptom'] = response
            current_assessment.step = AssessmentStep.DURATION
        
        elif current_assessment.step == AssessmentStep.DURATION:
            duration = self.extractor.extract_duration(response)
            current_assessment.duration = duration or response.strip()
            current_assessment.responses['duration'] = response
            current_assessment.step = AssessmentStep.SEVERITY
        
        elif current_assessment.step == AssessmentStep.SEVERITY:
            severity = self.extractor.extract_severity(response)
            current_assessment.severity = severity
            current_assessment.responses['severity'] = response
            current_assessment.step = AssessmentStep.ADDITIONAL_SYMPTOMS
        
        elif current_assessment.step == AssessmentStep.ADDITIONAL_SYMPTOMS:
            if response.lower() not in ['no', 'none', 'nothing']:
                # Extract additional symptoms
                additional = self.extractor.extract_symptom(response)
                if additional:
                    current_assessment.additional_symptoms.append(additional)
                else:
                    current_assessment.additional_symptoms.append(response.strip())
            current_assessment.responses['additional_symptoms'] = response
            current_assessment.step = AssessmentStep.MEDICAL_HISTORY
        
        elif current_assessment.step == AssessmentStep.MEDICAL_HISTORY:
            current_assessment.medical_history = response if response.lower() not in ['no', 'none'] else None
            current_assessment.responses['medical_history'] = response
            current_assessment.step = AssessmentStep.COMPLETE
        
        self.assessments[session_id] = current_assessment
        return current_assessment

    def generate_assessment_summary(self, assessment: SymptomAssessment) -> Dict:
        """Generate final assessment summary with disease predictions."""
        
        # Collect all symptoms
        all_symptoms = [assessment.primary_symptom] + assessment.additional_symptoms
        
        # Get disease predictions
        predictions = self.predictor.predict_diseases(all_symptoms)
        
        # Generate recommendations based on severity
        urgency_level = "low"
        if assessment.severity in [SeverityLevel.SEVERE, SeverityLevel.VERY_SEVERE]:
            urgency_level = "high"
        elif assessment.severity == SeverityLevel.MODERATE:
            urgency_level = "medium"
        
        return {
            "question": None,
            "type": "summary",
            "step": "complete",
            "assessment": {
                "primary_symptom": assessment.primary_symptom,
                "duration": assessment.duration,
                "severity": assessment.severity,
                "additional_symptoms": assessment.additional_symptoms,
                "medical_history": assessment.medical_history,
                "urgency_level": urgency_level,
                "disease_predictions": [
                    {"disease": disease, "confidence": confidence}
                    for disease, confidence in predictions[:3]  # Top 3 predictions
                ]
            }
        }

# Global assessment manager
assessment_manager = AssessmentManager()
