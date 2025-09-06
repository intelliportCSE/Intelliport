#!/usr/bin/env python3
"""
Gemini API Patch Generator
Generates patches for older versions using Gemini AI models.

This module provides two approaches:
1. Diff-based patch generation (unified diff format)
2. Complete function generation (recommended)
"""

import os
import json
import logging
import difflib
from typing import Dict, List, Tuple, Optional, Any
from google import genai
from google.genai import types

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class GeminiPatchGenerator:
    """
    Advanced patch generator using Gemini AI models for automated code transfer.
    
    Leverages Gemini 2.5 Pro's enhanced reasoning capabilities to analyze
    code patterns and generate semantically equivalent patches for different
    code versions.
    """
    
    def __init__(self, api_key: str, model: str = "gemini-2.5-pro"):
        """
        Initialize the Gemini Patch Generator.
        
        Args:
            api_key: Google AI API key for Gemini access
            model: Gemini model to use (default: gemini-2.5-pro)
        """
        self.api_key = api_key
        self.model = model
        self.client = None
        self._initialize_client()
    
    def _initialize_client(self):
        """Initialize the Gemini API client with optimal configuration."""
        try:
            # Set API key as environment variable for the client
            os.environ['GOOGLE_API_KEY'] = self.api_key
            self.client = genai.Client(api_key=self.api_key)
            logger.info(f"✅ Gemini API client initialized with model: {self.model}")
        except Exception as e:
            logger.error(f"❌ Failed to initialize Gemini client: {e}")
            raise
    
    def _get_generation_config(self, method: str) -> types.GenerateContentConfig:
        """
        Get optimized generation configuration for different methods.
        
        Args:
            method: Generation method ("diff" or "function")
            
        Returns:
            Optimized GenerateContentConfig for the specific task
        """
        base_config = {
            "temperature": 0.1,  # Low randomness for consistent code generation
            "top_p": 0.8,        # Focused sampling for quality
            "top_k": 40,         # Limit vocabulary for code generation
            "max_output_tokens": 8192,  # Sufficient for large functions
        }
        
        if method == "diff":
            # Slightly higher temperature for diff generation flexibility
            base_config["temperature"] = 0.15
            system_instruction = """You are an expert software engineer specializing in automated patch generation and code analysis. You excel at understanding code differences and generating precise unified diff patches."""
        else:  # function method
            # Lower temperature for more deterministic function generation
            base_config["temperature"] = 0.05
            system_instruction = """You are an expert software engineer with deep expertise in code transformation and automated patch generation. You excel at understanding code patterns, analyzing semantic differences, and generating functionally equivalent code for different versions."""
        
        return types.GenerateContentConfig(
            system_instruction=system_instruction,
            **base_config
        )
    
    def generate_unified_diff(self, pa_content: str, pb_content: str) -> str:
        """
        Generate unified diff between PA and PB versions.
        
        Args:
            pa_content: Pre-patch function content
            pb_content: Post-patch function content
            
        Returns:
            Unified diff string with zero context lines
        """
        pa_lines = pa_content.splitlines(keepends=True)
        pb_lines = pb_content.splitlines(keepends=True)
        
        # Generate unified diff with zero context lines
        diff = difflib.unified_diff(
            pa_lines,
            pb_lines,
            fromfile='PA/function.cc',
            tofile='PB/function.cc',
            n=0  # Zero context lines as requested
        )
        
        return ''.join(diff)
    
    def method1_diff_based_generation(self, pa_content: str, pb_content: str, pc_content: str) -> Dict[str, Any]:
        """
        Method 1: Generate patch for older version using diff-based approach.
        
        This method provides the mainline diff and asks Gemini to generate
        an equivalent diff for the older version.
        
        Args:
            pa_content: Mainline pre-patch function content
            pb_content: Mainline post-patch function content  
            pc_content: Older version pre-patch function content
            
        Returns:
            Dictionary containing generated diff and metadata
        """
        logger.info("🔄 Starting Method 1: Diff-based patch generation")
        
        # Generate mainline diff
        mainline_diff = self.generate_unified_diff(pa_content, pb_content)
        
        # Craft the expert prompt using chain-of-thought reasoning
        prompt = f"""# Expert Code Patch Generation Task

## Context
You are tasked with generating a unified diff patch for an older version of code, based on a patch applied to the mainline version. This requires deep understanding of code semantics and transformation patterns.

## Input Data

### Mainline Version Pre-Patch (PA):
```cpp
{pa_content}
```

### Mainline Version Post-Patch (PB):
```cpp
{pb_content}
```

### Mainline Diff (PA → PB):
```diff
{mainline_diff}
```

### Older Version Pre-Patch (PC):
```cpp
{pc_content}
```

## Task
Generate a unified diff patch for the older version (PC) that applies the same semantic changes shown in the mainline diff, but adapted to the older version's codebase structure.

## Chain-of-Thought Analysis
1. **Analyze the mainline changes**: What specific modifications were made? (e.g., variable additions, logic changes, error handling improvements)

2. **Identify semantic patterns**: What is the core intent of each change? How do they improve the code?

3. **Map to older version**: How should these changes be adapted to the older version's structure, considering:
   - Different variable names or function signatures
   - Different code organization or style
   - Different surrounding context

4. **Generate equivalent diff**: Create a unified diff that achieves the same functional improvements in the older version.

## Output Format Requirements
- Generate ONLY the unified diff in standard format
- Use zero context lines (as shown in the example)
- Include proper hunk headers with line numbers
- Ensure the diff can be applied cleanly to the older version
- Multiple hunks are acceptable if needed

## Generated Diff:
```diff
"""

        try:
            config = self._get_generation_config("diff")
            response = self.client.models.generate_content(
                model=self.model,
                contents=prompt,
                config=config
            )
            
            generated_diff = response.text.strip()
            
            # Extract diff from code blocks if present
            if "```diff" in generated_diff:
                start = generated_diff.find("```diff") + 7
                end = generated_diff.find("```", start)
                if end != -1:
                    generated_diff = generated_diff[start:end].strip()
            elif "```" in generated_diff:
                start = generated_diff.find("```") + 3
                end = generated_diff.rfind("```")
                if end != -1 and end > start:
                    generated_diff = generated_diff[start:end].strip()
            
            logger.info("✅ Method 1: Diff-based generation completed")
            
            return {
                "method": "diff_based",
                "success": True,
                "generated_diff": generated_diff,
                "mainline_diff": mainline_diff,
                "reasoning": "Applied semantic diff transformation to older version"
            }
            
        except Exception as e:
            logger.error(f"❌ Method 1 failed: {e}")
            return {
                "method": "diff_based",
                "success": False,
                "error": str(e),
                "generated_diff": None
            }
    
    def method2_function_generation(self, pa_content: str, pb_content: str, pc_content: str, 
                                  pa_function_name: str, pc_function_name: str) -> Dict[str, Any]:
        """
        Method 2: Generate complete patched function for older version.
        
        This method analyzes the complete transformation and generates the
        entire post-patch function for the older version.
        
        Args:
            pa_content: Mainline pre-patch function content
            pb_content: Mainline post-patch function content
            pc_content: Older version pre-patch function content
            pa_function_name: Mainline function name
            pc_function_name: Older version function name
            
        Returns:
            Dictionary containing generated function and metadata
        """
        logger.info("🔄 Starting Method 2: Complete function generation")
        
        # Craft the expert prompt with advanced chain-of-thought reasoning
        prompt = f"""# Expert Code Transformation & Patch Generation

## Mission
You are an elite software engineer specializing in automated code migration and patch generation. Your task is to analyze a successful patch applied to a mainline codebase and generate the equivalent patched function for an older version of the same codebase.

## Input Analysis

### Mainline Version - Pre-Patch Function ({pa_function_name}):
```cpp
{pa_content}
```

### Mainline Version - Post-Patch Function ({pa_function_name}):
```cpp
{pb_content}
```

### Older Version - Pre-Patch Function ({pc_function_name}):
```cpp
{pc_content}
```

## Deep Analysis Framework

### Step 1: Change Pattern Recognition
Analyze the mainline transformation to identify:
- **Structural changes**: New variables, modified logic flows, added validations
- **Semantic improvements**: Error handling, input validation, safety checks
- **Code quality enhancements**: Better variable naming, improved readability
- **Functional additions**: New features or capabilities

### Step 2: Contextual Mapping
Map the changes to the older version considering:
- **Function signature differences**: `{pa_function_name}` vs `{pc_function_name}`
- **Code style variations**: Different naming conventions or patterns
- **Structural differences**: Different organization or surrounding context
- **Version-specific considerations**: API differences or available functions

### Step 3: Semantic Preservation
Ensure the transformation preserves:
- **Core functionality**: The function's primary purpose remains intact
- **Improvement intent**: The same benefits are achieved in the older version
- **Code correctness**: Syntax and logic are valid for the older codebase
- **Integration compatibility**: Works within the older version's ecosystem

### Step 4: Quality Assurance
Verify the generated function:
- **Syntactic correctness**: Valid C++ syntax and structure
- **Logical consistency**: Proper variable usage and control flow
- **Error handling**: Appropriate validation and error management
- **Performance considerations**: Efficient implementation

## Generation Requirements

Generate the complete post-patch function for the older version that:
1. Incorporates all semantic improvements from the mainline patch
2. Adapts to the older version's structure and naming conventions
3. Maintains the function signature appropriate for `{pc_function_name}`
4. Preserves all functional enhancements while ensuring compatibility

## Output Format
Provide ONLY the complete function code without additional explanations or code blocks.

## Generated Function:
"""

        try:
            config = self._get_generation_config("function")
            response = self.client.models.generate_content(
                model=self.model,
                contents=prompt,
                config=config
            )
            
            generated_function = response.text.strip()
            
            # Clean up code blocks if present
            if "```cpp" in generated_function:
                start = generated_function.find("```cpp") + 6
                end = generated_function.find("```", start)
                if end != -1:
                    generated_function = generated_function[start:end].strip()
            elif "```" in generated_function:
                start = generated_function.find("```") + 3
                end = generated_function.rfind("```")
                if end != -1 and end > start:
                    generated_function = generated_function[start:end].strip()
            
            logger.info("✅ Method 2: Function generation completed")
            
            return {
                "method": "function_generation",
                "success": True,
                "generated_function": generated_function,
                "original_pc_function": pc_content,
                "function_name": pc_function_name,
                "reasoning": "Generated complete patched function with semantic preservation"
            }
            
        except Exception as e:
            logger.error(f"❌ Method 2 failed: {e}")
            return {
                "method": "function_generation",
                "success": False,
                "error": str(e),
                "generated_function": None
            }
    
    def generate_patch(self, triplet_data: Dict[str, Any], method: str = "both") -> Dict[str, Any]:
        """
        Generate patch for older version using specified method(s).
        
        Args:
            triplet_data: Function triplet data from FixMorph
            method: Generation method ("diff", "function", or "both")
            
        Returns:
            Dictionary containing patch generation results
        """
        logger.info(f"🚀 Starting patch generation using method: {method}")
        
        # Extract function data
        pa_content = triplet_data["pa_pre_patch"]["content"]
        pb_content = triplet_data["pb_post_patch"]["content"]
        pc_content = triplet_data["pc_pre_patch"]["content"]
        
        pa_function_name = triplet_data["function_mapping"]["pa_function_name"]
        pc_function_name = triplet_data["function_mapping"]["pc_function_name"]
        
        results = {
            "input_triplet": triplet_data["function_mapping"],
            "generation_timestamp": __import__('datetime').datetime.now().isoformat(),
            "model_used": self.model
        }
        
        if method in ["diff", "both"]:
            diff_result = self.method1_diff_based_generation(pa_content, pb_content, pc_content)
            results["diff_based_result"] = diff_result
        
        if method in ["function", "both"]:
            function_result = self.method2_function_generation(
                pa_content, pb_content, pc_content, pa_function_name, pc_function_name
            )
            results["function_generation_result"] = function_result
        
        # Determine recommended approach
        if method == "both":
            if (results.get("function_generation_result", {}).get("success", False) and 
                results.get("diff_based_result", {}).get("success", False)):
                results["recommendation"] = "function_generation"
                results["reason"] = "Complete function generation provides better semantic preservation and reliability"
            elif results.get("function_generation_result", {}).get("success", False):
                results["recommendation"] = "function_generation"
                results["reason"] = "Only function generation succeeded"
            elif results.get("diff_based_result", {}).get("success", False):
                results["recommendation"] = "diff_based"
                results["reason"] = "Only diff-based generation succeeded"
            else:
                results["recommendation"] = None
                results["reason"] = "Both methods failed"
        
        return results


def process_function_triplets_with_gemini(triplets_file: str, api_key: str, 
                                        output_dir: str, method: str = "function") -> str:
    """
    Process function triplets and generate patches using Gemini API.
    
    Args:
        triplets_file: Path to function triplets JSON file
        api_key: Gemini API key
        output_dir: Directory to save generated patches
        method: Generation method ("diff", "function", or "both")
        
    Returns:
        Path to generated patches file
    """
    logger.info(f"📁 Processing function triplets from: {triplets_file}")
    
    # Load function triplets
    with open(triplets_file, 'r') as f:
        triplets = json.load(f)
    
    # Initialize Gemini generator
    generator = GeminiPatchGenerator(api_key)
    
    # Process each triplet
    all_results = []
    for i, triplet in enumerate(triplets):
        logger.info(f"🔄 Processing triplet {i+1}/{len(triplets)}")
        try:
            result = generator.generate_patch(triplet, method=method)
            all_results.append(result)
        except Exception as e:
            logger.error(f"❌ Failed to process triplet {i+1}: {e}")
            all_results.append({
                "input_triplet": triplet.get("function_mapping", {}),
                "error": str(e),
                "success": False
            })
    
    # Update the original function-triplets.json file with Gemini results
    # Load the original triplets again to get the full structure
    with open(triplets_file, 'r') as f:
        original_triplets = json.load(f)
    
    # Create a mapping from function names to results for easy lookup
    results_map = {}
    for result in all_results:
        # Create a key using both PA and PC function names to match triplets
        input_triplet = result.get("input_triplet", {})
        pa_name = input_triplet.get("pa_function_name", "")
        pc_name = input_triplet.get("pc_function_name", "")
        key = f"{pa_name}::{pc_name}"
        results_map[key] = result
    
    # Add Gemini results to each triplet
    for triplet in original_triplets:
        function_mapping = triplet.get("function_mapping", {})
        pa_name = function_mapping.get("pa_function_name", "")
        pc_name = function_mapping.get("pc_function_name", "")
        key = f"{pa_name}::{pc_name}"
        
        # Add Gemini result if available
        if key in results_map:
            triplet["gemini_patch_generation"] = {
                "generation_timestamp": results_map[key].get("generation_timestamp"),
                "model_used": results_map[key].get("model_used"),
                "method": results_map[key].get("function_generation_result", {}).get("method") or 
                         results_map[key].get("diff_generation_result", {}).get("method"),
                "success": results_map[key].get("function_generation_result", {}).get("success") or 
                          results_map[key].get("diff_generation_result", {}).get("success"),
                "result": results_map[key].get("function_generation_result") or 
                         results_map[key].get("diff_generation_result"),
                "error": results_map[key].get("error") if not (results_map[key].get("function_generation_result", {}).get("success") or 
                                                               results_map[key].get("diff_generation_result", {}).get("success")) else None
            }
        else:
            # Mark as not processed by Gemini
            triplet["gemini_patch_generation"] = {
                "generation_timestamp": None,
                "model_used": None,
                "method": None,
                "success": False,
                "result": None,
                "error": "Not processed by Gemini"
            }
    
    # Save the updated triplets back to the original file
    with open(triplets_file, 'w') as f:
        json.dump(original_triplets, f, indent=2)
    
    logger.info(f"✅ Gemini patch generation results added to: {triplets_file}")
    
    # Also create a backup of the separate results file for reference
    backup_file = os.path.join(output_dir, "gemini-generated-patches-backup.json")
    with open(backup_file, 'w') as f:
        json.dump(all_results, f, indent=2)
    
    logger.info(f"📁 Backup of separate results saved to: {backup_file}")
    return triplets_file


if __name__ == "__main__":
    # Example usage
    import sys
    
    if len(sys.argv) < 3:
        print("Usage: python gemini_patch_generator.py <triplets_file> <api_key> [method]")
        print("Methods: diff, function, both (default: function)")
        sys.exit(1)
    
    triplets_file = sys.argv[1]
    api_key = sys.argv[2]
    method = sys.argv[3] if len(sys.argv) > 3 else "function"
    output_dir = os.path.dirname(triplets_file)
    
    process_function_triplets_with_gemini(triplets_file, api_key, output_dir, method)
