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
            'query': 'Microsoft',
            'size': 5
        }
        
        async with session.get('https://kg.diffbot.com/kg/v3/dql', params=params) as response:
            if response.status == 200:
                data = await response.json()
                entities = data.get('data', [])
                
                print(f'Full response structure for first entity:')
                if entities and 'entity' in entities[0]:
                    first_entity = entities[0]['entity']
                    print(json.dumps(first_entity, indent=2))
                    
                    # Check if there are other type fields
                    print(f'\nChecking for alternative type fields:')
                    for key, value in first_entity.items():
                        if 'type' in key.lower():
                            print(f'  {key}: {value}')
            else:
                error_text = await response.text()
                print(f'❌ Error: {error_text}')

if __name__ == "__main__":
    asyncio.run(test())
