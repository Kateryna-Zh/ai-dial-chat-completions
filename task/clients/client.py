from aidial_client import Dial, AsyncDial

from task.clients.base import BaseClient
from task.constants import DIAL_ENDPOINT
from task.models.message import Message
from task.models.role import Role


class DialClient(BaseClient):

    def __init__(self, deployment_name: str):
        super().__init__(deployment_name)
        # Documentation: https://pypi.org/project/aidial-client/ (here you can find how to create and use these clients)
        # 1. Create Dial client
        self.client = Dial(api_key=self._api_key, base_url= DIAL_ENDPOINT)
        # 2. Create AsyncDial client
        self.async_client = AsyncDial(base_url=DIAL_ENDPOINT, api_key=self._api_key)

    def get_completion(self, messages: list[Message]) -> Message:
        # 1. Create chat completions with client
        #    Hint: to unpack messages you can use the `to_dict()` method from Message object
        response = self.client.chat.completions.create(
            deployment_name=self._deployment_name,
            stream=False,
            messages=[message.to_dict() for message in messages],
        )

        # 2. Get content from response, print it and return message with assistant role and content
        if response and response.choices:
            message = response.choices[0].message
            print(message.content)
            return Message(role=Role.AI, content=message.content)
        # 3. If choices are not present then raise Exception("No choices in response found")
        raise Exception("No choices in response found")

    async def stream_completion(self, messages: list[Message]) -> Message:
        # 1. Create chat completions with async client
        #    Hint: don't forget to add `stream=True` in call.
        completion = await self.async_client.chat.completions.create(
            deployment_name=self._deployment_name,
            stream=True,
            messages=[message.to_dict() for message in messages]
        )
        # 2. Create array with `contents` name (here we will collect all content chunks)
        contents = []
        # 3. Make async loop from `chunks` (from 1st step)
        async for chunk in completion:
            if chunk.choices:
                # 4. Print content chunk and collect it contents array
                delta = chunk.choices[0].delta
                if delta and delta.content:
                    print(delta.content, end='')
                    contents.append(delta.content)
        # 5. Print empty row `print()` (it will represent the end of streaming and in console we will print input from a new line)
        print()
        # 6. Return Message with assistant role and message collected content
        return Message(Role.AI, ''.join(contents))
        