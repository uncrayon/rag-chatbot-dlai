# RAG Chatbot - Fix Implementation TODO

**Generated from**: Comprehensive test suite (41/41 tests passing)
**Date**: December 30, 2025
**Status**: All fixes identified and ready to implement

---

## 🔴 HIGH PRIORITY

### [ ] Fix #1: Standardize Chunk Prefixing
**File**: `backend/document_processor.py`
**Line**: 186
**Estimated Time**: 5 minutes

**Problem**: Inconsistent prefixing between regular lessons and last lesson affects search quality

**Change**:
```python
# BEFORE (Line 184-188):
if idx == 0:
    chunk_with_context = f"Lesson {current_lesson} content: {chunk}"
else:
    chunk_with_context = chunk

# AFTER:
if idx == 0:
    chunk_with_context = f"Course {course.title} Lesson {current_lesson} content: {chunk}"
else:
    chunk_with_context = chunk
```

**Test**: Run `uv run pytest tests/test_course_search_tool.py -v`

---

## 🟡 MEDIUM PRIORITY

### [ ] Fix #2: Remove Redundant Prompt Wrapper
**File**: `backend/rag_system.py`
**Line**: 116
**Estimated Time**: 2 minutes

**Problem**: Unnecessary prompt wrapping duplicates system prompt instructions

**Change**:
```python
# BEFORE (Line 116):
prompt = f"""Answer this question about course materials: {query}"""

# AFTER:
prompt = query
```

**Test**: Run `uv run pytest tests/test_rag_system.py -v`

---

### [ ] Fix #3: Add Input Validation for Lesson Numbers
**File**: `backend/search_tools.py`
**Lines**: After line 64 (in `execute()` method)
**Estimated Time**: 5 minutes

**Problem**: No validation for invalid lesson numbers (negative, zero)

**Change**:
```python
# ADD after line 64, before "# Use the vector store's unified search interface":

# Validate lesson_number
if lesson_number is not None and lesson_number < 1:
    return "Invalid lesson number. Lesson numbers must be positive integers."
```

**Test**: Run `uv run pytest tests/test_course_search_tool.py::test_execute_with_lesson_number_filter -v`

**Optional**: Add new test case:
```python
def test_execute_invalid_lesson_number(mock_vector_store):
    tool = CourseSearchTool(mock_vector_store)
    result = tool.execute(query="test", lesson_number=-1)
    assert "Invalid lesson number" in result
```

---

## 🟢 LOW PRIORITY (Enhancements)

### [ ] Fix #4: Add API Timeout Configuration
**File**: `backend/ai_generator.py`
**Line**: 38
**Estimated Time**: 3 minutes

**Problem**: No timeout configured - requests could hang indefinitely

**Change**:
```python
# BEFORE (Line 38):
self.client = anthropic.Anthropic(api_key=api_key)

# AFTER:
self.client = anthropic.Anthropic(
    api_key=api_key,
    timeout=30.0  # 30 second timeout for API calls
)
```

**Test**: Run `uv run pytest tests/test_ai_generator.py -v`

---

### [ ] Fix #5: Improve Edge Case Handling
**File**: `backend/ai_generator.py`
**Lines**: 88-92
**Estimated Time**: 10 minutes

**Problem**: Potential AttributeError when tool_use received without tool_manager

**Change**:
```python
# BEFORE (Lines 88-92):
# Handle tool execution if needed
if response.stop_reason == "tool_use" and tool_manager:
    return self._handle_tool_execution(response, api_params, tool_manager)

# Return direct response
return response.content[0].text

# AFTER:
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

**Test**: Run `uv run pytest tests/test_ai_generator.py::test_no_tool_manager_with_tool_use -v`

---

## 📋 Implementation Checklist

### Before Starting
- [ ] Commit current working state: `git add . && git commit -m "Pre-fixes checkpoint"`
- [ ] Create feature branch: `git checkout -b fix/test-improvements`

### For Each Fix
1. [ ] Make the code change
2. [ ] Run specific test file for that component
3. [ ] Run full test suite: `uv run pytest tests/ -v`
4. [ ] Verify all 41 tests still pass
5. [ ] Commit: `git commit -m "Fix #N: <description>"`

### After All Fixes
- [ ] Run full test suite with coverage: `uv run pytest tests/ --cov=. --cov-report=term`
- [ ] Verify coverage remains at 73%+ overall
- [ ] Test manually with the application running
- [ ] Update CHANGELOG or release notes
- [ ] Create PR or merge to main

---

## 🧪 Verification Commands

```bash
# Run all tests
uv run pytest tests/ -v

# Run with coverage
uv run pytest tests/ --cov=. --cov-report=term --cov-report=html

# Run specific test file
uv run pytest tests/test_course_search_tool.py -v
uv run pytest tests/test_ai_generator.py -v
uv run pytest tests/test_rag_system.py -v

# Run specific test
uv run pytest tests/test_course_search_tool.py::test_execute_basic_query -v

# View coverage report
open htmlcov/index.html  # On macOS
```

---

## 📊 Expected Results

After implementing all fixes:
- ✅ All 41 tests should still pass
- ✅ Coverage should remain at 73%+
- ✅ No new warnings or errors
- ✅ Consistent chunk formatting across all lessons
- ✅ More efficient API usage (no redundant prompts)
- ✅ Better input validation
- ✅ Improved reliability (timeout, error handling)

---

## 📚 Reference Documents

- **Detailed Analysis**: `backend/TEST_RESULTS.md`
- **Fix Details**: `backend/PROPOSED_FIXES.md`
- **Test Files**:
  - `backend/tests/test_course_search_tool.py`
  - `backend/tests/test_ai_generator.py`
  - `backend/tests/test_rag_system.py`

---

## 🎯 Success Criteria

- [x] Test suite created (41 tests)
- [x] All tests passing
- [x] Issues identified and documented
- [ ] All HIGH priority fixes applied
- [ ] All MEDIUM priority fixes applied
- [ ] All LOW priority fixes applied
- [ ] Full test suite passing after fixes
- [ ] Manual testing completed
- [ ] Changes committed and pushed

---

**Next Action**: Start with Fix #1 (Chunk Prefixing) - highest impact, easiest to implement!
