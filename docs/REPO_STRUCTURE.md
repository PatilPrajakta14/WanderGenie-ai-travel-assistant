# 📦 WanderGenie Repository Structure

This document outlines the complete folder structure for the WanderGenie project.

## Directory Layout

```
wandergenie/
│
├── frontend/                    # Next.js app
│   ├── app/
│   │   ├── page.tsx            # Main chat interface
│   │   ├── layout.tsx
│   │   └── api/
│   ├── components/
│   │   ├── Chat.tsx            # Chat pane
│   │   ├── Itinerary.tsx       # Timeline view
│   │   ├── Map.tsx             # Interactive map
│   │   ├── BookingLinks.tsx    # Flight/hotel buttons
│   │   ├── CalendarButton.tsx  # Export calendar
│   │   └── StatusChips.tsx     # Agent progress
│   ├── lib/
│   │   ├── api.ts              # Backend API client
│   │   └── types.ts            # TypeScript types
│   └── public/
│
├── backend/                     # Python FastAPI
│   ├── main.py                 # API entry point
│   ├── agents/
│   │   ├── __init__.py
│   │   ├── planner.py          # Planner agent
│   │   ├── researcher.py       # Researcher agent
│   │   ├── packager.py         # Packager-Executor agent
│   │   └── graph.py            # LangGraph setup
│   ├── tools/
│   │   ├── __init__.py
│   │   ├── poi.py              # POI search
│   │   ├── distance.py         # Distance calculations
│   │   ├── links.py            # Deep link builders
│   │   ├── calendar.py         # Calendar export
│   │   ├── geo.py              # GeoJSON generation
│   │   └── validate.py         # Schema validator
│   ├── memory/
│   │   ├── __init__.py
│   │   ├── vectordb.py         # pgvector client
│   │   └── graphdb.py          # Neo4j client
│   ├── schemas/
│   │   └── trip.py             # Pydantic models
│   └── utils/
│       ├── config.py
│       └── logger.py
│
├── data/                        # Seed data
│   ├── nyc_pois.json           # Offline POI cache
│   ├── nyc_booking_required.json
│   ├── poi_facts.csv           # VectorDB seed
│   └── neo4j_seed.cypher       # GraphDB seed
│
├── infra/                       # AWS/deployment
│   ├── lambda/
│   ├── terraform/
│   └── docker-compose.yml      # Local dev
│
├── scripts/
│   ├── seed_vectordb.py        # Populate pgvector
│   ├── seed_graphdb.py         # Populate Neo4j
│   └── embed_data.py           # Generate embeddings
│
├── docs/
│   ├── ARCHITECTURE.md         # This file
│   ├── API.md                  # API documentation
│   └── DEMO_SCRIPT.md          # Demo walkthrough
│
├── requirements.txt
├── package.json
├── .env.example
└── README.md
```

