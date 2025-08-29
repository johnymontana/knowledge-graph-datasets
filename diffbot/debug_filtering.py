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
        params = {
            'token': token,
            'query': 'technology',
            'size': 10
        }
        
        async with session.get('https://kg.diffbot.com/kg/v3/dql', params=params) as response:
            if response.status == 200:
                data = await response.json()
                entities = data.get('data', [])
                print(f'Found {len(entities)} entities')
                
                # Show entity types
                for i, item in enumerate(entities[:5]):  # Show first 5
                    if 'entity' in item:
                        entity = item['entity']
                        entity_types = entity.get('types', [])
                        name = entity.get('name', 'No name')
                        print(f'{i+1}. {name} - Types: {entity_types}')
                        
                        # Check if it matches Person or Organization
                        if any(t in entity_types for t in ['Person', 'Organization']):
                            print(f'   ✅ Matches Person or Organization')
                        else:
                            print(f'   ❌ Does not match Person or Organization')
                    else:
                        print(f'{i+1}. No entity data')
            else:
                error_text = await response.text()
                print(f'❌ Error: {error_text}')

if __name__ == "__main__":
    asyncio.run(test())
