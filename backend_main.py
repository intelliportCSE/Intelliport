#! /usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import subprocess
import json
from typing import List, Dict, Any
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from dotenv import load_dotenv
from app import main as intelliport_main
from app.common import values, definitions
import tempfile
import shutil

# Load environment variables from .env file
load_dotenv()

app = FastAPI(title="IntelliPort API", description="Automated Code Transfer Backend", version="1.0.0")

class AnalysisRequest(BaseModel):
    commit_hash: str
    tag: str

class FunctionResult(BaseModel):
    pc_file_location: str
    generated_function: str
    start_line: int
    end_line: int

class AnalysisResponse(BaseModel):
    results: List[FunctionResult]
    status: str
    message: str

def run_git_command(directory: str, command: str):
    """Execute git command in specified directory"""
    try:
        result = subprocess.run(
            command, 
            shell=True, 
            cwd=directory, 
            capture_output=True, 
            text=True, 
            check=True
        )
        print(f"Git command successful in {directory}: {command}")
        print(f"Output: {result.stdout}")
        return result.stdout
    except subprocess.CalledProcessError as e:
        error_msg = f"Git command failed in {directory}: {command}\nError: {e.stderr}"
        print(error_msg)
        raise HTTPException(status_code=500, detail=error_msg)

def checkout_repositories(commit_hash: str, tag: str):
    """Checkout repositories to specified states"""
    base_path = "/home/cseroot/New/Tensorflow"
    
    # PA: checkout to before commit (commit_hash^)
    pa_path = os.path.join(base_path, "PA", "tensorflow")
    print(f"🔄 Checking out PA to {commit_hash}^...")
    run_git_command(pa_path, f"git checkout {commit_hash}^")
    
    # PB: checkout to after commit (commit_hash)
    pb_path = os.path.join(base_path, "PB", "tensorflow")
    print(f"🔄 Checking out PB to {commit_hash}...")
    run_git_command(pb_path, f"git checkout {commit_hash}")
    
    # PC: checkout to tag
    pc_path = os.path.join(base_path, "PC", "tensorflow")
    print(f"🔄 Checking out PC to tag {tag}...")
    run_git_command(pc_path, f"git checkout {tag}")
    
    print("✅ All repositories checked out successfully")

def run_intelliport_analysis():
    """Run IntelliPort analysis with Tensorflow config"""
    config_path = "/home/cseroot/New/Tensorflow/repair.conf"
    
    if not os.path.exists(config_path):
        raise HTTPException(status_code=404, detail=f"Config file not found: {config_path}")
    
    print("🚀 Starting IntelliPort analysis...")
    
    try:
        # Run the complete analysis using the main run function
        intelliport_main.run(config_path)
        
        # Run Gemini AI Patch Generation
        print("🤖 Running Gemini AI Patch Generation...")
        from app.tools.gemini_integration import integrate_gemini_patch_generation
        
        output_dir = definitions.DIRECTORY_OUTPUT
        integrate_gemini_patch_generation(output_dir)
        
        print("✅ IntelliPort analysis completed successfully")
        
    except Exception as e:
        error_msg = f"IntelliPort analysis failed: {str(e)}"
        print(f"❌ {error_msg}")
        raise HTTPException(status_code=500, detail=error_msg)

def extract_results():
    """Extract results from function-triplets.json"""
    output_file = os.path.join(definitions.DIRECTORY_OUTPUT, "function-triplets.json")
    
    if not os.path.exists(output_file):
        raise HTTPException(status_code=404, detail="Results file not found")
    
    try:
        with open(output_file, 'r') as f:
            data = json.load(f)
        
        results = []
        
        # Handle both list and dict formats
        triplets = data if isinstance(data, list) else data.get('function_triplets', [])
        
        for triplet in triplets:
            # Extract PC pre-patch information
            pc_pre_patch = triplet.get('pc_pre_patch', {})
            gemini_result = triplet.get('gemini_result', {})
            
            if pc_pre_patch and gemini_result:
                # Make file path relative to project root
                pc_file_path = pc_pre_patch.get('source_file', '')
                relative_path = os.path.relpath(pc_file_path, '/home/cseroot/New')
                
                result = FunctionResult(
                    pc_file_location=relative_path,
                    generated_function=gemini_result.get('generated_patch', ''),
                    start_line=pc_pre_patch.get('start_line', 0),
                    end_line=pc_pre_patch.get('end_line', 0)
                )
                results.append(result)
        
        return results
        
    except Exception as e:
        error_msg = f"Failed to extract results: {str(e)}"
        print(f"❌ {error_msg}")
        raise HTTPException(status_code=500, detail=error_msg)

@app.post("/analyze", response_model=AnalysisResponse)
async def analyze_code_changes(request: AnalysisRequest):
    """
    Analyze code changes between commits and generate patches
    
    - **commit_hash**: The commit hash to analyze
    - **tag**: The tag of tensorflow library to compare against
    """
    try:
        print(f"🎯 Starting analysis for commit: {request.commit_hash}, tag: {request.tag}")
        
        # Step 1: Checkout repositories
        checkout_repositories(request.commit_hash, request.tag)
        
        # Step 2: Run IntelliPort analysis
        run_intelliport_analysis()
        
        # Step 3: Extract results
        results = extract_results()
        
        print(f"✅ Analysis completed successfully. Found {len(results)} results.")
        
        return AnalysisResponse(
            results=results,
            status="success",
            message=f"Analysis completed successfully for commit {request.commit_hash} and tag {request.tag}"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        error_msg = f"Unexpected error during analysis: {str(e)}"
        print(f"❌ {error_msg}")
        raise HTTPException(status_code=500, detail=error_msg)

@app.get("/")
async def root():
    """Health check endpoint"""
    return {"message": "IntelliPort Backend API is running", "version": "1.0.0"}

@app.get("/health")
async def health_check():
    """Detailed health check"""
    config_exists = os.path.exists("/home/cseroot/New/Tensorflow/repair.conf")
    tensorflow_dirs = {
        "PA": os.path.exists("/home/cseroot/New/Tensorflow/PA/tensorflow"),
        "PB": os.path.exists("/home/cseroot/New/Tensorflow/PB/tensorflow"),
        "PC": os.path.exists("/home/cseroot/New/Tensorflow/PC/tensorflow")
    }
    
    return {
        "status": "healthy",
        "config_file_exists": config_exists,
        "tensorflow_directories": tensorflow_dirs,
        "gemini_api_configured": bool(os.getenv('GEMINI_API_KEY'))
    }

if __name__ == "__main__":
    import uvicorn
    print("🚀 Starting IntelliPort Backend...")
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
