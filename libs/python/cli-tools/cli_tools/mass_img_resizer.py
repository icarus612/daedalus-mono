from img_resizer import resize

def mass_resize(images_data):
	for data in images_data:
		
		height, width = data['size']
		resize(data['src'], f"{data['src']}_resize_{height}_{width}", (height, width))
  
if __name__ == "__main__":
  mass_resize([{'src': 'path_to_input_dir', 'size': (800, 600)}])