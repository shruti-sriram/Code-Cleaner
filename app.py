from fastmcp import FastMCP
from crewai import Agent, Task, Crew
import os
import sys
import io
from contextlib import redirect_stdout, redirect_stderr
from langchain_community.chat_models import ChatOpenAI
from langchain.schema import HumanMessage

# Environment Setup
os.environ["OPENAI_API_KEY"] = "<OPENAI API KEY>"
os.environ["OPENAI_MODEL_NAME"] = 'gpt-3.5-turbo'

# CrewAI Cleaning Tool
def _analyze_code(code: str) -> dict:  # Removed async
    # Capture all output to prevent it from interfering with MCP protocol
    stdout_buffer = io.StringIO()
    stderr_buffer = io.StringIO()
    
    try:
        with redirect_stdout(stdout_buffer), redirect_stderr(stderr_buffer):
            # Agents
            code_parser = Agent(
                role="Code Structure Analyzer",
                goal="Extract all function definitions, imports, and comments from the code.",
                verbose=False,  
                backstory="An expert in parsing code structure into ASTs and clean metadata.",
            )

            function_usage_checker = Agent(
                role="Function Usage Auditor",
                goal="Detect unused functions.",
                verbose=False,  
                backstory="Finds defined functions that are never called.",
            )

            import_usage_checker = Agent(
                role="Import Usage Auditor",
                goal="Identify unused imports.",
                verbose=False,  
                backstory="Finds import statements that are never used.",
            )

            comment_reviewer = Agent(
                role="Comment Reviewer",
                goal="Find irrelevant or outdated comments.",
                verbose=False,  
                backstory="Sniffs out misleading or unnecessary comments.",
            )

            # Tasks
            parse_code = Task(
                description="Extract all function definitions, import statements, and inline comments from this code:\n{code}",
                expected_output="Structured list of functions, imports, and comments. Return a list in this format: 'Line X: [function/import/comment]'",
                agent=code_parser,
            )

            detect_unused_functions = Task(
                description="Find functions that are defined but not called. Identify the functions which have never been used in the code provided.",
                expected_output="List of unused functions with line numbers, in the format Line X: '[def ...]'.",
                agent=function_usage_checker,
                context=[parse_code],
            )

            detect_unused_imports = Task(
                description="Find unused import/include statements. Identify the imports that have never been used in the code.",
                expected_output="List of unused imports with line numbers, in the format Line X: '[import ...]'.",
                agent=import_usage_checker,
                context=[parse_code],
            )

            detect_irrelevant_comments = Task(
                description="""
                    Review the comments extracted from the code ({code}). 
                    For each comment:
                    - Identify whether it is useful, outdated, redundant, or irrelevant.
                    - Use the full code context to judge the relevance.
                    - Focus on comments that are vague, humorous, or unrelated to the logic.

                    Return a list of **irrelevant or misleading comments** in this format:
                    Line X: '[comment]' → Reason for removal
                """,
                expected_output="""
                    List of flagged comments with their line numbers, actual text, and specific reason for removal.
                    Format:
                    Line X: '[comment]' → [reason]
                """,
                agent=comment_reviewer,
                context=[parse_code],
            )

            # Unused Code Detection Crew - Set verbose=False
            unused_code_detection_crew = Crew(
                agents=[code_parser, function_usage_checker, import_usage_checker, comment_reviewer],
                tasks=[parse_code, detect_unused_functions, detect_unused_imports, detect_irrelevant_comments],
                verbose=False,  
                memory=False, 
            )

            # Execute the crew
            result = unused_code_detection_crew.kickoff(inputs={"code": code, "programming_language": "Python"})

            return {
                # "unused_functions": detect_unused_functions.output.raw if hasattr(detect_unused_functions.output, 'raw') else str(detect_unused_functions.output),
                # "unused_imports": detect_unused_imports.output.raw if hasattr(detect_unused_imports.output, 'raw') else str(detect_unused_imports.output),
                # "irrelevant_comments": detect_irrelevant_comments.output.raw if hasattr(detect_irrelevant_comments.output, 'raw') else str(detect_irrelevant_comments.output),
                "unused_functions": detect_unused_functions.output.raw if detect_unused_functions.output else "None found",
                "unused_imports": detect_unused_imports.output.raw if detect_unused_imports.output else "None found",
                "irrelevant_comments": detect_irrelevant_comments.output.raw if detect_irrelevant_comments.output else "None found",
            }
            
    except Exception as e:
        # Return error information instead of letting it crash
        return {
            "error": f"Analysis failed: {str(e)}",
            "unused_functions": "Could not analyze",
            "unused_imports": "Could not analyze", 
            "irrelevant_comments": "Could not analyze"
        }

# Prompt to Clean the Code
def _clean_code_with_prompt(code: str, unused_functions: str, unused_imports: str, irrelevant_comments: str) -> str:
    return f"""
        You are a code cleaning engine. Your job is to remove **only and exactly** the lines listed below from the given Python code.

        1. Remove these unused functions (entire function block):
        {unused_functions}

        2. Remove these unused imports (exact lines):
        {unused_imports}

        3. Remove these irrelevant comments (exact lines or lines containing them):
        {irrelevant_comments}

        Your final output must:
        - Be fully working Python code
        - Include ONLY the cleaned version inside a single Python code block (no explanation or commentary)

        Clean this Python code:

        ```python
        {code}
        ```
    """

# -------------------------------------------------------------------- MCP --------------------------------------------------------------------

# Create the MCP server
server = FastMCP(name="Dead Code Cleaner")

# Resource
@server.resource("/load_code/{file_path}")
def load_code(file_path: str) -> str:
    with open(file_path, "r") as f:
        return f.read()
    
# Tool
@server.tool()
def analyze_code_tool(code: str) -> dict:
    return _analyze_code(code) 

# Final Code Cleaning using FastMCP Prompt
@server.prompt()
def clean_code_with_prompt(code: str, unused_functions: str, unused_imports: str, irrelevant_comments: str) -> str:
    return _clean_code_with_prompt(code, unused_functions, unused_imports, irrelevant_comments)

# Code Cleaning
@server.tool()
def dead_code_cleaner(code: str) -> str:
    try:
        analysis = _analyze_code(code)
        
        print(analysis)

        if "error" in analysis:
            return f"Error during analysis: {analysis['error']}"
            
        prompt = _clean_code_with_prompt(
            code=code,
            unused_functions=analysis["unused_functions"],
            unused_imports=analysis["unused_imports"],
            irrelevant_comments=analysis["irrelevant_comments"],
        )

        chat = ChatOpenAI(model=os.environ["OPENAI_MODEL_NAME"], temperature=0)
        response = chat([HumanMessage(content=prompt)])

        return response.content

    except Exception as e:
        return f"Error during code cleaning: {str(e)}"

if __name__ == "__main__":
    server.run()