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
        async with session.get('https://kg.diffbot.com/kg/v3/dql', 
                              params={'token': token, 'query': 'Person', 'size': 1}) as response:
            data = await response.json()
            print('Sample result:')
            print(json.dumps(data['data'][0] if data.get('data') else data, indent=2))

if __name__ == "__main__":
    asyncio.run(test())
