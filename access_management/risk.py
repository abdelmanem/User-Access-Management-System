from typing import Dict

class RiskScorer:
    """Simple risk scoring engine used to calculate a 0-100 risk score for access requests.

    This implementation is intentionally lightweight and deterministic. It can be extended
    to use ML models or external threat intelligence as needed.
    """

    DEFAULT_WEIGHTS = {
        'access_type': 40,
        'system_sensitivity': 30,
        'user_tenure': 10,
        'is_admin_access': 15,
        'justification_quality': 5,
    }

    ACCESS_TYPE_SCORES = {
        'Super Admin': 100,
        'Admin': 80,
        'Full Access': 60,
        'Read/Write': 40,
        'Read Only': 10,
        'Limited': 20,
        'Custom': 30,
        'Temporary': 25,
    }

    SENSITIVITY_SCORES = {
        'High': 100,
        'Medium': 50,
        'Low': 10,
        None: 20,
    }

    def __init__(self, weights: Dict = None):
        self.weights = weights or self.DEFAULT_WEIGHTS

    def calculate_risk_score(self, *, access_type: str = None, system_sensitivity: str = None,
                             user_tenure_days: int = None, is_admin_access: bool = False,
                             justification_quality: int = None) -> int:
        """Return integer 0-100 risk score.

        justification_quality: 0-10 (higher is better)
        user_tenure_days: used inversely - shorter tenure increases risk
        """
        score = 0

        # access_type
        at_score = self.ACCESS_TYPE_SCORES.get(access_type, 30)
        score += (at_score * (self.weights['access_type'] / 100.0))

        # system sensitivity
        ss = self.SENSITIVITY_SCORES.get(system_sensitivity, 20)
        score += (ss * (self.weights['system_sensitivity'] / 100.0))

        # user tenure: less tenure -> more risk
        if user_tenure_days is None:
            tenure_component = 20
        else:
            if user_tenure_days < 30:
                tenure_component = 100
            elif user_tenure_days < 180:
                tenure_component = 60
            else:
                tenure_component = 10
        score += (tenure_component * (self.weights['user_tenure'] / 100.0))

        # admin access
        score += (100 if is_admin_access else 0) * (self.weights['is_admin_access'] / 100.0)

        # justification quality reduces risk when high
        if justification_quality is None:
            jq = 5
        else:
            jq = max(0, min(10, justification_quality))
        justification_component = 100 - (jq * 10)
        score += (justification_component * (self.weights['justification_quality'] / 100.0))

        # clamp
        final = int(max(0, min(100, round(score))))
        return final
