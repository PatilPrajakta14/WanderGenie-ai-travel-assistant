"""Diagnostic script for GraphDB connection issues."""

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv('backend/.env')

print("\n" + "="*60)
print("Neo4j Connection Diagnostics")
print("="*60)

# Check environment variables
neo4j_uri = os.getenv('NEO4J_URI')
neo4j_user = os.getenv('NEO4J_USER')
neo4j_password = os.getenv('NEO4J_PASSWORD')

print("\nEnvironment Variables:")
print(f"  NEO4J_URI: {neo4j_uri}")
print(f"  NEO4J_USER: {neo4j_user}")
print(f"  NEO4J_PASSWORD: {'*' * len(neo4j_password) if neo4j_password else 'NOT SET'}")

# Try to import neo4j
print("\nChecking neo4j package:")
try:
    import neo4j
    print(f"  ✓ neo4j package installed (version: {neo4j.__version__})")
except ImportError as e:
    print(f"  ✗ neo4j package not installed: {e}")
    print("\n  To install: pip install neo4j")
    exit(1)

# Try basic connection
print("\nAttempting connection:")
try:
    from neo4j import GraphDatabase
    
    driver = GraphDatabase.driver(
        neo4j_uri,
        auth=(neo4j_user, neo4j_password)
    )
    
    # Verify connectivity
    with driver.session() as session:
        result = session.run("RETURN 1 AS test")
        record = result.single()
        if record and record["test"] == 1:
            print("  ✓ Successfully connected to Neo4j!")
            
            # Get some database info
            result = session.run("CALL dbms.components() YIELD name, versions, edition")
            for record in result:
                print(f"\n  Database Info:")
                print(f"    Name: {record['name']}")
                print(f"    Version: {record['versions'][0]}")
                print(f"    Edition: {record['edition']}")
    
    driver.close()
    
except Exception as e:
    print(f"  ✗ Connection failed: {e}")
    print("\n  Troubleshooting tips:")
    print("    1. Verify the Neo4j instance is running")
    print("    2. Check if the URI is correct (should be neo4j+s://... for secure connection)")
    print("    3. Verify your credentials are correct")
    print("    4. Check if your IP is whitelisted in Neo4j Aura (if using cloud)")
    print("    5. Try accessing the Neo4j Browser at https://browser.neo4j.io/")

print("\n" + "="*60)
