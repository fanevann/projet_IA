import os, glob, random
import cv2
import numpy as np
from pdf2image import convert_from_path

random.seed(7)
np.random.seed(7)

NIVEAUX = {
    #            rotation, flou(kernel), bruit(sigma), contraste
    "leger":    (1.0, 1, 6, 1.0),
    "moyen":    (2.0, 3, 15, 0.9),
    "fort":     (3.0, 5, 28, 0.75),
    "extreme":  (6.0, 9, 45, 0.5),
    "terrible": (10.0, 13, 65, 0.35),
}


def degrader(img_bgr, rot_max, flou, sigma, contraste):
    # 0. Fampihenana résolution (sary kalitao ambany)
    if sigma >= 45:
        h0, w0 = img_bgr.shape[:2]
        k = 0.5 if sigma < 60 else 0.35
        img_bgr = cv2.resize(img_bgr, (int(w0 * k), int(h0 * k)),
                             interpolation=cv2.INTER_AREA)
        img_bgr = cv2.resize(img_bgr, (w0, h0), interpolation=cv2.INTER_LINEAR)

    h, w = img_bgr.shape[:2]

    # 1. Rotation (hodinkodina)
    angle = random.uniform(-rot_max, rot_max)
    M = cv2.getRotationMatrix2D((w / 2, h / 2), angle, 1.0)
    img = cv2.warpAffine(img_bgr, M, (w, h), borderValue=(255, 255, 255))

    # 2. Flou
    if flou > 1:
        img = cv2.GaussianBlur(img, (flou, flou), 0)

    # 3. Contraste ambany (ranjo kokoa)
    img = cv2.convertScaleAbs(img, alpha=contraste, beta=(1 - contraste) * 120)

    # 4. Tabataba
    bruit = np.random.normal(0, sigma, img.shape).astype(np.float32)
    img = np.clip(img.astype(np.float32) + bruit, 0, 255).astype(np.uint8)
    return img


if __name__ == "__main__":
    for niveau, (rot, flou, sigma, contraste) in NIVEAUX.items():
        out = f"data/factures_scan/{niveau}"
        os.makedirs(out, exist_ok=True)
        for pdf in sorted(glob.glob("data/factures/*.pdf")):
            page = convert_from_path(pdf, dpi=200)[0]
            img = cv2.cvtColor(np.array(page), cv2.COLOR_RGB2BGR)
            img = degrader(img, rot, flou, sigma, contraste)
            nom = os.path.basename(pdf).replace(".pdf", ".jpg")
            cv2.imwrite(os.path.join(out, nom), img, [cv2.IMWRITE_JPEG_QUALITY, 85])
        print(f"{niveau}: fait -> {out}")