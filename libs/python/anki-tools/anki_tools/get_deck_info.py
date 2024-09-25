import os
from anki.collection import Collection
from anki.utils import int_time

def get_anki_collection_path():
    # Adjust this path based on your operating system and Anki profile
    if os.name == 'nt':  # Windows
        return os.path.expanduser("~\\AppData\\Roaming\\Anki2\\User 1\\collection.anki2")
    elif os.name == 'posix':  # macOS/Linux
        return os.path.expanduser("~/.local/share/Anki2/User 1/collection.anki2")
    else:
        raise OSError("Unsupported operating system")

def get_deck_info(col):
    decks = col.decks.all()
    deck_info = []

    for deck in decks:
        conf = col.decks.config_dict_for_deck_dict(deck)
        deck_id = deck['id']
        deck_name = deck['name']
        
        # Get card count
        card_count = col.db.scalar(
            f"SELECT count() FROM cards WHERE did = ?",
            deck_id
        )
        
        # Get review stats for last 30 days
        thirty_days_ago = int_time() - (30 * 86400)
        review_count = col.db.scalar(
            f"SELECT count() FROM revlog WHERE cid IN (SELECT id FROM cards WHERE did = ?) AND id > ?",
            deck_id, thirty_days_ago
        )
        
        deck_info.append({
            'name': deck_name,
            'card_count': card_count,
            'reviews_last_30_days': review_count,
            'deck_conf': conf
        })
    
    return deck_info

if __name__ == "__main__":
    try:
        collection_path = get_anki_collection_path()
        col = Collection(collection_path)
        
        deck_info = get_deck_info(col)
        
        print("Anki Deck Information:")
        for deck in deck_info:
            print(f"{key.split('_')}: {value}" for key, value in deck.items())
        
        col.close()
    except Exception as e:
        print(f"An error occurred: {str(e)}")
        print("Make sure Anki is not running when you execute this script.")