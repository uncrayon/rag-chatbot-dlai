# Proposed Fixes for RAG Chatbot System

Based on comprehensive testing with 41 tests (100% pass rate), here are the recommended code improvements:

## Fix #1: Standardize Chunk Prefixing (HIGH PRIORITY)

**File**: `backend/document_processor.py`
**Line**: 186
**Issue**: Inconsistent prefixing between regular lessons and last lesson

### Current Code (Lines 184-188):
```python
# For the first chunk of each lesson, add lesson context
if idx == 0:
    chunk_with_context = f"Lesson {current_lesson} content: {chunk}"
else:
    chunk_with_context = chunk
```

### Proposed Fix:
```python
# For the first chunk of each lesson, add lesson context with course title
if idx == 0:
    chunk_with_context = f"Course {course.title} Lesson {current_lesson} content: {chunk}"
else:
    chunk_with_context = chunk
```

**Why**: Currently line 234 (last lesson) uses `Course {title} Lesson {N}` format, but line 186 (other lessons) uses `Lesson {N}` format. This creates inconsistent search results.

---

## Fix #2: Remove Redundant Prompt Wrapper (MEDIUM PRIORITY)

**File**: `backend/rag_system.py`
**Line**: 116
**Issue**: Unnecessary prompt wrapping that duplicates system prompt instructions

### Current Code (Line 116):
```python
prompt = f"""Answer this question about course materials: {query}"""
```

### Proposed Fix:
```python
prompt = query
```

**Why**: The system prompt in `ai_generator.py` already provides comprehensive context about course materials and how to use tools. This wrapper is redundant and uses extra tokens.

---

## Fix #3: Add Input Validation (MEDIUM PRIORITY)

**File**: `backend/search_tools.py`
**Lines**: After line 64 (in CourseSearchTool.execute method)
**Issue**: No validation for invalid lesson numbers

### Proposed Addition:
```python
def execute(self, query: str, course_name: Optional[str] = None, lesson_number: Optional[int] = None) -> str:
    """
    Execute the search tool with given parameters.

    Args:
        query: What to search for
        course_name: Optional course filter
        lesson_number: Optional lesson filter

    Returns:
        Formatted search results or error message
    """

    # Validate lesson_number
    if lesson_number is not None and lesson_number < 1:
        return "Invalid lesson number. Lesson numbers must be positive integers."

    # Use the vector store's unified search interface
    results = self.store.search(
        query=query,
        course_name=course_name,
        lesson_number=lesson_number
    )
    # ... rest of method
```

**Why**: Prevents invalid lesson numbers (negative, zero) from being passed to the VectorStore, providing better error messages to users.

---

## Fix #4: Add API Timeout (LOW PRIORITY)

**File**: `backend/ai_generator.py`
**Line**: 38
**Issue**: No timeout configured, requests could hang indefinitely

### Current Code (Line 38):
```python
self.client = anthropic.Anthropic(api_key=api_key)
```

### Proposed Fix:
```python
self.client = anthropic.Anthropic(
    api_key=api_key,
    timeout=30.0  # 30 second timeout for API calls
)
```

**Why**: Prevents requests from hanging indefinitely if the Anthropic API is slow or unavailable.

---

## Fix #5: Improve Edge Case Handling (LOW PRIORITY)

**File**: `backend/ai_generator.py`
**Lines**: 88-92
**Issue**: Potential AttributeError when tool_use received without tool_manager

### Current Code (Lines 88-92):
```python
# Handle tool execution if needed
if response.stop_reason == "tool_use" and tool_manager:
    return self._handle_tool_execution(response, api_params, tool_manager)

# Return direct response
return response.content[0].text
```

### Proposed Fix:
```python
# Handle tool execution if needed
if response.stop_reason == "tool_use":
    if tool_manager:
        return self._handle_tool_execution(response, api_params, tool_manager)
    else:
        return "Error: Tool use requested but no tool manager available."

# Return direct response if we have text content
if response.content and len(response.content) > 0:
    content_block = response.content[0]
    if hasattr(content_block, 'text'):
        return content_block.text

return "Unable to generate response - unexpected content format."
```

**Why**: Provides graceful error handling instead of crashing with AttributeError when content[0] is a ToolUse block instead of TextBlock.

---

## Implementation Order

### Immediate (Before Next Deployment):
1. ✅ Fix #1 - Chunk prefixing (affects data quality)
2. ✅ Fix #2 - Remove redundant prompt (improves efficiency)

### Next Sprint:
3. ✅ Fix #3 - Input validation (improves UX)
4. ✅ Fix #4 - API timeout (improves reliability)

### Future Enhancement:
5. ✅ Fix #5 - Edge case handling (rare but good practice)

---

## Testing After Fixes

Run the test suite after each fix to ensure no regressions:

```bash
# Run all tests
uv run pytest tests/ -v

# Run with coverage
uv run pytest tests/ --cov=. --cov-report=term

# Run specific test file
uv run pytest tests/test_course_search_tool.py -v
```

Expected: All 41 tests should still pass after each fix.

---

## Additional Recommendations

### New Tests to Add (Optional):

1. **Test invalid lesson number validation** (once Fix #3 applied):
```python
def test_execute_invalid_lesson_number(mock_vector_store):
    tool = CourseSearchTool(mock_vector_store)
    result = tool.execute(query="test", lesson_number=-1)
    assert "Invalid lesson number" in result

    result = tool.execute(query="test", lesson_number=0)
    assert "Invalid lesson number" in result
```

2. **Test API timeout** (once Fix #4 applied):
```python
def test_api_timeout(mocker):
    from anthropic import Anthropic
    mock_init = mocker.patch.object(Anthropic, '__init__', return_value=None)

    generator = AIGenerator(api_key="test", model="claude")

    # Verify timeout was set
    mock_init.assert_called_with(api_key="test", timeout=30.0)
```

### Performance Improvements (Future):

1. **Cache course metadata** in ToolManager to reduce VectorStore queries
2. **Implement source deduplication** when same lesson appears multiple times
3. **Add batch query support** for processing multiple questions efficiently

---

**Document Version**: 1.0
**Date**: December 30, 2025
**Test Coverage**: 73% overall, 100% on critical components
**All Tests Passing**: ✅ 41/41
