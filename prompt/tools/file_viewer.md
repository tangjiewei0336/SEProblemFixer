[[
## File Viewer Tool (`viewer`) - Guidelines

### Purpose:

- View specific code

### When to Use:

- Invoke this tool when you want to view code from repository.
- Use only for reading code snippets. Editing operations should use the Editor Tool.

### Execution Format:

- Return an XML markdown code block.
- Include the file's full path, filename in the XML structure.
- Follow the XML schema exactly.

### XML Schema:

```xml
<tool>
  <action type="view">
    <filepath>Full path to the file with extension (e.g., /home/user/project/src/app.js)</filepath>
  </action>
</tool>
```

### Key Considerations:
1. **Filepath:**
   - Use absolute paths for clarity.
   - Double-check filename spelling and extensions.
2. **Security:**
   - Never attempt to access system/protected files outside the project scope.

### Reminder:
- Always validate the file path and line numbers before execution.
- Omit explanations unless an error occurs.
- Whenever you feel uncertain about the file' s content, or if the file is too large, use this tool to view the file.

# Example Usage:
**Purpose:**
"Show src/components/Header.tsx"

**Formal Request:**
```xml
<tool>
  <action type="view">
    <filepath>src/components/Header.tsx</filepath>
  </action>
</tool>

````
]]
