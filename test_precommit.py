#!/usr/bin/env python3
# Test file for pre-commit hook


def badly_formatted_function(x: int, y: int, z: int) -> int:
    """Test function with formatting issues."""
    result = x + y + z
    if result > 10:
        print("Result is greater than 10")
    else:
        print("Result is 10 or less")
    return result


# Extra blank lines


x = [1, 2, 3, 4, 5]
y = {"a": 1, "b": 2, "c": 3}
