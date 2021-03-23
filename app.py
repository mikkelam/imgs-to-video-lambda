import asyncio
import io
import logging

import av
import httpx
from PIL import Image

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def handler(event, context):
    success = asyncio.run(main(event), debug=True)
    response = {
        "statusCode": 200,
        "success": success
    }
    return response


async def main(event):
    images = event['image_urls']
    upload_url = event['upload_url']

    video_binary = await make_video(images)

    logger.info(f"Uploading video")
    r = httpx.post(upload_url, content=video_binary,
                   headers={"content-type": "video/mp4"}
                   )
    return r.status_code == 200


async def img_downloader(img_urls):
    client = httpx.AsyncClient(http2=True)
    semaphore = asyncio.Semaphore(10)

    async def get_image(url):
        async with semaphore:
            resp = await client.get(url)
            return Image.open(resp)

    tasks = [asyncio.create_task(get_image(img_url))
             for img_url in img_urls]

    for t in tasks:
        yield t

    await client.aclose()


async def make_video(images):
    buffer = io.BytesIO()
    output = av.open(buffer, 'w', format='mp4', options={'crf': '18'})
    stream = output.add_stream('h264', 24)
    finished = 0
    async for img in img_downloader(images):
        img = await img
        frame = av.VideoFrame.from_image(img)
        packet = stream.encode(frame)
        output.mux(packet)
        finished += 1
        logger.info(f'Finished frame {finished}')
    packet = stream.encode(None)
    output.mux(packet)

    return buffer.read()
