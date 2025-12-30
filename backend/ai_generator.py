import anthropic
from typing import List, Optional, Dict, Any

class AIGenerator:
    """Handles interactions with Anthropic's Claude API for generating responses"""
    
    # Static system prompt to avoid rebuilding on each call
    SYSTEM_PROMPT = """ You are an AI assistant specialized in course materials and educational content with access to tools for course information.

Available Tools:
1. **search_course_content**: Search for specific content within course materials
   - Use for questions about detailed topics, concepts, or implementations
2. **get_course_outline**: Get complete course structure with all lessons
   - Use for questions about course structure, table of contents, lesson lists, or what a course covers
   - Returns: course title, course link, and all lessons with their numbers, titles, and links

Tool Usage Guidelines:
- **Sequential tool use**: You can make up to 2 tool calls across sequential rounds if needed for complex queries
- Use **get_course_outline** for: "What lessons are in X course?", "Show me the outline", "What does X course cover?", "List all lessons"
- Use **search_course_content** for: specific topics, concepts, code examples, or detailed explanations
- **Multi-step examples**:
  - "What lessons are in MCP course and what does lesson 2 cover?" → get outline, then search lesson 2
  - "Compare prompt engineering in lesson 1 vs lesson 3" → search lesson 1, then search lesson 3
- If no results, state this clearly without offering alternatives

Response Protocol:
- **General knowledge questions**: Answer using existing knowledge without tools
- **Course structure questions**: Use get_course_outline, then present the full lesson list
- **Course content questions**: Use search_course_content (multiple times if needed), then synthesize findings
- **Multi-step questions**: Use tools sequentially as needed to gather complete information
- **No meta-commentary**: Provide direct answers only — no reasoning process or tool explanations

All responses must be:
1. **Brief, Concise and focused** - Get to the point quickly
2. **Educational** - Maintain instructional value
3. **Clear** - Use accessible language
4. **Example-supported** - Include relevant examples when they aid understanding
Provide only the direct answer to what was asked.
"""

    # Maximum sequential tool-calling rounds per query
    MAX_TOOL_ROUNDS = 2

    def __init__(self, api_key: str, model: str):
        self.client = anthropic.Anthropic(api_key=api_key)
        self.model = model
        
        # Pre-build base API parameters
        self.base_params = {
            "model": self.model,
            "temperature": 0,
            "max_tokens": 800
        }

    def _execute_all_tools(self, response, tool_manager) -> List[Dict[str, Any]]:
        """
        Execute all tool calls from a response and return formatted results.

        Args:
            response: API response containing tool_use blocks
            tool_manager: Manager to execute tools

        Returns:
            List of tool_result dictionaries
        """
        tool_results = []

        for content_block in response.content:
            if content_block.type == "tool_use":
                # Execute tool
                result = tool_manager.execute_tool(
                    content_block.name,
                    **content_block.input
                )

                # Check if result indicates error
                is_error = result.startswith("Error:") or result.startswith("Tool '")

                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": content_block.id,
                    "content": result,
                    "is_error": is_error
                })

        return tool_results

    def generate_response(self, query: str,
                         conversation_history: Optional[str] = None,
                         tools: Optional[List] = None,
                         tool_manager=None) -> str:
        """
        Generate AI response with optional tool usage and conversation context.
        Supports up to MAX_TOOL_ROUNDS sequential tool-calling rounds.

        Args:
            query: The user's question or request
            conversation_history: Previous messages for context
            tools: Available tools the AI can use
            tool_manager: Manager to execute tools

        Returns:
            Generated response as string
        """

        # Build system content
        system_content = (
            f"{self.SYSTEM_PROMPT}\n\nPrevious conversation:\n{conversation_history}"
            if conversation_history
            else self.SYSTEM_PROMPT
        )

        # Initialize messages and round counter
        messages = [{"role": "user", "content": query}]
        round_count = 0

        # Iterative loop for sequential tool calling
        while round_count < self.MAX_TOOL_ROUNDS:
            # Prepare API call parameters (use copy to avoid mutation issues)
            api_params = {
                **self.base_params,
                "messages": messages.copy(),
                "system": system_content
            }

            # Add tools if available
            if tools:
                api_params["tools"] = tools
                api_params["tool_choice"] = {"type": "auto"}

            # Make API call
            response = self.client.messages.create(**api_params)

            # Termination condition: No tool use - return text response
            if response.stop_reason != "tool_use":
                return response.content[0].text

            # Termination condition: Tool use but no tool manager
            if not tool_manager:
                return "Error: Tool execution requested but no tool manager available"

            # Execute tools with error handling
            try:
                tool_results = self._execute_all_tools(response, tool_manager)
            except Exception as e:
                # Tool execution failed - add error result and break
                messages.append({"role": "assistant", "content": response.content})
                messages.append({
                    "role": "user",
                    "content": [{
                        "type": "tool_result",
                        "tool_use_id": response.content[0].id,
                        "content": f"Tool execution failed: {str(e)}",
                        "is_error": True
                    }]
                })
                break

            # Add assistant's tool use to messages
            messages.append({"role": "assistant", "content": response.content})

            # Add tool results to messages
            if tool_results:
                messages.append({"role": "user", "content": tool_results})

            # Increment round counter
            round_count += 1

        # Make final API call without tools to get synthesis
        final_params = {
            **self.base_params,
            "messages": messages.copy(),
            "system": system_content
        }

        final_response = self.client.messages.create(**final_params)
        return final_response.content[0].text