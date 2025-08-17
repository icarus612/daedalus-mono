import os
import itertools
from anki.collection import Collection

def get_anki_collection_path():
    if os.name == 'nt':  # Windows
        return os.path.expanduser("~\\AppData\\Roaming\\Anki2\\User 1\\collection.anki2")
    elif os.name == 'posix':  # macOS/Linux
        return os.path.expanduser("~/.local/share/Anki2/User 1/collection.anki2")
    else:
        raise OSError("Unsupported operating system")

def get_deck_info(col):
    decks = col.decks.all()
    deck_info = []
    
    # Get all deck config/options groups
    all_config = col.decks.all_config()
    config_dict = {conf['id']: conf['name'] for conf in all_config}
    
    for deck in decks:
        deck_id = deck['id']
        deck_name = deck['name']
        config_id = deck.get('conf')
        options_group_name = config_dict.get(config_id, "Default")
        
        deck_info.append({
            'name': deck_name,
            'options_group': options_group_name
        })
    
    return deck_info

def sort_by_deck_type(deck_info):
    sorted_deck_info = sorted(deck_info, key=lambda x: x['options_group'])
    group_deck = itertools.groupby(sorted_deck_info, key=lambda x: x['options_group'])
    return {key: list(group) for key, group in group_deck}

def pdash():
    print("-" * 50)

def main():
    try:
        collection_path = get_anki_collection_path()
        col = Collection(collection_path)
        
        deck_info = get_deck_info(col)
        deck_by_group = sort_by_deck_type(deck_info)

        print("\nDecks by Group:")
        for group, decks in deck_by_group.items():
            deck_string = "\n\t".join([deck['name'] for deck in decks])
            pdash()
            print(f"Options Group: {group}")
            pdash()
            print(f"Decks: \n\t{deck_string}")
        
        col.close()
    except Exception as e:
        print(f"An error occurred: {str(e)}")
        print("Make sure Anki is not running when you execute this script.")

if __name__ == "__main__":
    main()