import sys
from PIL import Image
import pytesseract

chemin = sys.argv[1] if len(sys.argv) > 1 else "data/factures/test.png"
texte = pytesseract.image_to_string(Image.open(chemin), lang="fra+eng")
print(texte)