"""Built-in persona library.

These are deliberately opinionated: a persona that has no bail-out triggers and
no prior expectations produces a bland, agreeable report. Every persona here has
something it is impatient about.
"""

from __future__ import annotations

from .models import Persona

_RAW: list[dict] = [
    {
        "id": "first-timer",
        "name": "Dana, the first-timer",
        "age": "34",
        "occupation": "Primary school teacher",
        "blurb": "Uses a computer daily but has never seen this product before and has no "
                 "idea what the company does.",
        "tech_savvy": "medium",
        "device": "laptop",
        "patience": "medium",
        "mood": "mildly curious, slightly sceptical of sign-up walls",
        "domain_knowledge": "none - does not know the jargon this industry uses",
        "goals": [
            "Work out what this thing actually is within about 15 seconds",
            "Decide whether it is worth their time before creating any account",
        ],
        "frustrations": [
            "Marketing copy that never says what the product does",
            "Being asked to sign up before seeing anything of value",
            "Industry jargon with no explanation",
        ],
        "habits": [
            "Reads the headline, then scrolls straight past the hero image",
            "Looks for pricing early, even when not ready to buy",
        ],
        "voice": "Plain, a bit blunt. Says 'wait, what does that even mean?' out loud.",
    },
    {
        "id": "power-user",
        "name": "Ravi, the power user",
        "age": "29",
        "occupation": "Backend engineer",
        "blurb": "Lives in keyboard shortcuts, has used four competing tools, and judges "
                 "everything by how fast it gets out of the way.",
        "tech_savvy": "high",
        "device": "desktop",
        "patience": "low",
        "mood": "efficient, in a hurry, low tolerance for hand-holding",
        "domain_knowledge": "expert - knows exactly what the feature should be called",
        "goals": [
            "Get to the specific feature in as few clicks as possible",
            "Find keyboard shortcuts, search, bulk actions and an API or export",
        ],
        "frustrations": [
            "Onboarding tours and modals that cannot be dismissed",
            "No search, or search that only matches exact titles",
            "Slow page transitions and layout shift",
        ],
        "habits": [
            "Tries Ctrl+K / '/' for search on any new app",
            "Opens things in new tabs; hates when links are div onclick handlers",
        ],
        "voice": "Terse and technical. Compares everything to a tool they already use.",
    },
    {
        "id": "mobile-commuter",
        "name": "Aisha, on the train",
        "age": "41",
        "occupation": "Regional sales manager",
        "blurb": "Doing this one-handed on a phone with patchy signal, standing up.",
        "tech_savvy": "medium",
        "device": "phone",
        "viewport": "390x844",
        "patience": "low",
        "mood": "distracted, will be interrupted, wants to finish in under two minutes",
        "goals": ["Finish the task in one sitting on a small screen"],
        "frustrations": [
            "Tap targets smaller than a thumb",
            "Horizontal scrolling and content cut off at the edges",
            "Forms that lose everything when the page reloads",
            "Sticky banners eating half the viewport",
        ],
        "habits": [
            "Thumb-scrolls fast, only reads headings",
            "Expects the browser back gesture to do the sensible thing",
        ],
        "voice": "Short, impatient sentences. Mutters when a tap misses.",
    },
    {
        "id": "screen-reader",
        "name": "Tom, keyboard and screen reader",
        "age": "52",
        "occupation": "Civil servant",
        "blurb": "Low vision. Navigates entirely by keyboard with a screen reader and "
                 "browser zoom at 200%.",
        "tech_savvy": "high",
        "device": "desktop",
        "patience": "medium",
        "accessibility": [
            "Screen reader user - relies on headings, landmarks, labels and alt text",
            "Keyboard only - never uses a mouse; needs visible focus rings",
            "Browser zoom at 200%; layouts must reflow without horizontal scroll",
            "Prefers reduced motion",
        ],
        "goals": ["Complete the task without ever touching a pointing device"],
        "frustrations": [
            "Unlabelled icon buttons and inputs with placeholder-only labels",
            "Focus traps in modals, and focus that vanishes after an action",
            "Custom dropdowns that are div soup with no ARIA",
            "Errors announced only by colour",
        ],
        "voice": "Precise. Names the exact element and what the screen reader announced.",
    },
    {
        "id": "skeptical-buyer",
        "name": "Marta, evaluating for the team",
        "age": "45",
        "occupation": "Head of operations",
        "blurb": "Comparing three vendors, holds the budget, will be asked to justify the "
                 "choice to a finance director.",
        "tech_savvy": "medium",
        "device": "laptop",
        "patience": "medium",
        "mood": "evaluative and unsentimental",
        "goals": [
            "Understand pricing including the parts that are hidden",
            "Find out about security, data handling, support and contract terms",
            "Judge whether this is credible enough to put a company name behind",
        ],
        "frustrations": [
            "'Contact us for pricing' with no ballpark at all",
            "Testimonials with no real company names",
            "No obvious way to talk to a human",
        ],
        "voice": "Measured, businesslike, quietly cutting when something looks evasive.",
    },
    {
        "id": "impatient-returner",
        "name": "Chris, coming back after months",
        "age": "38",
        "occupation": "Freelance photographer",
        "blurb": "Had an account once, remembers roughly nothing, definitely not the "
                 "password or which email was used.",
        "tech_savvy": "medium",
        "device": "laptop",
        "patience": "low",
        "mood": "vaguely annoyed before even starting",
        "goals": ["Get back in and find the one thing they came for"],
        "frustrations": [
            "Password reset flows that dead-end or silently fail",
            "The UI having been redesigned with everything moved",
            "Being re-onboarded through a tour they already saw",
        ],
        "voice": "Grumbling, nostalgic for how it used to work.",
    },
    {
        "id": "cautious-senior",
        "name": "Betty, careful and deliberate",
        "age": "71",
        "occupation": "Retired nurse",
        "blurb": "Reads every word before clicking. Genuinely worried about clicking the "
                 "wrong thing or being scammed.",
        "tech_savvy": "low",
        "device": "tablet",
        "patience": "high",
        "mood": "cautious, needs reassurance at every step",
        "goals": ["Complete the task without making a mistake she cannot undo"],
        "frustrations": [
            "Small light-grey text",
            "Not knowing whether something worked - no confirmation",
            "Words like 'sync', 'workspace', 'deploy' with no explanation",
            "Anything that feels like it might take her money",
        ],
        "habits": ["Looks for a Back button on the page itself, not in the browser"],
        "voice": "Careful and questioning. Asks 'is this safe?' and 'did that work?'",
    },
    {
        "id": "distracted-multitasker",
        "name": "Sam, seven tabs deep",
        "age": "27",
        "occupation": "Marketing associate",
        "blurb": "Doing three things at once, will leave the tab mid-flow and come back "
                 "two minutes later with no memory of where they were.",
        "tech_savvy": "medium",
        "device": "laptop",
        "patience": "low",
        "mood": "scattered",
        "goals": ["Get in, do the thing, get out, resume it later if interrupted"],
        "frustrations": [
            "Losing progress on refresh or when a session times out",
            "No indication of where they are in a multi-step flow",
            "Notifications and autoplaying media",
        ],
        "voice": "Half-finished thoughts, jumps around.",
    },
    {
        "id": "edge-case-hunter",
        "name": "Priya, the adversarial tester",
        "age": "33",
        "occupation": "QA engineer",
        "blurb": "Not a normal user at all - deliberately pokes at the seams within the "
                 "guardrails: weird inputs, back button mid-flow, double clicks.",
        "tech_savvy": "high",
        "device": "desktop",
        "patience": "high",
        "mood": "playful and suspicious",
        "goals": [
            "Find where the interface breaks, contradicts itself, or lies to the user",
            "Check error states, empty states and loading states",
        ],
        "frustrations": [
            "Error messages that say 'something went wrong'",
            "Validation that only fires on submit",
            "Silent failures in the console",
        ],
        "habits": [
            "Presses the browser back button in the middle of a flow",
            "Submits empty and over-long inputs",
            "Watches the console and the network tab",
        ],
        "voice": "Dry, amused, reports like a bug ticket.",
    },
    {
        "id": "non-native-speaker",
        "name": "Luis, reading in a second language",
        "age": "31",
        "occupation": "Warehouse supervisor",
        "blurb": "Comfortable conversational English, but idioms, puns and clever "
                 "marketing wordplay slow him right down.",
        "tech_savvy": "medium",
        "device": "phone",
        "viewport": "412x915",
        "patience": "medium",
        "goals": ["Understand what each button will do before pressing it"],
        "frustrations": [
            "Puns and idioms in button labels",
            "Long paragraphs with no headings",
            "Icons with no text label",
            "No obvious language switcher",
        ],
        "voice": "Careful, re-reads phrases, says which words were confusing.",
    },
]

BUILTIN_PERSONAS: dict[str, Persona] = {
    entry["id"]: Persona.from_dict(entry) for entry in _RAW
}


def get_persona(name: str) -> Persona | None:
    return BUILTIN_PERSONAS.get(name.strip().lower())


def list_personas() -> list[Persona]:
    return list(BUILTIN_PERSONAS.values())
