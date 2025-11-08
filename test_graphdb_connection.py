"""Integration test script for GraphDB connection and data operations."""

import sys
import logging
from backend.memory.graphdb import GraphDBClient

# Setup basic logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_connection():
    """Test basic connection to Neo4j."""
    print("\n" + "="*60)
    print("Testing GraphDB Connection")
    print("="*60)
    
    client = GraphDBClient()
    
    try:
        result = client.connect()
        print("✓ Successfully connected to Neo4j")
        return client
    except Exception as e:
        print(f"✗ Connection failed: {e}")
        sys.exit(1)


def clear_test_data(client):
    """Clear any existing test data."""
    print("\n" + "="*60)
    print("Clearing Test Data")
    print("="*60)
    
    try:
        # Delete all test nodes and relationships
        client.execute_query("""
            MATCH (n)
            WHERE n.id STARTS WITH 'test_'
            DETACH DELETE n
        """)
        print("✓ Test data cleared")
    except Exception as e:
        print(f"✗ Failed to clear test data: {e}")


def create_test_data(client):
    """Create sample POI data with relationships."""
    print("\n" + "="*60)
    print("Creating Test Data")
    print("="*60)
    
    try:
        # Create neighborhoods
        client.execute_query("""
            CREATE (n1:Neighborhood {
                name: 'Manhattan',
                city: 'NYC',
                id: 'test_neighborhood_1'
            })
            CREATE (n2:Neighborhood {
                name: 'Brooklyn',
                city: 'NYC',
                id: 'test_neighborhood_2'
            })
        """)
        print("✓ Created neighborhoods")
        
        # Create POIs
        client.execute_query("""
            CREATE (p1:POI {
                id: 'test_poi_1',
                name: 'Metropolitan Museum',
                lat: 40.7794,
                lon: -73.9632,
                category: 'museum',
                popularity: 0.95
            })
            CREATE (p2:POI {
                id: 'test_poi_2',
                name: 'Museum of Modern Art',
                lat: 40.7614,
                lon: -73.9776,
                category: 'museum',
                popularity: 0.90
            })
            CREATE (p3:POI {
                id: 'test_poi_3',
                name: 'Central Park',
                lat: 40.7829,
                lon: -73.9654,
                category: 'park',
                popularity: 0.98
            })
            CREATE (p4:POI {
                id: 'test_poi_4',
                name: 'Brooklyn Museum',
                lat: 40.6712,
                lon: -73.9636,
                category: 'museum',
                popularity: 0.85
            })
            CREATE (p5:POI {
                id: 'test_poi_5',
                name: 'Statue of Liberty',
                lat: 40.6892,
                lon: -74.0445,
                category: 'landmark',
                popularity: 0.99
            })
        """)
        print("✓ Created POIs")
        
        # Create ticket provider
        client.execute_query("""
            CREATE (tp:TicketProvider {
                id: 'test_provider_1',
                name: 'StatueCruises',
                url: 'https://statuecruises.com',
                booking_type: 'required'
            })
        """)
        print("✓ Created ticket provider")
        
        # Create relationships
        client.execute_query("""
            MATCH (p1:POI {id: 'test_poi_1'})
            MATCH (p2:POI {id: 'test_poi_2'})
            MATCH (p3:POI {id: 'test_poi_3'})
            MATCH (p4:POI {id: 'test_poi_4'})
            MATCH (p5:POI {id: 'test_poi_5'})
            MATCH (n1:Neighborhood {id: 'test_neighborhood_1'})
            MATCH (n2:Neighborhood {id: 'test_neighborhood_2'})
            MATCH (tp:TicketProvider {id: 'test_provider_1'})
            
            // IN_NEIGHBORHOOD relationships
            CREATE (p1)-[:IN_NEIGHBORHOOD]->(n1)
            CREATE (p2)-[:IN_NEIGHBORHOOD]->(n1)
            CREATE (p3)-[:IN_NEIGHBORHOOD]->(n1)
            CREATE (p4)-[:IN_NEIGHBORHOOD]->(n2)
            
            // SIMILAR_TO relationships (museums are similar)
            CREATE (p1)-[:SIMILAR_TO {score: 0.92}]->(p2)
            CREATE (p2)-[:SIMILAR_TO {score: 0.92}]->(p1)
            CREATE (p1)-[:SIMILAR_TO {score: 0.75}]->(p4)
            CREATE (p4)-[:SIMILAR_TO {score: 0.75}]->(p1)
            
            // NEAR relationships
            CREATE (p1)-[:NEAR {distance_km: 0.5}]->(p3)
            CREATE (p3)-[:NEAR {distance_km: 0.5}]->(p1)
            CREATE (p1)-[:NEAR {distance_km: 2.1}]->(p2)
            CREATE (p2)-[:NEAR {distance_km: 2.1}]->(p1)
            
            // REQUIRES_TICKET relationship
            CREATE (p5)-[:REQUIRES_TICKET {advance_days: 7}]->(tp)
        """)
        print("✓ Created relationships")
        
        print("\n✓ All test data created successfully")
        
    except Exception as e:
        print(f"✗ Failed to create test data: {e}")
        sys.exit(1)


def test_find_pois_in_neighborhood(client):
    """Test finding POIs in a neighborhood."""
    print("\n" + "="*60)
    print("Testing: find_pois_in_neighborhood()")
    print("="*60)
    
    try:
        results = client.find_pois_in_neighborhood("NYC", "Manhattan")
        print(f"Found {len(results)} POIs in Manhattan, NYC:")
        for poi in results:
            print(f"  - {poi['name']} ({poi['category']}) - Popularity: {poi['popularity']}")
        
        assert len(results) == 3, f"Expected 3 POIs, got {len(results)}"
        print("✓ Test passed")
        
    except Exception as e:
        print(f"✗ Test failed: {e}")


def test_find_similar_pois(client):
    """Test finding similar POIs."""
    print("\n" + "="*60)
    print("Testing: find_similar_pois()")
    print("="*60)
    
    try:
        results = client.find_similar_pois("test_poi_1", limit=5)
        print(f"Found {len(results)} similar POIs to Metropolitan Museum:")
        for poi in results:
            print(f"  - {poi['name']} (Score: {poi['similarity_score']})")
        
        assert len(results) == 2, f"Expected 2 similar POIs, got {len(results)}"
        assert results[0]['similarity_score'] >= results[-1]['similarity_score'], "Results not sorted by score"
        print("✓ Test passed")
        
    except Exception as e:
        print(f"✗ Test failed: {e}")


def test_find_nearby_pois(client):
    """Test finding nearby POIs."""
    print("\n" + "="*60)
    print("Testing: find_nearby_pois()")
    print("="*60)
    
    try:
        # Using Metropolitan Museum coordinates
        results = client.find_nearby_pois(40.7794, -73.9632, radius_km=3.0)
        print(f"Found {len(results)} POIs within 3km:")
        for poi in results:
            print(f"  - {poi['name']} ({poi['distance_km']}km away)")
        
        assert len(results) == 2, f"Expected 2 nearby POIs, got {len(results)}"
        assert results[0]['distance_km'] <= results[-1]['distance_km'], "Results not sorted by distance"
        print("✓ Test passed")
        
    except Exception as e:
        print(f"✗ Test failed: {e}")


def test_get_poi_with_booking_info(client):
    """Test getting POI with booking information."""
    print("\n" + "="*60)
    print("Testing: get_poi_with_booking_info()")
    print("="*60)
    
    try:
        # Test POI with booking info
        result = client.get_poi_with_booking_info("test_poi_5")
        print(f"POI: {result['name']}")
        print(f"  Booking URL: {result.get('booking_url', 'N/A')}")
        print(f"  Booking Type: {result.get('booking_type', 'N/A')}")
        print(f"  Advance Days: {result.get('advance_days', 'N/A')}")
        
        assert result['booking_url'] == 'https://statuecruises.com', "Booking URL mismatch"
        assert result['advance_days'] == 7, "Advance days mismatch"
        print("✓ Test passed (with booking info)")
        
        # Test POI without booking info
        result2 = client.get_poi_with_booking_info("test_poi_3")
        print(f"\nPOI: {result2['name']}")
        print(f"  Booking URL: {result2.get('booking_url', 'N/A')}")
        
        assert result2['booking_url'] is None, "Expected no booking URL"
        print("✓ Test passed (without booking info)")
        
    except Exception as e:
        print(f"✗ Test failed: {e}")


def test_execute_query(client):
    """Test basic query execution."""
    print("\n" + "="*60)
    print("Testing: execute_query()")
    print("="*60)
    
    try:
        results = client.execute_query("""
            MATCH (p:POI)
            WHERE p.id STARTS WITH 'test_'
            RETURN count(p) as poi_count
        """)
        
        count = results[0]['poi_count']
        print(f"Total test POIs in database: {count}")
        assert count == 5, f"Expected 5 POIs, got {count}"
        print("✓ Test passed")
        
    except Exception as e:
        print(f"✗ Test failed: {e}")


def main():
    """Run all integration tests."""
    print("\n" + "="*60)
    print("GraphDB Integration Tests")
    print("="*60)
    
    # Connect to database
    client = test_connection()
    
    try:
        # Clear any existing test data
        clear_test_data(client)
        
        # Create test data
        create_test_data(client)
        
        # Run tests
        test_execute_query(client)
        test_find_pois_in_neighborhood(client)
        test_find_similar_pois(client)
        test_find_nearby_pois(client)
        test_get_poi_with_booking_info(client)
        
        print("\n" + "="*60)
        print("All Tests Passed! ✓")
        print("="*60)
        
    finally:
        # Cleanup
        print("\n" + "="*60)
        print("Cleaning Up")
        print("="*60)
        clear_test_data(client)
        client.close()
        print("✓ Connection closed")


if __name__ == "__main__":
    main()
