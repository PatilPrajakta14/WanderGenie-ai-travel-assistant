"""Test script to verify VectorDB connection and embedding generation."""

import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from backend.memory.vectordb import VectorDBClient
from backend.utils.config import settings

def test_connection():
    """Test Supabase connection."""
    print("=" * 60)
    print("Testing VectorDB Connection")
    print("=" * 60)
    
    try:
        # Initialize client
        print("\n1. Initializing VectorDBClient...")
        client = VectorDBClient()
        print(f"   ✓ Client initialized")
        print(f"   - Supabase URL: {settings.supabase_url}")
        print(f"   - Embedding Model: {client.embedding_model}")
        
        # Test connection
        print("\n2. Testing Supabase connection...")
        client.connect()
        print("   ✓ Successfully connected to Supabase!")
        
        return client
        
    except Exception as e:
        print(f"   ✗ Connection failed: {str(e)}")
        return None


def test_embeddings(client):
    """Test embedding generation."""
    print("\n" + "=" * 60)
    print("Testing Embedding Generation")
    print("=" * 60)
    
    if not client:
        print("   ✗ Skipping - no client connection")
        return
    
    test_texts = [
        "The Statue of Liberty is an iconic landmark in New York City",
        "Central Park offers a peaceful escape in the heart of Manhattan",
        "The Empire State Building provides stunning views of the city"
    ]
    
    try:
        for i, text in enumerate(test_texts, 1):
            print(f"\n{i}. Testing embedding for: '{text[:50]}...'")
            
            # Generate embedding
            embedding = client._generate_embedding(text)
            
            print(f"   ✓ Embedding generated successfully")
            print(f"   - Dimensions: {len(embedding)}")
            print(f"   - Sample values: [{embedding[0]:.4f}, {embedding[1]:.4f}, {embedding[2]:.4f}, ...]")
            print(f"   - Min value: {min(embedding):.4f}")
            print(f"   - Max value: {max(embedding):.4f}")
            
            # Verify dimensions
            if len(embedding) == 1536:
                print(f"   ✓ Correct dimensions (1536)")
            else:
                print(f"   ✗ Incorrect dimensions (expected 1536, got {len(embedding)})")
        
        # Test caching
        print("\n4. Testing embedding cache...")
        print("   Generating embedding for same text twice...")
        
        import time
        
        # First call
        start = time.time()
        embedding1 = client._generate_embedding(test_texts[0])
        time1 = time.time() - start
        
        # Second call (should be cached)
        start = time.time()
        embedding2 = client._generate_embedding(test_texts[0])
        time2 = time.time() - start
        
        print(f"   - First call: {time1:.4f}s")
        print(f"   - Second call: {time2:.4f}s (cached)")
        
        if embedding1 == embedding2:
            print(f"   ✓ Cache working correctly (embeddings match)")
        else:
            print(f"   ✗ Cache issue (embeddings don't match)")
        
        if time2 < time1 * 0.1:  # Cached should be much faster
            print(f"   ✓ Cache performance verified (>10x faster)")
        else:
            print(f"   ⚠ Cache may not be working optimally")
            
    except Exception as e:
        print(f"   ✗ Embedding generation failed: {str(e)}")
        import traceback
        traceback.print_exc()


def test_similarity():
    """Test cosine similarity calculation."""
    print("\n" + "=" * 60)
    print("Testing Cosine Similarity")
    print("=" * 60)
    
    try:
        client = VectorDBClient()
        
        # Test with simple vectors
        print("\n1. Testing with identical vectors...")
        vec1 = [1.0, 0.0, 0.0]
        vec2 = [1.0, 0.0, 0.0]
        similarity = client._cosine_similarity(vec1, vec2)
        print(f"   Similarity: {similarity:.4f}")
        if abs(similarity - 1.0) < 0.001:
            print(f"   ✓ Correct (expected ~1.0)")
        else:
            print(f"   ✗ Incorrect (expected ~1.0)")
        
        print("\n2. Testing with orthogonal vectors...")
        vec1 = [1.0, 0.0, 0.0]
        vec2 = [0.0, 1.0, 0.0]
        similarity = client._cosine_similarity(vec1, vec2)
        print(f"   Similarity: {similarity:.4f}")
        if abs(similarity - 0.0) < 0.001:
            print(f"   ✓ Correct (expected ~0.0)")
        else:
            print(f"   ✗ Incorrect (expected ~0.0)")
        
        print("\n3. Testing with opposite vectors...")
        vec1 = [1.0, 0.0, 0.0]
        vec2 = [-1.0, 0.0, 0.0]
        similarity = client._cosine_similarity(vec1, vec2)
        print(f"   Similarity: {similarity:.4f}")
        if abs(similarity - (-1.0)) < 0.001:
            print(f"   ✓ Correct (expected ~-1.0)")
        else:
            print(f"   ✗ Incorrect (expected ~-1.0)")
            
    except Exception as e:
        print(f"   ✗ Similarity test failed: {str(e)}")


def main():
    """Run all tests."""
    print("\n" + "=" * 60)
    print("VectorDB Connection & Embedding Test Suite")
    print("=" * 60)
    
    # Test connection
    client = test_connection()
    
    # Test embeddings
    test_embeddings(client)
    
    # Test similarity
    test_similarity()
    
    print("\n" + "=" * 60)
    print("Test Suite Complete")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    main()
