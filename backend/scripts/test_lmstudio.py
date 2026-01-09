#!/usr/bin/env python3
"""
LMStudio Connectivity Test Script

Tests connectivity to LMStudio (local LLM) and embedding model configuration.
Requires LMStudio to be running locally (default: http://localhost:1234).

This script verifies:
1. LMStudio server is accessible
2. LLM model is loaded and working
3. Embedding model is configured and working (if EMBEDDING_MODEL is set)
"""

import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "backend" / "src"))

# Load environment variables from .env file
from dotenv import load_dotenv
env_path = project_root / ".env"
if env_path.exists():
    load_dotenv(dotenv_path=env_path)
else:
    print(f"⚠️  Warning: .env file not found at {env_path}")
    print("   Using default values. Create .env from .env.example")

try:
    import litellm
    import requests
    from datetime import datetime
    print("✓ litellm and requests libraries imported successfully")
except ImportError as e:
    print(f"✗ Failed to import required libraries: {e}")
    print("  Install with: pip install litellm>=1.30.0 requests>=2.31.0")
    sys.exit(1)


def test_lmstudio_server():
    """Test LMStudio server availability"""
    print("\n" + "="*60)
    print("TEST 1: LMStudio Server Availability")
    print("="*60)
    
    api_base = os.getenv("LM_STUDIO_API_BASE", "http://localhost:1234/v1")
    print(f"\nUsing LM Studio API base: {api_base}")
    
    try:
        response = requests.get(f"{api_base}/models", timeout=5)
        response.raise_for_status()
        models_data = response.json()
        models = models_data.get("data", [])
        
        print(f"✓ Success: LM Studio server is running")
        if models:
            model_names = [m.get("id", "unknown") for m in models]
            print(f"  Available models ({len(models)}):")
            for i, name in enumerate(model_names[:10], 1):
                print(f"    {i}. {name}")
            if len(models) > 10:
                print(f"    ... and {len(models) - 10} more")
            return True, model_names
        else:
            print(f"  ⚠️  Warning: No models found. Load models in LM Studio.")
            return False, []
    except requests.exceptions.ConnectionError:
        print(f"✗ Failed: Cannot connect to LM Studio server at {api_base}")
        print("  Please ensure:")
        print("    1. LM Studio is installed from: https://lmstudio.ai/")
        print("    2. LM Studio application is running")
        print("    3. Models are loaded in LM Studio")
        print("    4. Local server is started (usually on port 1234)")
        return False, []
    except Exception as e:
        print(f"✗ Failed: {e}")
        return False, []


def test_llm_model():
    """Test LLM model chat completion"""
    print("\n" + "="*60)
    print("TEST 2: LLM Model Chat Completion")
    print("="*60)
    
    api_base = os.getenv("LM_STUDIO_API_BASE", "http://localhost:1234/v1")
    model_name = os.getenv("LM_STUDIO_MODEL", "local-model")
    
    print(f"\nTesting LLM model: {model_name}")
    print(f"API base: {api_base}")
    
    # Set API base for LiteLLM
    os.environ["OPENAI_API_BASE"] = api_base
    
    # Set dummy API key for LMStudio (it doesn't validate it)
    if not os.getenv("OPENAI_API_KEY"):
        os.environ["OPENAI_API_KEY"] = "lm-studio"
    
    try:
        # Format model name for LiteLLM (openai/ prefix)
        if not model_name.startswith("openai/"):
            litellm_model = f"openai/{model_name}"
        else:
            litellm_model = model_name
        
        print(f"Using LiteLLM model format: {litellm_model}")
        
        response = litellm.completion(
            model=litellm_model,
            messages=[
                {"role": "user", "content": "Say 'Hello, LM Studio LLM test successful!' and nothing else."}
            ],
            max_tokens=20,
            timeout=10,
            api_base=api_base
        )
        
        if response and response.choices:
            content = response.choices[0].message.content
            print(f"✓ Success: LLM model is working")
            print(f"  Response: {content[:100]}...")
            return True
        else:
            print(f"✗ Failed: No response from LLM model")
            return False
            
    except Exception as e:
        print(f"✗ Failed: {e}")
        print("  Please ensure:")
        print("    1. LM Studio is running")
        print("    2. LLM model is loaded in LM Studio")
        print("    3. Model name matches LM_STUDIO_MODEL in .env")
        print("    4. Local server is started")
        return False


def test_embedding_model():
    """Test embedding model"""
    print("\n" + "="*60)
    print("TEST 3: Embedding Model")
    print("="*60)
    
    api_base = os.getenv("LM_STUDIO_API_BASE", "http://localhost:1234/v1")
    embedding_provider = os.getenv("EMBEDDING_PROVIDER", "")
    embedding_model = os.getenv("EMBEDDING_MODEL", "")
    llm_provider = os.getenv("LLM_PROVIDER", "lmstudio")
    
    # Determine effective provider and model
    effective_provider = embedding_provider if embedding_provider else llm_provider
    
    if effective_provider != "lmstudio":
        print(f"⚠️  Skipping: Embedding provider is '{effective_provider}', not 'lmstudio'")
        print(f"   (Set EMBEDDING_PROVIDER=lmstudio to test LMStudio embeddings)")
        return None
    
    if not embedding_model:
        print(f"⚠️  Warning: EMBEDDING_MODEL not set")
        print(f"   The system will try to use LLM model for embeddings, which may not work")
        print(f"   Set EMBEDDING_MODEL in .env to your embedding model name")
        embedding_model = os.getenv("LM_STUDIO_MODEL", "local-model")
        print(f"   Using LLM model as fallback: {embedding_model}")
    
    print(f"\nTesting embedding model: {embedding_model}")
    print(f"API base: {api_base}")
    
    # Set API base and dummy key
    os.environ["OPENAI_API_BASE"] = api_base
    if not os.getenv("OPENAI_API_KEY"):
        os.environ["OPENAI_API_KEY"] = "lm-studio"
    
    try:
        # Format model name for LiteLLM
        if not embedding_model.startswith("openai/"):
            litellm_model = f"openai/{embedding_model}"
        else:
            litellm_model = embedding_model
        
        print(f"Using LiteLLM model format: {litellm_model}")
        
        test_text = "AAPL stock analysis"
        response = litellm.embedding(
            model=litellm_model,
            input=[test_text],
            api_base=api_base
        )
        
        if response and response.data:
            embedding = response.data[0]["embedding"]
            dimension = len(embedding)
            
            # Check for zero vectors
            is_all_zeros = all(x == 0.0 for x in embedding)
            
            if is_all_zeros:
                print(f"✗ Failed: Embedding is all zeros!")
                print(f"   This means semantic search will be disabled.")
                print(f"   Please ensure:")
                print(f"     1. Embedding model is loaded in LM Studio")
                print(f"     2. EMBEDDING_MODEL matches the model name in LM Studio")
                print(f"     3. The model supports embeddings (not all models do)")
                return False
            else:
                print(f"✓ Success: Embedding model is working")
                print(f"  Dimension: {dimension}")
                print(f"  Sample values: {embedding[:5]}")
                print(f"  Non-zero count: {sum(1 for x in embedding if x != 0.0)}/{dimension}")
                return True
        else:
            print(f"✗ Failed: No embedding data returned")
            return False
            
    except Exception as e:
        print(f"✗ Failed: {e}")
        print("  Please ensure:")
        print("    1. LM Studio is running")
        print("    2. Embedding model is loaded in LM Studio")
        print("    3. EMBEDDING_MODEL matches the model name in LM Studio")
        print("    4. The model supports embeddings")
        return False


def main():
    """Main test function"""
    print("\n" + "="*60)
    print("LMStudio Connectivity Test")
    print("="*60)
    print(f"Timestamp: {datetime.now().isoformat()}")
    print(f"Project root: {project_root}")
    
    # Check configuration
    print("\nConfiguration:")
    print(f"  LM_STUDIO_API_BASE: {os.getenv('LM_STUDIO_API_BASE', 'http://localhost:1234/v1')}")
    print(f"  LM_STUDIO_MODEL: {os.getenv('LM_STUDIO_MODEL', 'NOT SET')}")
    print(f"  LLM_PROVIDER: {os.getenv('LLM_PROVIDER', 'NOT SET')}")
    print(f"  EMBEDDING_PROVIDER: {os.getenv('EMBEDDING_PROVIDER', 'NOT SET (will use LLM_PROVIDER)')}")
    print(f"  EMBEDDING_MODEL: {os.getenv('EMBEDDING_MODEL', 'NOT SET')}")
    
    # Run tests
    results = []
    
    server_ok, models = test_lmstudio_server()
    results.append(("Server Availability", server_ok))
    
    if server_ok:
        llm_ok = test_llm_model()
        results.append(("LLM Model", llm_ok))
        
        embedding_result = test_embedding_model()
        if embedding_result is not None:
            results.append(("Embedding Model", embedding_result))
        else:
            results.append(("Embedding Model", None))
    else:
        results.append(("LLM Model", False))
        results.append(("Embedding Model", False))
    
    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    
    for test_name, result in results:
        if result is None:
            status = "⏭️  SKIPPED"
        elif result:
            status = "✓ PASSED"
        else:
            status = "✗ FAILED"
        print(f"{status}: {test_name}")
    
    all_passed = all(r for r in results if r is not None)
    
    print("\n" + "="*60)
    if all_passed:
        print("✓ ALL TESTS PASSED")
        print("\nLMStudio is configured correctly and ready to use.")
    else:
        print("✗ SOME TESTS FAILED")
        print("\nPlease check:")
        print("  - LM Studio is installed and running")
        print(f"  - Configuration in .env file at: {project_root / '.env'}")
        print("  - Models are loaded in LM Studio")
        print("  - Local server is started")
        if not os.getenv("EMBEDDING_MODEL"):
            print("\n⚠️  IMPORTANT: Set EMBEDDING_MODEL in .env for embedding support")
            print("   Example: EMBEDDING_MODEL=text-embedding-ada-002")
    print("="*60 + "\n")
    
    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())

