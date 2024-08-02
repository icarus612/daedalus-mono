import argparse

def build_deck(cards, savefile='built-deck.txt', delimiter='|'):
		filename = savefile + '.txt' if not savefile.endswith('.txt') else savefile
		with open(filename, 'w') as f:
				for card in cards:
						f.write(f' {delimiter} '.join(card) + '\n')

def build_decks(items, delimiter='|'):
		for name, cards in items.items():
				build_deck(cards, name, delimiter)
    
  
  
if __name__ == '__main__':
	parser = argparse.ArgumentParser(description='Build Anki decks from a dictionary')
	parser.add_argument('cardsfile', type=str, help='The cards to add to the deck')
	parser.add_argument('--savefile', '-sf', type=str, default='built-deck.txt', help='The name of the file')
	parser.add_argument('--delimiter', '-d', type=str, default='|', help='The delimiter to use between fields')
	args = parser.parse_known_args()
	with open(args.cardsfile, 'r') as f:
		cards = f.readlines()
		cards = [card.strip().split(args.delimiter) for card in cards]
	
	build_decks(cards, args.savefile, args.delimiter)