import subprocess
import time
from PIL import Image
from resizeimage import resizeimage

def img2svg(filename):
	start = time.time()
	try:
		#Perform Vectorization
		url = "https://www.vectorizer.io/api/v2/vectorize"
		cmd = f"""curl $ curl --http1.1 -H 'Expect:' --data-binary "@{filename}" "{url}" > {filename.split('.')[0]}.svg """
		out = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE).stdout.read()
		print(f"Completed In: {int(time.time() - start)}s")
		return {'status': 200, 'svg': f"{filename.split('.')[0]}.svg"}
	except Exception as e:
		return {'status': 500, 'errcode': str(e)}
