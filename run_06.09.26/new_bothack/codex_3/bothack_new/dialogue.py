"""Recognized prompts and interruptible terminal transactions."""
from dataclasses import dataclass, field
from enum import Enum


class Prompt(str, Enum):
    START = "start"
    GAME = "game"
    MENU = "menu"
    DIRECTION = "direction"
    END = "end"
    UNKNOWN = "unknown"


@dataclass
class Transaction:
    action: str
    expected: set[Prompt]
    started_revision: int
    accepted: int = 0
    cancelled: bool = False
    events: list[str] = field(default_factory=list)

    def observe(self, prompt: Prompt) -> bool:
        if self.cancelled: return False
        if prompt in self.expected:
            self.accepted += 1
            return True
        self.events.append(f"unexpected:{prompt.value}")
        return False

    def cancel(self, reason: str) -> None:
        self.cancelled = True
        self.events.append(f"cancel:{reason}")


def classify(text: str | tuple[str, ...]) -> Prompt:
    if not isinstance(text, str):
        text = "\n".join(text)
    lower = text.lower()
    if "do you want to quit" in lower or "you die" in lower or "ascended" in lower or "game over" in lower or "starved" in lower or "possessions identified" in lower:
        return Prompt.END
    if "hit return to continue" in lower or "are you sure you want to pray" in lower or "really attack" in lower or "beware, there will be no return" in lower or "there is already a game" in lower or "do what?" in lower or "what do you want to call" in lower or "name your" in lower or "pick your role" in lower or "shall i pick" in lower or "character" in lower:
        return Prompt.START
    if "in what direction" in lower or "which direction" in lower:
        return Prompt.DIRECTION
    if "--more--" in lower or "pick an object" in lower or "what do you want to use" in lower or "what do you want to eat" in lower:
        return Prompt.MENU
    if "@" in text or "hp:" in lower or "dungeon" in lower:
        return Prompt.GAME
    return Prompt.UNKNOWN
