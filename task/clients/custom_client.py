import json
import aiohttp
import requests

from task.clients.base import BaseClient
from task.constants import DIAL_ENDPOINT
from task.models.message import Message
from task.models.role import Role


class CustomDialClient(BaseClient):
    _endpoint: str
    _api_key: str

    def __init__(self, deployment_name: str):
        super().__init__(deployment_name)
        self._endpoint = DIAL_ENDPOINT + f"/openai/deployments/{deployment_name}/chat/completions"

    def get_completion(self, messages: list[Message]) -> Message:
        # Take a look at README.md of how the request and regular response are looks like!
        # 1. Create headers dict with api-key and Content-Type
        headers = {
            "Api-Key": self._api_key,
            "Content-Type": "application/json"
        }
        # 2. Create request_data dictionary with:
        #   - "messages": convert messages list to dict format using msg.to_dict() for each message
        request_data = {"messages": [m.to_dict() for m in messages]}
        # 3. Make POST request using requests.post() with:
        #   - URL: self._endpoint
        #   - headers: headers from step 1
        #   - json: request_data from step 2
        response = requests.post(url=self._endpoint, headers=headers, json=request_data)
        # 4. Get content from response, print it and return message with assistant role and content
        # 5. If status code != 200 then raise Exception with format: f"HTTP {response.status_code}: {response.text}"
        
        if response.status_code != 200:
            raise Exception(f"HTTP {response.status_code}: {response.text}")
       
        data = response.json()
        choices = data.get("choices", [])
        if not choices:
            raise Exception("No choices in response")
        content = choices[0]["message"].get("content", " ")
        print(content)
        return Message(role=Role.AI, content=content)
        
    async def stream_completion(self, messages: list[Message]) -> Message:
        # Take a look at README.md of how the request and streamed response chunks are looks like!
        # 1. Create headers dict with api-key and Content-Type
        headers = {
            "Api-Key": self._api_key,
            "Content-Type": "application/json"
        }
        # 2. Create request_data dictionary with:
        #    - "stream": True  (enable streaming)
        #    - "messages": convert messages list to dict format using msg.to_dict() for each message
        request_data = {
            "messages": [m.to_dict() for m in messages],
            "stream": True
            }
        # 3. Create empty list called 'contents' to store content snippets
        contents = []
        # 4. Create aiohttp.ClientSession() using 'async with' context manager
        async with aiohttp.ClientSession() as session:
        # 5. Inside session, make POST request using session.post() with:
        #    - URL: self._endpoint
        #    - json: request_data from step 2
        #    - headers: headers from step 1
        #    - Use 'async with' context manager for response
            async with session.post(url=self._endpoint, json=request_data, headers=headers) as response:
        # 6. Get content from chunks (don't forget that chunk start with `data: `, final chunk is `data: [DONE]`), print
        #    chunks, collect them and return as assistant message
                if response.status != 200:
                    error_text = await response.text()
                    raise Exception(f"{response.status} {error_text}")

                async for row_chunk in response.content:
                    line = row_chunk.decode("utf-8").strip()
                    if line.startswith("data: "):
                        data = line[6:].strip()
                        if data != "[DONE]":
                            content_piece = self._get_content_snippet(data)
                            print(content_piece, end="")
                            contents.append(content_piece)
                    else:
                        print()
                
        return Message(role=Role.AI, content=''.join(contents))

    
    def _get_content_snippet(self, data: str) -> str:
        data = json.loads(data)

        choices = data.get("choices", [])
        if not choices:
            return ""

        delta = choices[0].get("delta", {})

        content = delta.get("content", "")
        if content is None:
            return ""
        return content.replace("\n", "")




