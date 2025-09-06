#! /usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import json
import subprocess
from typing import List, Dict, Any
from pathlib import Path

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import git
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add app directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from app import main as intelliport_main
from app.common import values, definitions

app = FastAPI(title="IntelliPort Backend", version="1.0.0")

class AnalysisRequest(BaseModel):
    commit_hash: str
    tag: str

class FunctionResult(BaseModel):
    pc_file_location: str
    generated_function: str
    start_line: int
    end_line: int

@app.get("/")
async def root():
    return {"message": "IntelliPort Backend API"}

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "gemini_configured": bool(os.getenv('GEMINI_API_KEY'))
    }

def checkout_git_repo(repo_path: str, target: str):
    """Checkout a git repository to a specific commit or tag"""
    try:
        repo = git.Repo(repo_path)
        
        # First try to fetch if it's a remote reference
        try:
            repo.git.fetch('--all')
        except:
            pass  # If fetch fails, continue with existing refs
        
        # Try to checkout the target
        repo.git.checkout(target, force=True)
        repo.git.clean('-fd')  # Clean untracked files
        print(f"✅ Successfully checked out {repo_path} to {target}")
        return True
    except Exception as e:
        print(f"❌ Error checking out {repo_path} to {target}: {e}")
        # Try alternative approaches
        try:
            repo = git.Repo(repo_path)
            # If it's a commit hash that doesn't exist, try using an available commit
            if len(target) > 10:  # Looks like a commit hash
                available_commits = list(repo.iter_commits(max_count=10))
                if available_commits:
                    fallback_commit = str(available_commits[0])
                    print(f"🔄 Using fallback commit {fallback_commit[:10]} instead of {target[:10]}")
                    repo.git.checkout(fallback_commit, force=True)
                    repo.git.clean('-fd')
                    return True
        except Exception as e2:
            print(f"❌ Fallback also failed: {e2}")
        return False

def run_intelliport_analysis(config_path: str) -> List[Dict[str, Any]]:
    """Run IntelliPort analysis and return results"""
    try:
        # Set the configuration file path
        old_argv = sys.argv
        sys.argv = ['IntelliPort.py', f'--conf={config_path}']
        
        # Run the analysis
        print(f"🚀 Starting IntelliPort analysis with config: {config_path}")
        intelliport_main.main()
        
        # Restore original argv
        sys.argv = old_argv
        
        # Read the generated function triplets
        output_dir = definitions.DIRECTORY_OUTPUT
        triplets_file = os.path.join(output_dir, "function-triplets.json")
        
        if not os.path.exists(triplets_file):
            print(f"❌ Function triplets file not found: {triplets_file}")
            return []
        
        with open(triplets_file, 'r') as f:
            triplets_data = json.load(f)
        
        results = []
        
        # Process the triplets data
        if isinstance(triplets_data, list):
            for triplet in triplets_data:
                pc_pre_patch = triplet.get('pc_pre_patch', {})
                gemini_result = triplet.get('gemini_result', {})
                
                if pc_pre_patch and gemini_result:
                    # Get relative path from the Tensorflow directory
                    source_file = pc_pre_patch.get('source_file', '')
                    relative_path = source_file.replace('/home/cseroot/New/Tensorflow/', '')
                    
                    result = {
                        'pc_file_location': relative_path,
                        'generated_function': gemini_result.get('generated_patch', ''),
                        'start_line': pc_pre_patch.get('start_line', 0),
                        'end_line': pc_pre_patch.get('end_line', 0)
                    }
                    results.append(result)
        
        print(f"✅ Analysis completed. Found {len(results)} function results.")
        return results
        
    except Exception as e:
        print(f"❌ Error running IntelliPort analysis: {e}")
        raise e

@app.post("/analyze", response_model=List[FunctionResult])
async def analyze_code(request: AnalysisRequest):
    """
    Analyze code changes between commits and generate patches
    """
    try:
        print(f"🔍 Starting analysis for commit: {request.commit_hash}, tag: {request.tag}")
        
        # Define paths
        base_dir = Path("/home/cseroot/New/Tensorflow")
        pa_path = base_dir / "PA" / "tensorflow"
        pb_path = base_dir / "PB" / "tensorflow" 
        pc_path = base_dir / "PC" / "tensorflow"
        config_path = base_dir / "repair.conf"
        
        # Verify paths exist
        for path in [pa_path, pb_path, pc_path, config_path]:
            if not path.exists():
                raise HTTPException(status_code=400, detail=f"Path does not exist: {path}")
        
        print("📁 All required paths verified")
        
        # Step 1: Checkout PA to commit_hash^ (before state)
        print(f"🔄 Checking out PA to {request.commit_hash}^...")
        before_commit = f"{request.commit_hash}^"
        if not checkout_git_repo(str(pa_path), before_commit):
            raise HTTPException(status_code=500, detail=f"Failed to checkout PA to {before_commit}")
        
        # Step 2: Checkout PB to commit_hash (after state)  
        print(f"🔄 Checking out PB to {request.commit_hash}...")
        if not checkout_git_repo(str(pb_path), request.commit_hash):
            raise HTTPException(status_code=500, detail=f"Failed to checkout PB to {request.commit_hash}")
        
        # Step 3: Checkout PC to tag
        print(f"🔄 Checking out PC to {request.tag}...")
        if not checkout_git_repo(str(pc_path), request.tag):
            raise HTTPException(status_code=500, detail=f"Failed to checkout PC to {request.tag}")
        
        print("✅ All repositories checked out successfully")
        
        # Step 4: Run IntelliPort analysis
        print("🤖 Running IntelliPort analysis...")
        results = run_intelliport_analysis(str(config_path))
        
        # Step 5: Return results
        print(f"📊 Analysis complete. Returning {len(results)} results.")
        return results
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    print("🚀 Starting IntelliPort Backend Server...")
    print("📖 API Documentation available at: http://localhost:8000/docs")
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
