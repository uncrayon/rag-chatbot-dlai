Refactor @backend/ai_generator.py to support sequential tool calling where Claude can make up to 2 calls in separate API rounds.

Current behavior:
- Claude makes 1 tool call -> tools are removed from API params -> final reponse 
- If Claude wanto another call after seeing the results, it can't (gets empty reponse)

Desired behavior:
- Each tool call should be a separate API request where Claude can reason about previous results
- Support complex queries requiring multiple searches for comparisons, multi-part questions, or when information from different courses/lessons is needed 

Example Flow:
1. User: "Search for a course that discusses the same topic as lesson 4 of course X"
2. Claude: get course outline for course X -> get title of lesson 4
3. Claude: uses the title to search for a course that discusses the same topic -> returns course information
4. Claude: provides complete answer

Requirements:
- Maximum 2 sequential rounds per user query
- Terminate when: (a) 2 rounds completed, (b) Claude's response has not tool_use blocks, or (c) tool call fails, 
- preserve conversation context between rounds
- handle tool execition errors gracefully
- maintain existing functionality for single-round queries

Notes:
- update the system prompt in @backend/ai_generator.py
- update the test @backend/tests/test_ai_generator.py
- Write tests that verify the external behavior (API calls made, tools executed, results returned) rather than internal state details. 

Use two parallel subagents to brainstorm the possible plan. Do not implement any code.
