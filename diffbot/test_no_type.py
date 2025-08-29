#!/usr/bin/env python3
import asyncio
import aiohttp
import json
from dotenv import load_dotenv
import os

async def test():
    load_dotenv('config.env')
    token = os.getenv('DIFFBOT_TOKEN')
    
    async with aiohttp.ClientSession() as session:
        # Test without type parameter
        params = {
            'token': token,
            'query': 'technology',
            'size': 5
        }
        
        async with session.get('https://kg.diffbot.com/kg/v3/dql', params=params) as response:
            print(f'Status: {response.status}')
            if response.status == 200:
                data = await response.json()
                print(f'✅ Success! Found {len(data.get("data", []))} results')
                if data.get('data'):
                    print(f'First result type: {data["data"][0].get("entity", {}).get("types", ["No types"])}')
            else:
                error_text = await response.text()
                print(f'❌ Error: {error_text}')

if __name__ == "__main__":
    asyncio.run(test())
