# 🏞 ➡ ️📼
Simple program to turn a sequence of images into a video, given a list of urls of the images

This was written for usage in AWS lambda. In my case to turn a set of presigned S3 image urls into a video and upload it.

One cool thing about this piece, is that images are downloaded and muxed into the video with a streaming pattern. Currently it will maximally download 10 images at a time over HTTP/2. This result is accomplished by an async generator bounded by a semaphore using python's excellent asyncio. ❤️

# Build
build and run
```
docker build -t myfunc:latest .
docker run -p 9000:8080  myfunc:latest
```
# Invocation
```
curl -X POST "http://localhost:9000/2015-03-31/functions/function/invocations" -d '{{
	"image_urls": [
		<image1>,	<image2>
	],
	"upload_url": "<upload_url>"
}}'
```
