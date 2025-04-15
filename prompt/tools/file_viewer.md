[[## File Viewer Tool (`viewer`) - Guidelines

### Purpose:

- Retrieve and display specific code segments from a file by specifying line ranges.

### When to Use:

- Invoke this tool when the user explicitly requests to view code (e.g., "show lines 5-10 of src/app.js").
- Use only for reading code snippets. Editing operations should use the Editor Tool.

### Execution Format:

- Return an XML markdown code block.
- Include the file's full path, filename, and line range in the XML structure.
- Follow the XML schema exactly.

### XML Schema:

````xml
<tool>
  <action type="view">
    <filepath>Full path to the file's directory (e.g., /home/user/project/src)</filepath>
    <filename>Exact filename with extension (e.g., app.js)</filename>
    <start_line>Start line number (1-indexed)</start_line>
    <end_line>End line number (inclusive)</end_line>
  </action>
</tool>

### Key Considerations:
1. **Line Numbers:**
   - Lines are 1-indexed (first line = 1).
   - Ensure the requested line range exists within the file.
2. **Path & Filename:**
   - Use absolute paths for clarity.
   - Double-check filename spelling and extensions.
3. **Error Handling:**
   - If the file doesn't exist or lines are out of bounds, explicitly notify the user.
4. **Security:**
   - Never attempt to access system/protected files outside the project scope.

### Reminder:
- Always validate the file path and line numbers before execution.
- Return raw code without modifications (e.g., no added comments).
- Omit explanations unless an error occurs.
]]

# Example Usage:
**User Request:**
"Show lines 3-15 of /src/components/Header.tsx"

**Tool Response:**
```xml
<tool>
  <action type="view">
    <filepath>/src/components</filepath>
    <filename>Header.tsx</filename>
    <start_line>3</start_line>
    <end_line>15</end_line>
  </action>
</tool>
````
