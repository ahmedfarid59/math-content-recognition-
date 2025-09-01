import re


def _find_matching_bracket(text: str, start_index: int, open_bracket: str, close_bracket: str) -> int:
    """
    Finds the index of the matching closing bracket from a starting open bracket.
    Handles nesting and escaped characters. Returns -1 if not found.
    """
    if start_index >= len(text) or text[start_index] != open_bracket:
        return -1

    balance = 1
    i = start_index + 1
    while i < len(text):
        char = text[i]
        # Basic escape handling: if we see a backslash, skip the next character
        if char == "\\" and i + 1 < len(text):
            i += 2
            continue

        if char == close_bracket:
            balance -= 1
        elif char == open_bracket:
            balance += 1

        if balance == 0:
            return i
        i += 1
    return -1  # Unmatched bracket


def change_all(input_str, old_inst, new_inst, old_surr_l, old_surr_r, new_surr_l, new_surr_r):
    """
    Recursively and efficiently replaces all occurrences of a LaTeX command
    and its delimited content.
    """
    output_parts = []
    last_end = 0

    # Use regex to find all potential starts of the command.
    # We must escape the command string in case it contains special regex characters.
    pattern = re.compile(r"(?<!\\)" + re.escape(old_inst))

    for match in pattern.finditer(input_str):
        start_cmd = match.start()
        start_arg = match.end()

        # Check if the command is immediately followed by the opening delimiter.
        if start_arg < len(input_str) and input_str[start_arg] == old_surr_l:
            end_arg = _find_matching_bracket(input_str, start_arg, old_surr_l, old_surr_r)

            if end_arg != -1:
                # A complete, balanced pattern was found.
                output_parts.append(input_str[last_end:start_cmd])

                # Extract the inner content and recursively process it.
                inner_content = input_str[start_arg + 1 : end_arg]
                processed_inner = change_all(
                    inner_content, old_inst, new_inst, old_surr_l, old_surr_r, new_surr_l, new_surr_r
                )

                output_parts.append(new_inst + new_surr_l + processed_inner + new_surr_r)
                last_end = end_arg + 1

    output_parts.append(input_str[last_end:])
    return "".join(output_parts)


def remove_style(input_str: str) -> str:
    input_str = change_all(input_str, r"\bm", r" ", r"{", r"}", r"", r" ")
    input_str = change_all(input_str, r"\boldsymbol", r" ", r"{", r"}", r"", r" ")
    input_str = change_all(input_str, r"\textit", r" ", r"{", r"}", r"", r" ")
    input_str = change_all(input_str, r"\textbf", r" ", r"{", r"}", r"", r" ")
    input_str = change_all(input_str, r"\mathbf", r" ", r"{", r"}", r"", r" ")
    output_str = input_str.strip()
    return output_str


def add_newlines(latex_str: str) -> str:
    """
    Adds newlines to a LaTeX string based on specific patterns, ensuring no
    duplicate newlines are added around begin/end environments.
    - After \\ (if not already followed by newline)
    - Before \\begin{...} (if not already preceded by newline)
    - After \\begin{...} (if not already followed by newline)
    - Before \\end{...} (if not already preceded by newline)
    - After \\end{...} (if not already followed by newline)

    Args:
        latex_str: The input LaTeX string.

    Returns:
        The LaTeX string with added newlines, avoiding duplicates.
    """
    processed_str = latex_str

    # 1. Replace whitespace around \begin{...} with \n...\n
    # \s* matches zero or more whitespace characters (space, tab, newline)
    # Captures the \begin{...} part in group 1 (\g<1>)
    processed_str = re.sub(r"\s*(\\begin\{[^}]*\})\s*", r"\n\g<1>\n", processed_str)

    # 2. Replace whitespace around \end{...} with \n...\n
    # Same logic as for \begin
    processed_str = re.sub(r"\s*(\\end\{[^}]*\})\s*", r"\n\g<1>\n", processed_str)

    # 3. Add newline after \\ (if not already followed by newline)
    processed_str = re.sub(r"\\\\(?!\n| )|\\\\ ", r"\\\\\n", processed_str)

    # 4. Cleanup: Collapse multiple consecutive newlines into a single newline.
    # This handles cases where the replacements above might have created \n\n.
    processed_str = re.sub(r"\n{2,}", "\n", processed_str)

    # Remove leading/trailing whitespace (including potential single newlines
    # at the very start/end resulting from the replacements) from the entire result.
    return processed_str.strip()
