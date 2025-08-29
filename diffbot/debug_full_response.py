#!/usr/bin/env python3
import asyncio
import aiohttp
import json
from dotenv import load_dotenv
import os

async def test():
    load_dotenv('config.env')
    token = os.getenv('DIFFBOT_TOKEN')
    base_url = os.getenv('DIFFBOT_API_BASE_URL', 'https://kg.diffbot.com/kg/v3')
    
    print(f"🔧 Capturing full Diffbot response:")
    print(f"  Token: {token[:10]}..." if token else "❌ No token found")
    
    if not token:
        print("❌ DIFFBOT_TOKEN not found in config.env")
        return
    
    async with aiohttp.ClientSession() as session:
        params = {
            'token': token,
            'query': 'Elon Musk',
            'size': 3
        }
        
        async with session.get(f"{base_url}/dql", params=params) as response:
            print(f"Status: {response.status}")
            if response.status == 200:
                data = await response.json()
                print(f"✅ Success! Found {len(data.get('data', []))} results")
                
                # Save full response to file for inspection
                with open('diffbot_response.json', 'w') as f:
                    json.dump(data, f, indent=2)
                print("💾 Full response saved to diffbot_response.json")
                
                # Check for any time-related fields
                print("\n🔍 Checking for time-related fields...")
                for i, item in enumerate(data.get('data', [])[:2]):
                    if 'entity' in item:
                        entity = item['entity']
                        print(f"\nEntity {i+1}: {entity.get('name', 'No name')}")
                        
                        # Look for fields that might contain time data
                        for key, value in entity.items():
                            if isinstance(value, str) and any(time_word in value.lower() for time_word in ['days', 'hours', 'minutes', 'ago']):
                                print(f"  ⏰ {key}: {value}")
                            elif isinstance(value, dict) and any(time_word in str(value).lower() for time_word in ['days', 'hours', 'minutes', 'ago']):
                                print(f"  ⏰ {key}: {value}")
            else:
                error_text = await response.text()
                print(f"❌ Error: {error_text}")

if __name__ == "__main__":
    asyncio.run(test())
