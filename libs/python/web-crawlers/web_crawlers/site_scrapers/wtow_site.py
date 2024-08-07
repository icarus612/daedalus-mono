from bs4 import BeautifulSoup as soup
import json 
import sys
import os

def short_stories():
	data = []
	file = "wtow.html"
	if len(sys.argv) > 1:
		file = sys.argv[1]

	def find_next(x):
		item = x.find_next()
		match item.name:
			case "p":
				return {
					"text": item.text
				}
			case "img":
				src = item['src'].split('/')[-1].split('.')
				return {
					"src": "/stories/" + src[0] + '.' + src[2]
				}
			case _: 
				return find_next(item)
				

	with open (file, 'r') as f:
		res = f.read()
		page = soup(res, 'lxml')
		for h3 in page.find_all("h3"):
			d = dict({
				"header": h3.text,
			})
			d.update(find_next(h3))
			data.append(d)

	with open ("scraped.json", 'w') as s:
		d = json.dumps({
			"sections": data 
		})
		s.write(d)

def new_testament():
	file = os.path.expanduser("~") + "/repos/live-websites/apps/the-wilderness-tabernacle-of-witness/public/new-testament"
	if len(sys.argv) > 1:
		file = sys.argv[1]
	data = os.listdir(file)
	
	with open ("scraped.json", 'w') as s:
		d = json.dumps({
			"sections": [
				{
					"header": a.split('.')[0].replace("_", " ").lower(),
					"src": "/new-testament/" + a
				} for a in data
			] 
		})
		s.write(d)


if __name__ == "__main__":
	new_testament()