This folder holds the tarot card images (WebP or PNG).

13 cards (0 The Fool to XII The Hanged Man) were exported from Figma already.
To add the other 65, run once on your computer (needs internet):

  1. In Figma: Settings > Security > Personal access tokens > Generate new token
     (read access to file content is enough).
  2. From the source_code folder:
       python scripts/export_figma_cards.py --token YOUR_TOKEN
     It knows the layer id of every card in the Figma file, saves each one with
     its proper name, and skips cards that are already here.

You can also export by hand from Figma (select the cards > Export > PNG); any file
name containing the card's name works ("The Star.png", "Ace of Cups.png", ...).
The app matches names to the 78 standard cards and sorts them into deck order.
A file named back.png is used as the card back.

Licence: see ATTRIBUTION.txt (CC BY 4.0 for the Figma file; the 1909 artwork is
public domain). Keep the credit when you publish the repository.
