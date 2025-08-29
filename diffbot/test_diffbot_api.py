#!/usr/bin/env python3
"""
Test script to debug Diffbot API calls
"""

import asyncio
import aiohttp
import json
from dotenv import load_dotenv
import os

async def test_diffbot_api():
    """Test basic Diffbot API functionality"""
    
    # Load environment variables
    load_dotenv('config.env')
    
    token = os.getenv('DIFFBOT_TOKEN')
    base_url = os.getenv('DIFFBOT_API_BASE_URL', 'https://kg.diffbot.com/kg/v3')
    
    print(f"🔧 Testing Diffbot API:")
    print(f"  Token: {token[:10]}..." if token else "❌ No token found")
    print(f"  Base URL: {base_url}")
    
    if not token:
        print("❌ DIFFBOT_TOKEN not found in config.env")
        return
    
    async with aiohttp.ClientSession() as session:
        # Test 1: Basic DQL endpoint
        print("\n📝 Test 1: Testing DQL endpoint...")
        dql_url = f"{base_url}/dql"
        params = {
            'token': token,
            'query': 'type:Person',
            'size': 10
        }
        
        try:
            async with session.get(dql_url, params=params) as response:
                print(f"  Status: {response.status}")
                print(f"  Headers: {dict(response.headers)}")
                
                if response.status == 200:
                    data = await response.json()
                    print(f"  ✅ Success! Found {len(data.get('data', []))} results")
                    if data.get('data'):
                        print(f"  First result: {data['data'][0].get('name', 'No name')}")
                else:
                    error_text = await response.text()
                    print(f"  ❌ Error: {error_text}")
                    
        except Exception as e:
            print(f"  ❌ Exception: {e}")
        
        # Test 2: KG endpoint
        print("\n📝 Test 2: Testing KG endpoint...")
        kg_url = f"{base_url}/kg"
        params = {
            'token': token,
            'id': 'test'
        }
        
        try:
            async with session.get(kg_url, params=params) as response:
                print(f"  Status: {response.status}")
                if response.status == 200:
                    data = await response.json()
                    print(f"  ✅ Success!")
                else:
                    error_text = await response.text()
                    print(f"  ❌ Error: {error_text}")
                    
        except Exception as e:
            print(f"  ❌ Exception: {e}")
        
        # Test 3: Different query format
        print("\n📝 Test 3: Testing different query format...")
        params = {
            'token': token,
            'query': 'Person',
            'size': 10
        }
        
        try:
            async with session.get(dql_url, params=params) as response:
                print(f"  Status: {response.status}")
                if response.status == 200:
                    data = await response.json()
                    print(f"  ✅ Success! Found {len(data.get('data', []))} results")
                else:
                    error_text = await response.text()
                    print(f"  ❌ Error: {error_text}")
                    
        except Exception as e:
            print(f"  ❌ Exception: {e}")

if __name__ == "__main__":
    asyncio.run(test_diffbot_api())
