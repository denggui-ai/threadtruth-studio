"""Validate and bind the current task's scene, light and composition targets."""

BEGIN = '[Task photography targets]'
END = '[/Task photography targets]'


def validate(value):
    if not isinstance(value, list) or not 2 <= len(value) <= 4:
        raise ValueError('Task photography_targets must be a list of 2–4 nonempty single-line strings, at most 240 characters each')
    result = []
    for target in value:
        if (not isinstance(target, str) or not target.strip() or len(target.strip()) > 240
                or len(target.splitlines()) != 1
                or any(ord(character) < 32 or ord(character) == 127 for character in target)
                or BEGIN in target or END in target):
            raise ValueError('Each task photography target must be a nonempty single-line string of at most 240 characters, without block markers')
        result.append(target.strip())
    return result


def render(value):
    return BEGIN + '\n' + '\n'.join('- ' + target for target in validate(value)) + '\n' + END


def apply(prompt, value=None):
    """Keep prose intact; reuse one matching block or append the frozen targets."""
    has_markers = BEGIN in prompt or END in prompt
    if value is None:
        if has_markers:
            raise ValueError('A task photography target block requires frozen context.photography_targets')
        return prompt
    canonical = render(value)
    if has_markers:
        if prompt.count(BEGIN) != 1 or prompt.count(END) != 1:
            raise ValueError('Task photography target block is incomplete or duplicated')
        start = prompt.index(BEGIN)
        end = prompt.index(END) + len(END)
        if prompt[start:end] != canonical:
            raise ValueError('Task photography target block conflicts with frozen context.photography_targets')
        return prompt
    return prompt + ('' if prompt.endswith('\n') else '\n') + canonical + '\n'
