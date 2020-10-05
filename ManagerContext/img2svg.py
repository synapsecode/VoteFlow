#curl $ curl --http1.1 -H 'Expect:' --data-binary "@dps.png" "https://www.vectorizer.io/api/v2/vectorize" -v > dps.svg

import subprocess
import time
from PIL import Image
from resizeimage import resizeimage

def img2svg(filename):
	start = time.time()
	try:
		aspectRatio = (96,96)
		# Resize Image
		with open(filename, 'r+b') as f:
		    with Image.open(f) as image:
		        cover = resizeimage.resize_cover(image, [aspectRatio[0],aspectRatio[1]])
		        cover.save(filename, image.format)

		#Perform Vectorization
		url = "https://www.vectorizer.io/api/v2/vectorize"
		cmd = f"""curl $ curl --http1.1 -H 'Expect:' --data-binary "@{filename}" "{url}" > {filename.split('.')[0]}.svg """
		out = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE).stdout.read()
		print(f"Completed In: {int(time.time() - start)}s")
		return {'status': 200, 'svg': f"{filename.split('.')[0]}.svg"}
	except Exception as e:
		return {'status': 500, 'errcode': str(e)}

converted = img2svg('C:/Users/manas/OneDrive/Desktop/index.jpg')
print(converted)

