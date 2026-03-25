from typing import Dict

def score_lead(lead: Dict) -> int:
    """
    Rates a lead from 1 to 10 based on digital presence.
    - Website: +3
    - Email: +2
    - Social Links: +2
    - Reviews > 50: +2
    - Rating > 4.0: +1
    """
    score = 0
    if lead.get('website') and lead['website'] != 'N/A':
        score += 3
    if lead.get('email') and lead['email'] != 'N/A':
        score += 2
    
    # Check for social links in the raw data (stored as string in DB)
    socials = lead.get('social_links', {})
    if isinstance(socials, str):
        # Very basic check if it's a non-empty dict string or has platform names
        if len(socials) > 10: score += 2
    elif isinstance(socials, dict) and socials:
        score += 2

    if (lead.get('reviews_count') or 0) > 50:
        score += 2
    
    if (lead.get('rating') or 0.0) >= 4.0:
        score += 1
        
    return min(max(score, 1), 10)
