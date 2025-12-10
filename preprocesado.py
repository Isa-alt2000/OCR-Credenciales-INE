import cv2
import numpy as np


# [y1, y2, x1, x2]
REGIONES_INE = {
    'apellido_paterno': [337, 397, 594, 1410],
    'apellido_materno': [397, 457, 594, 1410],
    'nombre': [457, 517, 594, 1410],
    'domicilio': [576, 755, 591, 1620],
    'clave_elector': [765, 834, 945, 1564],
    'curp': [838, 901, 707, 1303],
    'fecha_nacimiento': [330, 400, 1490, 1893],
    'sexo': [394, 462, 1775, 1870],
}


def main_alineadores(imagen_escaneada, ine_referencia):
    """
    Args:
        imagen_escaneada: Path
        ine_referencia: Path
    Returns:
        Array numpy de imagen alineada
    Función que intenta alinear la imagen usando dos métodos diferentes
    """

    try:
        return alinear_ine_principal(imagen_escaneada, ine_referencia)
    except Exception as e:
        print(f"Método principal falló: {e}")
        print("Intentando con método secundario...")

        try:
            return alinear_ine_secundario(imagen_escaneada, ine_referencia)
        except Exception as e2:
            print(f"Método secundario falló: {e2}")
            raise ValueError("No se pudo alinear la imagen con ningún método")


def alinear_ine_principal(imagen_escaneada, ine_referencia):
    """
    Args:
        imagen_escaneada: Path
        ine_referencia: Path
    Returns:
        Array numpy de imagen alineada
    Alinea la imagen del INE usando ORB y homografía con validaciones robustas
    """

    im_template = cv2.imread(ine_referencia)
    im_scan = cv2.imread(imagen_escaneada)

    if im_template is None or im_scan is None:
        raise ValueError("No se pudo cargar una o ambas imágenes")

    # escala de grises
    gray_template = cv2.cvtColor(im_template, cv2.COLOR_BGR2GRAY)
    gray_scan = cv2.cvtColor(im_scan, cv2.COLOR_BGR2GRAY)

    # Normalizar histogramas para mejorar detección
    gray_template = cv2.equalizeHist(gray_template)
    gray_scan = cv2.equalizeHist(gray_scan)

    # Detectar características ORB con más puntos
    orb = cv2.ORB_create(
        nfeatures=30000,
        scaleFactor=1.2,
        nlevels=8,
        edgeThreshold=15,
        patchSize=31
    )

    kp1, desc1 = orb.detectAndCompute(gray_scan, None)
    kp2, desc2 = orb.detectAndCompute(gray_template, None)

    if desc1 is None or desc2 is None or len(kp1) < 10 or len(kp2) < 10:
        raise ValueError("No se pudieron detectar suficientes características")

    # Matching con ratio test de Lowe
    matcher = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=False)
    matches = matcher.knnMatch(desc1, desc2, k=2)

    # Filtrar matches con ratio test
    good_matches = []
    for match_pair in matches:
        if len(match_pair) == 2:
            m, n = match_pair
            if m.distance < 0.75 * n.distance:  # Ratio test
                good_matches.append(m)

    if len(good_matches) < 30:
        raise ValueError(f"Muy pocos matches de calidad: {len(good_matches)}")

    # Extraer puntos
    pts1 = np.float32([kp1[m.queryIdx].pt for m in good_matches])
    pts2 = np.float32([kp2[m.trainIdx].pt for m in good_matches])

    # Calcular homografía con RANSAC más estricto
    h, mask = cv2.findHomography(
        pts1, pts2, 
        cv2.RANSAC, 
        ransacReprojThreshold=3.0,
        maxIters=5000,
        confidence=0.995
    )

    if h is None:
        raise ValueError("No se pudo calcular la homografía")

    # Validar homografía para evitar deformaciones extremas
    if not validar_homografia(h, im_scan.shape, im_template.shape):
        raise ValueError("Homografía inválida - deformación excesiva detectada")

    # Contar inliers
    inliers = np.sum(mask)
    total = len(mask)
    ratio_inliers = inliers / total

    if ratio_inliers < 0.3:
        (f"Muy pocos inliers: {ratio_inliers:.2%}")

    # Alinear imagen
    height, width = im_template.shape[:2]
    aligned = cv2.warpPerspective(
        im_scan, h, (width, height),
        flags=cv2.INTER_LINEAR,
        borderMode=cv2.BORDER_CONSTANT,
        borderValue=(255, 255, 255)
    )

    return aligned


def validar_homografia(h, shape_src, shape_dst, max_scale=3.0, max_shear=0.5):
    """
    Valida que la homografía no cause deformaciones excesivas
    """
    try:
        # Descomponer la homografía
        h_norm = h / h[2, 2]

        # Extraer componentes de transformación
        a = h_norm[0, 0]
        b = h_norm[0, 1]
        c = h_norm[1, 0]
        d = h_norm[1, 1]

        # Calcular escalas en X y Y
        scale_x = np.sqrt(a**2 + c**2)
        scale_y = np.sqrt(b**2 + d**2)

        # Verificar escalas razonables
        if scale_x > max_scale or scale_y > max_scale:
            return False
        if scale_x < 1/max_scale or scale_y < 1/max_scale:
            return False

        # Calcular shear (deformación angular)
        shear = abs(a*b + c*d) / (scale_x * scale_y)
        if shear > max_shear:
            return False

        # Verificar que las esquinas mapeadas estén dentro de límites razonables
        h_src, w_src = shape_src[:2]
        h_dst, w_dst = shape_dst[:2]

        corners_src = np.float32([
            [0, 0], [w_src, 0], 
            [w_src, h_src], [0, h_src]
        ]).reshape(-1, 1, 2)

        corners_dst = cv2.perspectiveTransform(corners_src, h)

        # Verificar que ninguna esquina esté muy fuera de la imagen destino
        margin = max(w_dst, h_dst) * 0.5
        for corner in corners_dst:
            x, y = corner[0]
            if x < -margin or x > w_dst + margin:
                return False
            if y < -margin or y > h_dst + margin:
                return False

        return True

    except Exception as e:
        print(f"Error validando homografía: {e}")
        return False


def alinear_ine_secundario(imagen_escaneada, ine_referencia):
    """
    Args:
        imagen_escaneada: Path
        ine_referencia: Path
    Returns:
        Array numpy de imagen alineada
    Versión con parámetros menos estrictos para casos difíciles
    """

    im_template = cv2.imread(ine_referencia)
    im_scan = cv2.imread(imagen_escaneada)

    gray_template = cv2.equalizeHist(cv2.cvtColor(im_template, cv2.COLOR_BGR2GRAY))
    gray_scan = cv2.equalizeHist(cv2.cvtColor(im_scan, cv2.COLOR_BGR2GRAY))

    # SIFT es más robusto que ORB para casos difíciles
    # Si no tienes SIFT, puedes usar AKAZE como alternativa
    try:
        detector = cv2.SIFT_create(nfeatures=5000)
    except Exception as e:
        print(f"Error creando detector: {e}")
        detector = cv2.AKAZE_create()

    kp1, desc1 = detector.detectAndCompute(gray_scan, None)
    kp2, desc2 = detector.detectAndCompute(gray_template, None)

    if desc1 is None or desc2 is None:
        raise ValueError("No se detectaron características")

    # Matcher apropiado según el descriptor
    if len(desc1[0]) == 128:  # SIFT
        matcher = cv2.BFMatcher(cv2.NORM_L2, crossCheck=False)
    else:  # AKAZE u otros binarios
        matcher = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=False)

    matches = matcher.knnMatch(desc1, desc2, k=2)

    good_matches = []
    for match_pair in matches:
        if len(match_pair) == 2:
            m, n = match_pair
            if m.distance < 0.8 * n.distance:
                good_matches.append(m)

    if len(good_matches) < 20:
        raise ValueError(f"Matches insuficientes: {len(good_matches)}")

    pts1 = np.float32([kp1[m.queryIdx].pt for m in good_matches])
    pts2 = np.float32([kp2[m.trainIdx].pt for m in good_matches])

    h, mask = cv2.findHomography(pts1, pts2, cv2.RANSAC, 5.0)

    if h is None or not validar_homografia(h, im_scan.shape, im_template.shape, max_scale=2.5):
        raise ValueError("Homografía inválida")

    height, width = im_template.shape[:2]
    aligned = cv2.warpPerspective(im_scan, h, (width, height))

    return aligned


def limpiar_fondo_fecha_nacimiento(img, regiones, clave_region):
    """
    Args:
        img: Array numpy de imagen
        regiones: Diccionario con regiones
        clave_region: Clave de la región a limpiar
    Returns:
        Array numpy de imagen con campo limpiado
    Elimina líneas de color específico dentro de una región definida en el diccionario,
    protegiendo dinámicamente el texto oscuro.
    """

    y1, y2, x1, x2 = regiones[clave_region]
    roi = img[y1:y2, x1:x2]

    # --- 1. Detectar lo que queremos BORRAR (Color Morado/Vino) ---
    target_bgr = (113, 85, 128) # #805571
    tolerancia = 35 # Tolerancia amplia porque confiamos en la protección de texto
    
    lower_bound = np.array([max(c - tolerancia, 0) for c in target_bgr])
    upper_bound = np.array([min(c + tolerancia, 255) for c in target_bgr])
    
    mask_fondo = cv2.inRange(roi, lower_bound, upper_bound)
    
    # Dilatar fondo para cubrir bordes difusos del color
    kernel = np.ones((2,2), np.uint8)
    mask_fondo = cv2.dilate(mask_fondo, kernel, iterations=1)


    # --- 2. Detectar lo que queremos PROTEGER (Texto Negro/Oscuro) ---
    # Convertimos a gris
    gray_roi = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
    
    # --- CAMBIO IMPORTANTE: Umbral Dinámico (Otsu) ---
    # Usamos THRESH_OTSU para que calcule el umbral óptimo automáticamente.
    # 'otsu_thresh' guardará el valor calculado (ej. 85, 110, etc.)
    otsu_thresh, mask_texto = cv2.threshold(gray_roi, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)

    # (Opcional) Validación de seguridad:
    # Si la imagen está muy dañada, Otsu podría fallar dando valores extremos.
    # Forzamos rangos lógicos para texto (entre 50 y 160).
    print
    if otsu_thresh < 50:
        _, mask_texto = cv2.threshold(gray_roi, 50, 255, cv2.THRESH_BINARY_INV)
    elif otsu_thresh > 160:
        _, mask_texto = cv2.threshold(gray_roi, 200, 255, cv2.THRESH_BINARY_INV)

    # Dilatar un poco la protección para cubrir bordes finos de las letras
    mask_texto = cv2.dilate(mask_texto, np.ones((2,2), np.uint8), iterations=1)

    # --- 3. Combinar máscaras: (Fondo a borrar) - (Texto a proteger) ---
    # Borrar SOLO donde hay 'mask_fondo' Y NO hay 'mask_texto'
    mask_final = cv2.bitwise_and(mask_fondo, mask_fondo, mask=cv2.bitwise_not(mask_texto))

    # --- 4. Reemplazo ---
    fondo_limpio = (240, 240, 240) # Gris muy claro
    roi[mask_final > 0] = fondo_limpio

    img[y1:y2, x1:x2] = roi
    return img


def procesado(alineada, gamma=1.0, contraste=1.7, brillo=20, usar_clahe=True, umbral=250):
    img = alineada.copy()
    limpiar_fondo_fecha_nacimiento(img, REGIONES_INE, 'fecha_nacimiento')
    limpiar_fondo_fecha_nacimiento(img, REGIONES_INE, 'sexo')

    # Asegurar tipo y rango
    if img.dtype != np.uint8:
        img = cv2.convertScaleAbs(img)

    # Corrección gamma para brillo/contraste
    if gamma != 1.0:
        # O = I^(1/gamma) * 255
        inv_gamma = 1.0 / gamma
        # Construir lookup table para eficiencia
        table = np.array([((i / 255.0) ** inv_gamma) * 255 for i in np.arange(256)]).astype("uint8")
        img = cv2.LUT(img, table)

    # 3) Ajuste global de contraste y brillo
    img = cv2.convertScaleAbs(img, alpha=contraste, beta=brillo)

    # 4) Mejora local de contraste (opcional)
    if usar_clahe:
        # Convertir a YCrCb para aplicar CLAHE solo al canal luminancia
        lab = cv2.cvtColor(img, cv2.COLOR_BGR2LAB)
        l, a, b = cv2.split(lab)
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        cl = clahe.apply(l)
        lab = cv2.merge((cl, a, b))
        img = cv2.cvtColor(lab, cv2.COLOR_LAB2BGR)

    # 5) Binarización opcional para OCR
    if umbral is not None:
        # Convierte a gris, aplica umbral y vuelve a BGR
        gris = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        _, thresh = cv2.threshold(gris, umbral, 255, cv2.THRESH_BINARY)
        img = cv2.cvtColor(thresh, cv2.COLOR_GRAY2BGR)

    return img


def extraer_regiones(imagen_alineada, regiones):
    """
    Extrae cada región y aplica preprocesamiento
    """
    gray = cv2.cvtColor(imagen_alineada, cv2.COLOR_BGR2GRAY)
    regiones_extraidas = {}

    for nombre_campo, coords in regiones.items():
        y1, y2, x1, x2 = coords
        roi = gray[y1:y2, x1:x2]

        # Preprocesamiento para mejorar OCR
        roi = cv2.GaussianBlur(roi, (3, 3), 0)
        roi = cv2.threshold(roi, 0, 255,
                            cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]

        # Opcional: aumentar contraste
        roi = cv2.equalizeHist(roi)

        regiones_extraidas[nombre_campo] = roi

    return regiones_extraidas