"""Pure parsing helpers for bot commands."""

import re

# Inline buttons prefill "@botname /add ", so an optional mention may precede the command.
_PREFIX = r"^\s*(?:@\w+\s+)?/{command}(?:@\w+)?(?!\w)"


def command_pattern(command: str) -> re.Pattern[str]:
    """Regex matching messages that start with the given command."""
    return re.compile(_PREFIX.format(command=re.escape(command)))


def get_command_args(text: str, command: str) -> str | None:
    """Return the text after the command, or None if the message isn't this command."""
    match = re.match(_PREFIX.format(command=re.escape(command)) + r"(.*)", text, flags=re.DOTALL)
    return match.group(1).strip() if match else None


def split_items(args: str) -> list[str]:
    """Split comma-separated items, dropping empty entries."""
    return [item.strip() for item in args.split(",") if item.strip()]


def parse_numbers(args: str) -> set[int]:
    """Extract all integers from the text."""
    return {int(n) for n in re.findall(r"\d+", args)}


def resolve_numbers(items: list[tuple[int, str]], numbers: set[int]) -> tuple[list[int], list[int]]:
    """Map 1-based list numbers to item IDs. Returns (item_ids, invalid_numbers)."""
    ids = [items[n - 1][0] for n in sorted(numbers) if 0 < n <= len(items)]
    invalid = [n for n in sorted(numbers) if not 0 < n <= len(items)]
    return ids, invalid


def ids_except(items: list[tuple[int, str]], numbers: set[int]) -> list[int]:
    """Item IDs of all entries whose 1-based number is not in numbers."""
    return [item_id for i, (item_id, _) in enumerate(items, 1) if i not in numbers]


def parse_chat_ids(value: str) -> set[int]:
    """Parse a comma-separated list of chat IDs. Raises ValueError on invalid entries."""
    return {int(part) for part in value.split(",") if part.strip()}
