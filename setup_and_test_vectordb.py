"""Setup Supabase tables and test with sample data."""

import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from backend.memory.vectordb import VectorDBClient
from backend.utils.config import settings

# Sample POI data for NYC
SAMPLE_POIS = [
    {
        "id": "poi_001",
        "name": "Statue of Liberty",
        "city": "NYC",
        "booking_required": True,
        "booking_url": "https://www.statueofliberty.org/",
        "hours_text": "9:00 AM - 5:00 PM",
        "tags": ["landmark", "monument", "outdoor", "historical"],
        "popularity": 9.5,
        "body": "The Statue of Liberty is a colossal neoclassical sculpture on Liberty Island in New York Harbor. A gift from France, it has become an iconic symbol of freedom and democracy. Visitors can take a ferry to the island and climb to the crown for spectacular views of Manhattan."
    },
    {
        "id": "poi_002",
        "name": "Central Park",
        "city": "NYC",
        "booking_required": False,
        "hours_text": "6:00 AM - 1:00 AM",
        "tags": ["park", "outdoor", "nature", "recreation"],
        "popularity": 9.8,
        "body": "Central Park is an urban park in Manhattan, offering 843 acres of green space in the heart of the city. Features include walking paths, lakes, playgrounds, and the famous Bethesda Fountain. Perfect for picnics, jogging, or simply escaping the city bustle."
    },
    {
        "id": "poi_003",
        "name": "Empire State Building",
        "city": "NYC",
        "booking_required": True,
        "booking_url": "https://www.esbnyc.com/",
        "hours_text": "8:00 AM - 2:00 AM",
        "tags": ["landmark", "observation", "architecture", "indoor"],
        "popularity": 9.3,
        "body": "The Empire State Building is a 102-story Art Deco skyscraper in Midtown Manhattan. Its observation decks on the 86th and 102nd floors offer breathtaking 360-degree views of New York City. The building is beautifully lit at night with changing colors."
    },
    {
        "id": "poi_004",
        "name": "Metropolitan Museum of Art",
        "city": "NYC",
        "booking_required": False,
        "hours_text": "10:00 AM - 5:00 PM (Closed Mondays)",
        "tags": ["museum", "art", "culture", "indoor", "educational"],
        "popularity": 9.4,
        "body": "The Met is one of the world's largest and finest art museums. Its collection spans 5,000 years of art from around the world, including Egyptian artifacts, European paintings, and American decorative arts. The rooftop garden offers stunning views of Central Park."
    },
    {
        "id": "poi_005",
        "name": "Times Square",
        "city": "NYC",
        "booking_required": False,
        "hours_text": "24/7",
        "tags": ["landmark", "entertainment", "shopping", "outdoor"],
        "popularity": 8.9,
        "body": "Times Square is a major commercial intersection and entertainment hub in Midtown Manhattan. Known for its bright billboards, Broadway theaters, and bustling atmosphere. It's especially spectacular at night when all the digital displays are illuminated."
    },
    {
        "id": "poi_006",
        "name": "Brooklyn Bridge",
        "city": "NYC",
        "booking_required": False,
        "hours_text": "24/7",
        "tags": ["landmark", "bridge", "outdoor", "historical", "walking"],
        "popularity": 9.1,
        "body": "The Brooklyn Bridge is a hybrid cable-stayed suspension bridge connecting Manhattan and Brooklyn. Walking across the bridge offers stunning views of the Manhattan skyline and East River. It's a historic engineering marvel completed in 1883."
    },
    {
        "id": "poi_007",
        "name": "9/11 Memorial & Museum",
        "city": "NYC",
        "booking_required": True,
        "booking_url": "https://www.911memorial.org/",
        "hours_text": "9:00 AM - 8:00 PM",
        "tags": ["memorial", "museum", "historical", "indoor", "educational"],
        "popularity": 9.2,
        "body": "The National September 11 Memorial & Museum honors the victims of the 2001 and 1993 terrorist attacks. The memorial features two reflecting pools in the footprints of the Twin Towers. The museum provides a powerful and moving experience with artifacts and stories."
    },
    {
        "id": "poi_008",
        "name": "High Line",
        "city": "NYC",
        "booking_required": False,
        "hours_text": "7:00 AM - 10:00 PM",
        "tags": ["park", "outdoor", "walking", "art", "urban"],
        "popularity": 8.7,
        "body": "The High Line is an elevated linear park built on a historic freight rail line on Manhattan's West Side. It features beautiful gardens, public art installations, and unique views of the city. A perfect spot for a leisurely stroll with food vendors along the way."
    }
]


def setup_table():
    """Read and display SQL setup instructions."""
    print("=" * 60)
    print("Supabase Table Setup")
    print("=" * 60)
    print("\nTo set up the database tables, follow these steps:")
    print("\n1. Go to your Supabase Dashboard")
    print("2. Navigate to: SQL Editor")
    print("3. Create a new query")
    print("4. Copy and paste the contents of 'setup_supabase_tables.sql'")
    print("5. Run the query")
    print("\nThe SQL file will:")
    print("   - Enable pgvector extension")
    print("   - Create poi_facts table with proper schema")
    print("   - Create indexes for fast similarity search")
    print("   - Create a match_poi_facts() function for queries")
    print("\n" + "=" * 60)
    
    response = input("\nHave you run the SQL setup? (yes/no): ").strip().lower()
    return response == 'yes' or response == 'y'


def insert_sample_data(client):
    """Insert sample POI data."""
    print("\n" + "=" * 60)
    print("Inserting Sample Data")
    print("=" * 60)
    
    try:
        # Verify collection exists
        print("\n1. Verifying poi_facts table exists...")
        client.create_collection("poi_facts", {})
        print("   ✓ Table verified")
        
        # Insert documents
        print(f"\n2. Inserting {len(SAMPLE_POIS)} sample POIs...")
        result = client.insert_documents("poi_facts", SAMPLE_POIS)
        
        print(f"\n   Results:")
        print(f"   ✓ Successfully inserted: {result['success']}")
        print(f"   ✗ Failed: {result['failed']}")
        
        if result['errors']:
            print(f"\n   Errors:")
            for error in result['errors'][:3]:  # Show first 3 errors
                print(f"   - {error}")
        
        return result['success'] > 0
        
    except Exception as e:
        print(f"   ✗ Error inserting data: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def test_similarity_search(client):
    """Test similarity search with various queries."""
    print("\n" + "=" * 60)
    print("Testing Similarity Search")
    print("=" * 60)
    
    test_queries = [
        ("outdoor activities and nature", 3),
        ("historical landmarks and monuments", 3),
        ("museums and art galleries", 2),
        ("places with great views of the city", 3),
    ]
    
    for query, k in test_queries:
        print(f"\n{'─' * 60}")
        print(f"Query: '{query}'")
        print(f"Top {k} results:")
        print(f"{'─' * 60}")
        
        try:
            results = client.similarity_search(
                collection_name="poi_facts",
                query=query,
                k=k
            )
            
            if results:
                for i, result in enumerate(results, 1):
                    print(f"\n{i}. {result['name']}")
                    print(f"   City: {result['city']}")
                    print(f"   Tags: {', '.join(result.get('tags', []))}")
                    print(f"   Similarity: {result['similarity_score']:.4f}")
                    print(f"   Description: {result['body'][:100]}...")
            else:
                print("   No results found")
                
        except Exception as e:
            print(f"   ✗ Search failed: {str(e)}")


def test_filtered_search(client):
    """Test similarity search with filters."""
    print("\n" + "=" * 60)
    print("Testing Filtered Search")
    print("=" * 60)
    
    print(f"\n{'─' * 60}")
    print(f"Query: 'family friendly activities'")
    print(f"Filter: city = 'NYC'")
    print(f"{'─' * 60}")
    
    try:
        results = client.similarity_search(
            collection_name="poi_facts",
            query="family friendly activities",
            k=3,
            filters={"city": "NYC"}
        )
        
        if results:
            for i, result in enumerate(results, 1):
                print(f"\n{i}. {result['name']}")
                print(f"   Booking Required: {result.get('booking_required', 'N/A')}")
                print(f"   Hours: {result.get('hours_text', 'N/A')}")
                print(f"   Similarity: {result['similarity_score']:.4f}")
        else:
            print("   No results found")
            
    except Exception as e:
        print(f"   ✗ Search failed: {str(e)}")


def main():
    """Run setup and tests."""
    print("\n" + "=" * 60)
    print("VectorDB Setup & Test Suite")
    print("=" * 60)
    
    # Check if SQL setup is done
    if not setup_table():
        print("\nPlease run the SQL setup first, then run this script again.")
        return
    
    # Initialize client
    print("\n" + "=" * 60)
    print("Initializing VectorDB Client")
    print("=" * 60)
    
    try:
        client = VectorDBClient()
        client.connect()
        print("   ✓ Connected to Supabase")
    except Exception as e:
        print(f"   ✗ Connection failed: {str(e)}")
        return
    
    # Insert sample data
    if insert_sample_data(client):
        # Test searches
        test_similarity_search(client)
        test_filtered_search(client)
    
    print("\n" + "=" * 60)
    print("Setup & Test Complete!")
    print("=" * 60)
    print("\nYour VectorDB is now ready to use!")
    print("You can now:")
    print("  - Insert more POI data")
    print("  - Perform similarity searches")
    print("  - Use filters to narrow results")
    print("\n")


if __name__ == "__main__":
    main()
