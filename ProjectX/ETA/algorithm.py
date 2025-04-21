#------------------------------- WHats hot algrorithm ---------------------------#
import math

def compute_aura_score(friend_going, friend_interested, friend_not_going,
                       public_going, public_interested, public_not_going,
                       T, F=300, C=5000, bonus=0.5, k=0.05):
    """
    Calculate the aura score for an event.
    T: Days until the event
    F: Friend bonus factor
    C: Soft cap constant for public interactions
    bonus: Bonus multiplier for imminent events
    k: Decay constant for the time multiplier
    """
    # Calculate raw scores based on attendance responses
    friend_raw = friend_going * 5 + friend_interested * 3 + friend_not_going * (-5)
    public_raw = public_going * 5 + public_interested * 3 + public_not_going * (-5)
    friend_bonus = friend_raw * F
    public_score = C * (1 - math.exp(-public_raw / C))
    total_raw = friend_bonus + public_score

    # Compute a time multiplier that favors events happening sooner
    time_multiplier = 1 + bonus * math.exp(-k * (T - 1))
    final_score = total_raw * time_multiplier
    return final_score