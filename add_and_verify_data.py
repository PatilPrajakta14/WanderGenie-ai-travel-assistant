"""Script to add data to GraphDB and verify it was added successfully."""

import logging
from backend.memory.graphdb import GraphDBClient

# Setup basic logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def add_sample_data(client):
    """Add sample POI data to the database."""
    print("\n" + "="*60)
    print("Adding Sample Data to GraphDB")
    print("="*60)
    
    try:
        # Create a neighborhood
        print("\n1. Creating neighborhood: SoHo, NYC")
        client.execute_query("""
            MERGE (n:Neighborhood {
                id: 'soho_nyc',
                name: 'SoHo',
                city: 'NYC'
            })
        """)
        print("   ✓ Neighborhood created")
        
        # Create POIs
        print("\n2. Creating POIs:")
        
        print("   - Adding 'The Drawing Center' (art gallery)")
        client.execute_query("""
            MERGE (p:POI {
                id: 'drawing_center_soho',
                name: 'The Drawing Center',
                lat: 40.7230,
                lon: -74.0030,
                category: 'art_gallery',
                popularity: 0.75
            })
        """)
        
        print("   - Adding 'Dominique Ansel Bakery' (bakery)")
        client.execute_query("""
            MERGE (p:POI {
                id: 'dominique_ansel_soho',
                name: 'Dominique Ansel Bakery',
                lat: 40.7235,
                lon: -74.0025,
                category: 'bakery',
                popularity: 0.88
            })
        """)
        
        print("   - Adding 'New York City Fire Museum' (museum)")
        client.execute_query("""
            MERGE (p:POI {
                id: 'fire_museum_soho',
                name: 'New York City Fire Museum',
                lat: 40.7245,
                lon: -74.0040,
                category: 'museum',
                popularity: 0.70
            })
        """)
        print("   ✓ All POIs created")
        
        # Create relationships
        print("\n3. Creating relationships:")
        
        print("   - Linking POIs to SoHo neighborhood")
        client.execute_query("""
            MATCH (p1:POI {id: 'drawing_center_soho'})
            MATCH (p2:POI {id: 'dominique_ansel_soho'})
            MATCH (p3:POI {id: 'fire_museum_soho'})
            MATCH (n:Neighborhood {id: 'soho_nyc'})
            
            MERGE (p1)-[:IN_NEIGHBORHOOD]->(n)
            MERGE (p2)-[:IN_NEIGHBORHOOD]->(n)
            MERGE (p3)-[:IN_NEIGHBORHOOD]->(n)
        """)
        
        print("   - Creating NEAR relationships (proximity)")
        client.execute_query("""
            MATCH (p1:POI {id: 'drawing_center_soho'})
            MATCH (p2:POI {id: 'dominique_ansel_soho'})
            MATCH (p3:POI {id: 'fire_museum_soho'})
            
            MERGE (p1)-[:NEAR {distance_km: 0.08}]->(p2)
            MERGE (p2)-[:NEAR {distance_km: 0.08}]->(p1)
            MERGE (p1)-[:NEAR {distance_km: 0.15}]->(p3)
            MERGE (p3)-[:NEAR {distance_km: 0.15}]->(p1)
        """)
        
        print("   - Creating SIMILAR_TO relationships (art venues)")
        client.execute_query("""
            MATCH (p1:POI {id: 'drawing_center_soho'})
            MATCH (p3:POI {id: 'fire_museum_soho'})
            
            MERGE (p1)-[:SIMILAR_TO {score: 0.65}]->(p3)
            MERGE (p3)-[:SIMILAR_TO {score: 0.65}]->(p1)
        """)
        print("   ✓ All relationships created")
        
        print("\n✓ Sample data added successfully!")
        
    except Exception as e:
        print(f"\n✗ Failed to add data: {e}")
        raise


def verify_data(client):
    """Verify the data was added correctly."""
    print("\n" + "="*60)
    print("Verifying Data in GraphDB")
    print("="*60)
    
    try:
        # Check total nodes
        print("\n1. Checking total nodes:")
        result = client.execute_query("""
            MATCH (n)
            WHERE n.id STARTS WITH 'soho_' OR n.id ENDS WITH '_soho'
            RETURN labels(n)[0] as type, count(n) as count
        """)
        for record in result:
            print(f"   - {record['type']}: {record['count']}")
        
        # Check POIs in SoHo
        print("\n2. Querying POIs in SoHo using find_pois_in_neighborhood():")
        pois = client.find_pois_in_neighborhood("NYC", "SoHo")
        print(f"   Found {len(pois)} POIs:")
        for poi in pois:
            print(f"   - {poi['name']} ({poi['category']}) - Popularity: {poi['popularity']}")
        
        # Check nearby POIs
        print("\n3. Finding nearby POIs to The Drawing Center:")
        nearby = client.find_nearby_pois(40.7230, -74.0030, radius_km=0.2)
        print(f"   Found {len(nearby)} nearby POIs:")
        for poi in nearby:
            print(f"   - {poi['name']} ({poi['distance_km']}km away)")
        
        # Check similar POIs
        print("\n4. Finding similar POIs to The Drawing Center:")
        similar = client.find_similar_pois("drawing_center_soho", limit=5)
        print(f"   Found {len(similar)} similar POIs:")
        for poi in similar:
            print(f"   - {poi['name']} (Similarity: {poi['similarity_score']})")
        
        # Check relationships
        print("\n5. Checking relationships:")
        result = client.execute_query("""
            MATCH (p:POI)-[r]->(target)
            WHERE p.id ENDS WITH '_soho'
            RETURN type(r) as relationship_type, count(r) as count
        """)
        for record in result:
            print(f"   - {record['relationship_type']}: {record['count']}")
        
        print("\n✓ All data verified successfully!")
        
    except Exception as e:
        print(f"\n✗ Verification failed: {e}")
        raise


def view_graph_structure(client):
    """Display the graph structure."""
    print("\n" + "="*60)
    print("Graph Structure Visualization")
    print("="*60)
    
    try:
        result = client.execute_query("""
            MATCH (p:POI)-[r]->(target)
            WHERE p.id ENDS WITH '_soho'
            RETURN p.name as from_poi, type(r) as relationship, 
                   labels(target)[0] as target_type,
                   CASE 
                       WHEN target:POI THEN target.name
                       WHEN target:Neighborhood THEN target.name
                       ELSE 'Unknown'
                   END as target_name
            ORDER BY from_poi, relationship
        """)
        
        print("\nGraph connections:")
        current_poi = None
        for record in result:
            if current_poi != record['from_poi']:
                current_poi = record['from_poi']
                print(f"\n{current_poi}:")
            print(f"  --[{record['relationship']}]--> {record['target_name']} ({record['target_type']})")
        
    except Exception as e:
        print(f"\n✗ Failed to visualize graph: {e}")


def main():
    """Main execution."""
    print("\n" + "="*60)
    print("GraphDB Data Addition & Verification")
    print("="*60)
    
    # Connect to database
    print("\nConnecting to Neo4j...")
    client = GraphDBClient()
    
    try:
        client.connect()
        print("✓ Connected successfully")
        
        # Add data
        add_sample_data(client)
        
        # Verify data
        verify_data(client)
        
        # View structure
        view_graph_structure(client)
        
        print("\n" + "="*60)
        print("Success! Data added and verified ✓")
        print("="*60)
        print("\nYou can view this data in Neo4j Browser:")
        print("1. Go to https://browser.neo4j.io/")
        print("2. Connect using your credentials")
        print("3. Run: MATCH (n) WHERE n.id ENDS WITH '_soho' RETURN n")
        print("\nTo clean up this data, run:")
        print("MATCH (n) WHERE n.id STARTS WITH 'soho_' OR n.id ENDS WITH '_soho' DETACH DELETE n")
        
    except Exception as e:
        print(f"\n✗ Error: {e}")
        
    finally:
        client.close()
        print("\n✓ Connection closed")


if __name__ == "__main__":
    main()
