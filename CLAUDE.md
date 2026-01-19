# Project-Specific Claude Instructions

## Package Manager

Always use `bun` instead of `npm` or `yarn` for frontend operations.

## Serena MCP Best Practices

This project uses Serena for semantic code navigation and editing. Follow these practices for efficient workflows:

### Use Symbolic Tools First
Instead of reading entire files, use `find_symbol` with `include_body=True` for targeted reads:
```
find_symbol(name_path="MyClass/myMethod", include_body=True)
```
This is faster and uses less context than reading whole files.

### Leverage Substring Matching
When unsure of exact symbol names:
```
find_symbol(name_path="handler", substring_matching=True)
```

### Use Regex Mode in `replace_content`
For partial edits within symbols (when `replace_symbol_body` is too broad):
```
replace_content(needle="old_pattern.*?end", repl="new_content", mode="regex")
```
Use non-greedy `.*?` to avoid matching too much.

### Keep Memories Updated
After significant work, update memories with `write_memory` so future sessions have context. Review `.serena/memories/` periodically and keep them current.

### Think Tools Are Your Friends
Use `think_about_collected_information` after research and `think_about_task_adherence` before making edits. These help maintain focus on complex tasks.
