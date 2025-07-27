# Bot Comment Enhancement Workflow

## Overview

The `enhance-bot-comments.yml` workflow automatically enhances comments from review bots (CodeRabbit, Codecov, and Claude Code Review) by appending structured prompts that developers can copy-paste to coding agents for quick issue resolution.

## How It Works

### Trigger
- **Event**: `issue_comment` with `created` activity type
- **Condition**: Only processes comments on pull requests
- **Target Bots**: 
  - `codecov[bot]` / `codecov-commenter` (cobertura de testes)
  - `coderabbit[bot]` / `coderabbitai` (revisão READ-ONLY)
  
**⚠️ IMPORTANTE**: CodeRabbit configurado como SOMENTE LEITURA - não faz commits ou alterações

### Process Flow

1. **Comment Detection**: Workflow triggers when any comment is created on a PR
2. **Bot Identification**: Checks if comment author matches target bot patterns
3. **Content Parsing**: Extracts actionable information based on bot type:
   - **File paths** mentioned in the comment
   - **Line numbers** referenced
   - **Code snippets** included
   - **Suggested changes** described
4. **Prompt Generation**: Creates a structured prompt section with:
   - Context about the bot's feedback
   - Specific tasks to perform
   - File and line references
   - Code examples when available
5. **Comment Enhancement**: Appends the prompt section to the original comment

### Bot-Specific Parsing

#### Codecov Comments
- Detects coverage decrease percentages
- Identifies files with missing coverage
- Extracts line numbers needing test coverage

#### CodeRabbit Comments  
- Parses summary sections and suggestions
- Extracts file references from backticks
- Captures code blocks for context

#### Claude Code Review Comments
- Identifies review sections and recommendations
- Extracts file paths and line references
- Captures suggested code improvements

## Example Transformation

### Before Enhancement
```
Suggestion: The variable old_data is never used. Consider removing it to improve clarity.

File: grimperium/utils/file_utils.py
Lines: 15-18
```python
def process_files():
  old_data = load_data()
  new_data = transform_data()
  return new_data
```
```

### After Enhancement
```
Suggestion: The variable old_data is never used. Consider removing it to improve clarity.

File: grimperium/utils/file_utils.py
Lines: 15-18
```python
def process_files():
  old_data = load_data()
  new_data = transform_data()
  return new_data
```

---
### 🤖 Code Agent Prompt

**CONTEXT:** A coderabbit bot has identified issues in this pull request that need attention.

**TASK:** Please address the following suggestions:

1. **CODE REVIEW**: Suggestion: The variable old_data is never used. Consider removing it to improve clarity...
   - **File:** `grimperium/utils/file_utils.py`
   - **Lines:** 15-18
   - **Code:**
   ```python
   def process_files():
     old_data = load_data()
     new_data = transform_data()
     return new_data
   ```

**PR:** #123

**INSTRUCTIONS:** 
1. Read the relevant files using the Read tool
2. Implement the suggested changes
3. Run any necessary tests or linting
4. Ensure the changes address the bot's concerns

---
```

## Safety Features

- **Idempotency**: Prevents duplicate enhancements by checking for existing prompt markers
- **Error Handling**: Graceful failure that doesn't break PR workflows
- **Non-Destructive**: Only appends content, never modifies original bot comments
- **Minimal Permissions**: Only requires `pull-requests: write`, `contents: read`, `issues: write`

## Configuration

The workflow is self-contained and requires no additional configuration. It uses the default `GITHUB_TOKEN` with standard permissions.

### Environment Variables (Optional)
You can disable the workflow by setting:
```yaml
env:
  ENHANCE_BOT_COMMENTS_ENABLED: false
```

## Monitoring and Debugging

### Logs
Check the workflow logs in the Actions tab for:
- Bot identification results
- Parsing success/failure
- Comment enhancement status

### Common Issues
1. **Comment not enhanced**: Check if bot author matches target patterns
2. **Parsing failures**: Review comment format and adjust parsing logic
3. **Permission errors**: Ensure workflow has required write permissions

## Maintenance

### Adding New Bots
To support additional bots:
1. Add bot username to `TARGET_BOTS` array
2. Create parsing function for the new bot's comment format
3. Add case to the switch statement in main processing logic

### Updating Parsing Logic
Bot comment formats may change over time. Update the relevant parsing functions:
- `parseCodecovComment()` for Codecov changes
- `parseCodeRabbitComment()` for CodeRabbit changes  
- `parseClaudeComment()` for Claude Code Review changes

## Testing

The workflow can be tested by:
1. Creating a PR with code that triggers bot reviews
2. Checking that bot comments get enhanced with prompt sections
3. Verifying the generated prompts contain relevant context

---

*This workflow enhances developer productivity by making bot suggestions immediately actionable with coding agents.*