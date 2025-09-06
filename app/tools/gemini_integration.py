#! /usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import json
import os

import google.generativeai as genai
from dotenv import load_dotenv


def load_environment_config():
    env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), '.env')
    
    try:
        load_dotenv(env_path)
    except Exception as e:
        pass
    
    config = {
        'api_key': os.getenv('GEMINI_API_KEY'),
        'model': os.getenv('GEMINI_MODEL', 'gemini-2.0-flash-exp'),
        'method': os.getenv('GEMINI_METHOD', 'function')
    }
    
    return config


def process_function_triplets_with_gemini(triplets_file, api_key, output_dir=None, method="semantic"):
    try:
        with open(triplets_file, 'r') as f:
            data = json.load(f)
        
        # Handle both list format (new) and dict format (old)
        if isinstance(data, list):
            triplets = data
        else:
            triplets = data.get('function_triplets', [])
        
        if not triplets:
            raise ValueError("No function triplets found in " + triplets_file)
        
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-2.0-flash-exp')
        
        gemini_results = []
        
        for i, triplet in enumerate(triplets):
            try:
                if method == "function":
                    # Extract function content from the new format
                    function_a = triplet.get('pa_pre_patch', {}).get('content', '')
                    function_b = triplet.get('pb_post_patch', {}).get('content', '')  
                    function_c = triplet.get('pc_pre_patch', {}).get('content', '')
                    
                    prompt = f"""Generate a patch for the following code context:

FUNCTION A (Original):
{function_a}

FUNCTION B (Target):
{function_b}

FUNCTION C (Current):
{function_c}

Generate a patch that transforms Function C to match the semantic behavior of Function B.
Return only the corrected function code without explanations."""
                
                    response = model.generate_content(prompt)
                    patch_content = response.text.strip()
                    
                    triplet_id = triplet.get('function_mapping', {}).get('pa_function_name', f"triplet_{i}")
                    
                    gemini_results.append({
                        "triplet_index": i,
                        "triplet_id": triplet_id,
                        "method": method,
                        "prompt": prompt,
                        "generated_patch": patch_content
                    })
                    
            except Exception as e:
                print(f"Error processing triplet {i}: {e}")
                continue
        
        # Add gemini_results to the original data structure
        if isinstance(data, list):
            # For list format, add gemini_results to each triplet
            for i, result in enumerate(gemini_results):
                if i < len(data):
                    data[i]['gemini_result'] = result
        else:
            # For dict format, add as separate key
            data['gemini_results'] = gemini_results
        
        with open(triplets_file, 'w') as f:
            json.dump(data, f, indent=2)
        
        return triplets_file
        
    except Exception as e:
        raise RuntimeError(f"Failed to process with Gemini API: {e}")


def integrate_gemini_patch_generation(output_dir, api_key=None, method=None):
    config = load_environment_config()
    
    if api_key is None:
        api_key = config['api_key']
    if method is None:
        method = config['method']
    
    if not api_key:
        raise ValueError(
            "Gemini API key not found. Please:\n"
            "1. Copy .env.example to .env\n"
            "2. Add your API key to the .env file: GEMINI_API_KEY=your-key-here\n"
            "3. Or set the GEMINI_API_KEY environment variable"
        )
    
    triplets_filename = "function-triplets.json"
    triplets_file = os.path.join(output_dir, triplets_filename)
    if not os.path.exists(triplets_file):
        raise FileNotFoundError("Function triplets file not found: " + triplets_file)
    
    patches_file = process_function_triplets_with_gemini(
        triplets_file=triplets_file,
        api_key=api_key,
        output_dir=output_dir,
        method=method
    )
    
    return patches_file


def generate_patches_with_gemini_cli():
    parser = argparse.ArgumentParser(description="Generate patches using Gemini API")
    parser.add_argument("--output-dir", required=True, help="Output directory containing function triplets")
    parser.add_argument("--api-key", help="Gemini API key (or configure in .env file)")
    parser.add_argument("--method", choices=["diff", "function", "both"], 
                       help="Generation method (or configure in .env file)")
    parser.add_argument("--verbose", "-v", action="store_true", help="Enable verbose logging")
    
    args = parser.parse_args()
    
    if args.verbose:
        pass
    
    try:
        patches_file = integrate_gemini_patch_generation(
            output_dir=args.output_dir,
            api_key=args.api_key,
            method=args.method
        )
        print(f"Generated patches saved to: {patches_file}")
    except Exception as e:
        print(f"Error: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    exit(generate_patches_with_gemini_cli())
