from PIL import Image
import sys

def resize(input_image_path, output_image_path, size):
	
	original_image = Image.open(input_image_path)
	width, height = original_image.size
	print(f"Original: {width} x {height}")

	resized_image = original_image.resize(size)
	width, height = resized_image.size
	print(f"The resized image size is {width} wide x {height} tall")
	resized_image.show()
	resized_image.save(output_image_path)
		

if __name__ == "__main__":
	
	name, size = sys.argv[1:]
	if not name:
		name = input("Enter the name of the image: ")
	if not size:
		size = input("Enter the size of the image: ")
	
	size = (int(i) for i in size.split(","))
	resize(name, f"resized_{name}", size)