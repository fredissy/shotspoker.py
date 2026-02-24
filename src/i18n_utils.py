from flask_babel import _

SUPPORTED_LANGUAGES = ['en', 'es', 'fr']

def get_js_translations():
    """
    Returns a dictionary of English string keys to translated values.
    Since we are in Python, _() will return the translated string based on the active locale.
    """
    return {
        # vote.js
        "Please enter a Jira Ticket ID": _("Please enter a Jira Ticket ID"),

        # vote-ui.js
        "Voting on": _("Voting on"),
        "Waiting for session...": _("Waiting for session..."),
        "Waiting for reveal...": _("Waiting for reveal..."),
        "Results are already visible": _("Results are already visible"),
        "Reveal results": _("Reveal results"),
        "Only the starter can reset": _("Only the starter can reset"),
        "Participants": _("Participants"),
        "No history yet.": _("No history yet."),
        "Failed to load history.": _("Failed to load history."),
        "Room ID copied to clipboard!": _("Room ID copied to clipboard!"),
        "Failed to copy Room ID": _("Failed to copy Room ID"),
        "Current Queue": _("Current Queue"),
        "Set Voting Queue": _("Set Voting Queue"),
        "Queue is empty": _("Queue is empty"),

        # vote-queue.js
        "Click to start voting on this ticket": _("Click to start voting on this ticket"),

        # login.js / server responses handled in JS
        "Connection error": _("Connection error"),
        "Name is required": _("Name is required"),
        "Room not found": _("Room not found"),

        # Dynamic roles/values (if needed)
        "Voter": _("Voter"),
        "Observer": _("Observer"),
        "Public": _("Public"),
        "Private": _("Private"),
        "Avg Score": _("Avg Score"),
        "Vote Breakdown": _("Vote Breakdown"),
        "Date": _("Date"),
        "Ticket Key": _("Ticket Key"),
        "Type": _("Type"),

        # Chart
        "Number of votes": _("Number of votes"),
        "Votes": _("Votes"),
    }
