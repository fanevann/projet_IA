import cv2
import numpy as np


def pretraiter(pil_image):
    img = cv2.cvtColor(np.array(pil_image), cv2.COLOR_RGB2BGR)
    gris = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # 1. Fampitomboana habe
    gris = cv2.resize(gris, None, fx=1.5, fy=1.5, interpolation=cv2.INTER_CUBIC)

    # 2. Fanesorana tabataba
    gris = cv2.fastNlMeansDenoising(gris, None, h=20)

    # 3. Fanatsarana contraste
    gris = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8)).apply(gris)

    # 4. Binarisation adaptative
    bin_ = cv2.adaptiveThreshold(gris, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                 cv2.THRESH_BINARY, 31, 15)

    # 5. Alahatra (deskew)
    coords = np.column_stack(np.where(bin_ < 128))
    if len(coords) > 100:
        angle = cv2.minAreaRect(coords)[-1]
        angle = -(90 + angle) if angle < -45 else -angle
        if abs(angle) > 0.3:
            h, w = bin_.shape
            M = cv2.getRotationMatrix2D((w / 2, h / 2), angle, 1.0)
            bin_ = cv2.warpAffine(bin_, M, (w, h), flags=cv2.INTER_CUBIC,
                                  borderValue=255)
    return bin_