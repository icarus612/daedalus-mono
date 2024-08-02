import argparse
import requests
import os
from bs4 import BeautifulSoup as soup


def crawl_page(language, output_file='output', audio_dir='audio_files'):
	page =  soup(requests.get(f'http://www.nemolanguageapps.com/phrasebooks/{language}').content, 'html.parser')
	cards = []
	if not os.path.isdir(audio_dir):
		os.mkdir(audio_dir)

	for raw_card in page.find('table', {'class': 'nemocards'}).find_all('tr'):
		tds = raw_card.find_all('td')
		audio_url = tds[0].find('audio').find('source')['src']
		card = [i.text for i in tds[1].find_all('div')]
		audio_name = f'ic_{card[1].replace(" ", "_").replace("...", "")}.mp3'
		audio = requests.get(f'http://www.nemolanguageapps.com/{audio_url}').content

		card.append(f'[sound:{audio_name}]')
		cards.append(card)
		
		with open(os.path.join(audio_dir, audio_name), 'wb') as audio_file:
			audio_file.write(audio)
		
	with open(f'{output_file}.txt', 'w') as file:
		file.writelines([f'{" | ".join(i)} \n' for i in cards])	
		
if __name__ == '__main__':
	parser = argparse.ArgumentParser()
	parser.add_argument('language', type=str, help='The language to use for the TTS')
	parser.add_argument('--output_file', '-o', default='output', type=str, help='The name of the output file')
	parser.add_argument('--audio_dir', '-d', default='audio_files', type=str, help='The name of the output file')
	parser.add_argument('--split_char', '-s', default='|', type=str, help='The name of the output file')
	args = parser.parse_args()    
	
	crawl_page(args.language, output_file=args.output_file, audio_dir=args.audio_dir)
