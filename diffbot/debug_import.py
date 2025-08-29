#!/usr/bin/env python3
import asyncio
import aiohttp
import json
from dotenv import load_dotenv
import os
from diffbot_client import DiffbotClient

async def test():
    load_dotenv('config.env')
    token = os.getenv('DIFFBOT_TOKEN')
    base_url = os.getenv('DIFFBOT_API_BASE_URL', 'https://kg.diffbot.com/kg/v3')
    
    print(f"🔧 Debug Diffbot client:")
    print(f"  Token: {token[:10]}..." if token else "❌ No token found")
    print(f"  Base URL: {base_url}")
    
    if not token:
        print("❌ DIFFBOT_TOKEN not found in config.env")
        return
    
    # Test 1: Direct API call (like working test)
    print("\n📝 Test 1: Direct API call...")
    async with aiohttp.ClientSession() as session:
        params = {
            'token': token,
            'query': 'Elon Musk',
            'size': 5
        }
        
        async with session.get(f"{base_url}/dql", params=params) as response:
            print(f"  Status: {response.status}")
            if response.status == 200:
                data = await response.json()
                print(f"  ✅ Success! Found {len(data.get('data', []))} results")
            else:
                error_text = await response.text()
                print(f"  ❌ Error: {error_text}")
    
    # Test 2: Using DiffbotClient (like import script)
    print("\n📝 Test 2: Using DiffbotClient...")
    try:
        async with DiffbotClient(
            token=token,
            base_url=base_url,
            request_delay=1.0,
            max_retries=3,
            timeout=30,
            max_concurrent=5
        ) as client:
            print("  ✅ DiffbotClient initialized successfully")
            
            # Test search
            response = await client.search_entities(
                query='Elon Musk',
                size=5
            )
            
            if response and 'data' in response:
                print(f"  ✅ Search successful! Found {len(response['data'])} results")
            else:
                print(f"  ❌ Search failed: {response}")
                
    except Exception as e:
        print(f"  ❌ DiffbotClient error: {e}")

if __name__ == "__main__":
    asyncio.run(test())
