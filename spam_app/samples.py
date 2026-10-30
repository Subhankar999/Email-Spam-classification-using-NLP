"""Built-in sample emails shown as one-click examples."""

from __future__ import annotations

# (key, button label, email text). Chosen so the pre-trained model classifies them
# as the label suggests; ordering alternates so the two classes are easy to compare.
SAMPLE_EMAILS: tuple[tuple[str, str, str], ...] = (
    (
        "prize",
        "Prize winner",
        "Congratulations! You have won 50000 rupees. Click here now to claim your free cash prize.",
    ),
    (
        "meeting",
        "Meeting reminder",
        "Hi Rahul, our project meeting is scheduled for tomorrow at 10 AM. Please bring your report.",
    ),
    (
        "iphone",
        "Free iPhone",
        "You have been selected for a free iPhone. Claim your exclusive gift now before the offer expires.",
    ),
    (
        "study",
        "Study plan",
        "Hey, are we still meeting at the library this evening to study for the exam?",
    ),
    (
        "loan",
        "Instant loan",
        "Limited time offer! Get cheap loans instantly without paperwork. Apply now and receive money today.",
    ),
    (
        "interview",
        "Interview invite",
        "Your interview is confirmed for Monday at 11 AM. Please bring your resume and academic certificates.",
    ),
    (
        "lottery",
        "Lottery claim",
        "URGENT! Your mobile number has won a lottery prize. Send your bank details to receive the money.",
    ),
    (
        "train",
        "Delayed train",
        "The train is delayed by twenty minutes. I will call you when I reach the station.",
    ),
)

SAMPLES_BY_KEY = {key: text for key, _label, text in SAMPLE_EMAILS}
