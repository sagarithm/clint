from typing import Dict, Any

def score_lead(lead: Dict[str, Any]) -> int:
    """
    Calculates a multi-condition digital excellence score (0-10) for a business.
    
    This intelligence engine evaluates:
    1. Infrastructure Gap (40%): Missing or poor website/SSL.
    2. Reputation Gap (30%): Low or missing reviews/ratings.
    3. Social/Marketing Gap (20%): Missing socials or engagement.
    4. Industry Value (10%): High-ticket niches (e.g. Dental, Legal).

    Returns:
        An integer quality score from 1 (Low Priority) to 10 (High Priority).
    """
    score = 0
    
    # 1. Infrastructure Opportunity
    website = lead.get('website', '').lower()
    if not website or website == 'n/a' or 'google.com' in website:
        score += 4 # Massive opportunity: No digital home
    
    # 2. Reputation Maturity
    rating = float(lead.get('rating') or 0.0)
    reviews = int(lead.get('reviews_count') or 0)
    
    if rating == 0:
        score += 2 # Clean slate: High growth project
    elif 0 < rating < 4.2:
        score += 3 # Recovery needed: High value for reputation mgmt
        
    if 0 < reviews < 15:
        score += 2 # Social proof gap: High value for marketing
    
    # 3. Industry Multiplier (Bonus for high-value clients)
    high_ticket_niches = ['dentist', 'dental', 'legal', 'lawyer', 'attorney', 'roofing', 'hvac', 'construction', 'medical']
    cat = (lead.get('business_category') or "").lower()
    if any(niche in cat for niche in high_ticket_niches):
        score += 1

    # 4. Technical Debt (Extracted from metadata if available)
    metadata = lead.get('about_us_info', '')
    if 'failed' in metadata.lower() or 'not found' in metadata.lower():
        score += 1 # Site is broken/outdated

    return min(max(score, 1), 10)
