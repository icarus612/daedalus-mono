import os
import sys


def get_name():
  return os.path.basename(sys.argv[0]).split('.')[0]

def get_path(new_path=""):
	current_path = os.path.abspath(os.path.join(os.getcwd(), os.path.dirname(sys.argv[0]), new_path))
	
	return current_path
		
class ANN_Shell:	
	def __init__(self, name=get_name(), model_type='keras'):
		self.name = name
		self.model_type = model_type
		self.model = self.load_model()
	
	@property
	def file_name(self):
		return f'{self.name}.{self.model_type}'
	
	@property
	def model_location(self):
		return get_path(f'../models/{self.file_name}')
	
	def load_model(self, func=None):
		os.makedirs(os.path.dirname(self.model_location), exist_ok=True)
		with open(self.model_location, 'w+') as f:
			return func(f) if func else f.read()
		
	def save_model(self):
		self.load_model(lambda f: f.write(self.model))	

if __name__ == '__main__':
	ann_shell = ANN_Shell()
	to_print = ['name', 'model_type', 'file_name', 'file_location']
	
	for item in to_print:
		key = item.replace('_', ' ').title()
		val = getattr(ann_shell, item)
		print(f'{key}: {val}')