import asyncio
import io
import logging

import av
import httpx
from PIL import Image

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def handler(event, context):
    success = asyncio.run(main(event))

    response = {
        "statusCode": 200,
        "success": success
    }
    return response


async def main(event):
    images = event['image_urls']
    upload_url = event['upload_url']
    queue = asyncio.Queue(maxsize=100)
    produce = asyncio.create_task(img_downloader(images, queue))
    video_binary = await make_video(queue)

    logger.info(f"Uploading img")
    r = httpx.post(upload_url, content=video_binary,
                   headers={"content-type": "video/mp4"}
                   )
    return r.status_code == 200


async def img_downloader(img_urls, queue):
    for img_url in img_urls:
        logger.info(f"Downloading {img_url}")
        r = httpx.get(img_url)

        image = Image.open(io.BytesIO(r.content))
        await queue.put(image)
    await queue.put(None)
    return


async def make_video(queue):
    with io.BytesIO() as buffer:
        output = av.open(buffer, 'w', format='mp4', options={'crf': '18'})
        stream = output.add_stream('h264', 24)
        while True:
            logger.info(f"Waiting for img")
            item = await queue.get()
            if item is None:
                logger.info(f"Done!")
                break

            frame = av.VideoFrame.from_image(item)
            packet = stream.encode(frame)
            output.mux(packet)
        packet = stream.encode(None)
        output.mux(packet)

        return buffer.read()
