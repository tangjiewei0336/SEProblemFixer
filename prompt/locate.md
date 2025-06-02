# Locate

## Background

I gave you a summary of a Spring Boot project code repo when constructing your RAG System.

## Task

Your task is to try to complement "{{commit_type}} {{commit_msg}}" in the code repo.
You need to decide which function is needed to be deleted or updated, and consider if there is need to create new functions.

## Final Output Format

Strictly answer in following json format. Do not add any words. Do not add any comments. Do not make up parts. Do not prepend or append any words to the json.
[
    {{
        "file": "the_file_name",
        "function": "the_function_name",
        "operation": "delete" or "create" or "update",
    }},
    {{
        ( the second or more file with same format as above if needed )
    }}
]
Do not explain the reason. Do not make up your answer. Don't miss anything because of newlines and whitespaces.

## Asking Questions Guidelines

You must come across doubts when viewing the code repo, so you can reply with your doubts, and I will answer you.

You must ask at least one question before you output your final answer.

Also, you have access to file-viewing tool, to impl the task, you must use it at least one time. The tool usage is below.

When you are using file-viewing tool, pay attention: the filepath is provied in the context after "Source:".

## Tools Access and Execution Guidelines

### Overview
You now have access to specialized tools that empower you to assist users with specific tasks. These tools are available only when explicitly requested by the user.

### General Rules
- **User-Triggered:** Only use a tool when the user explicitly indicates that a specific tool should be employed (e.g., phrases like "run command" for the cmd_runner).
- **Strict Schema Compliance:** Follow the exact XML schema provided when invoking any tool.
- **XML Format:** Always wrap your responses in a markdown code block designated as XML and within the `<tools></tools>` tags.
- **Valid XML Required:** Ensure that the constructed XML is valid and well-formed.
- **Multiple Commands:**
  - If issuing commands of the same type, combine them within one `<tools></tools>` XML block with separate `<action></action>` entries.
  - If issuing commands for different tools, ensure they're wrapped in `<tool></tool>` tags within the `<tools></tools>` block.
- **No Side Effects:** Tool invocations should not alter your core tasks or the general conversation structure.

## File Viewer Tool (`viewer`) - Guidelines

### Purpose:

- View specific code

### When to Use:

- Invoke this tool when you want to view code from repository.
- Use only for reading code snippets. Editing operations should use the Editor Tool.

### Execution Format:

- Return an XML markdown code block.
- Include the file's full path, filename in the XML structure. This can be found in Source section of RAG retrieved context.
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
{context}
```

## Code Repo

{{code_repo}}
