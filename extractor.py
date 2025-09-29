import cv2
import os
from PIL import Image
from fpdf import FPDF
import numpy as np

def autocrop_image(image_path):
    """
    Rimuove automaticamente le bande nere (letterbox/pillarbox) da un'immagine.
    Restituisce un oggetto PIL Image ritagliato.
    """
    try:
        img_pil = Image.open(image_path)
        img_cv = np.array(img_pil)
        
        if img_cv.ndim == 3:
            gray = cv2.cvtColor(img_cv, cv2.COLOR_BGR2GRAY)
        else:
            gray = img_cv

        _, thresh = cv2.threshold(gray, 10, 255, cv2.THRESH_BINARY) 
        coords = cv2.findNonZero(thresh)
        if coords is None:
            return img_pil

        x, y, w, h = cv2.boundingRect(coords)
        cropped_img_cv = img_cv[y:y+h, x:x+w]
        return Image.fromarray(cropped_img_cv)
    except Exception as e:
        print(f"Errore durante il ritaglio: {e}")
        return Image.open(image_path)

def extract_and_create_score_two_per_page(video_path, output_pdf_name, threshold=50000, cooldown_frames=40, brightness_threshold=30, initial_jump_frames=10):
    """
    Estrae i cambi di pagina da un video, rimuove le bande nere e li salva in un PDF stampabile,
    con due immagini per pagina, impilate verticalmente.
    """
    
    temp_dir = "temp_extracted_pages"
    if not os.path.exists(temp_dir):
        os.makedirs(temp_dir)

    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        print(f"Errore: Non è stato possibile aprire il file video {video_path}")
        return

    saved_pages = []
    prev_gray = None
    first_frame_saved = False
    
    print(f"Processing video: {video_path}...")
    
    # Gestione del primo fotogramma
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        
        # Ignoriamo i fotogrammi completamente neri
        if cv2.mean(frame)[0] > 5:  # Una soglia molto bassa per il nero
            # Fai un salto in avanti per superare la dissolvenza iniziale
            cap.set(cv2.CAP_PROP_POS_FRAMES, cap.get(cv2.CAP_PROP_POS_FRAMES) + initial_jump_frames)
            ret, frame = cap.read()
            
            if ret:
                page_path_temp = os.path.join(temp_dir, f"page_0_temp.jpg")
                cv2.imwrite(page_path_temp, frame)
                
                cropped_pil_img = autocrop_image(page_path_temp)
                page_path_final = os.path.join(temp_dir, f"page_0.jpg")
                cropped_pil_img.save(page_path_final)
                saved_pages.append(page_path_final)
                print(f"Salvato il primo fotogramma valido come {page_path_final}")
                os.remove(page_path_temp)
                first_frame_saved = True
                prev_gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                break
            else:
                break
    
    # Gestione dei successivi cambi di pagina
    cooldown = 0
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        
        current_gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        if prev_gray is None:
            prev_gray = current_gray
            continue

        if cooldown > 0:
            cooldown -= 1
            prev_gray = current_gray
            continue
            
        frame_diff = cv2.absdiff(current_gray, prev_gray)
        diff_count = cv2.countNonZero(cv2.threshold(frame_diff, 30, 255, cv2.THRESH_BINARY)[1])

        if diff_count > threshold:
            page_path_temp = os.path.join(temp_dir, f"page_{len(saved_pages)}_temp.jpg")
            cv2.imwrite(page_path_temp, frame)
            
            cropped_pil_img = autocrop_image(page_path_temp)
            page_path_final = os.path.join(temp_dir, f"page_{len(saved_pages)}.jpg")
            cropped_pil_img.save(page_path_final)
            saved_pages.append(page_path_final)
            print(f"Salvato il fotogramma {len(saved_pages)} (ritagliato) come {page_path_final}")
            os.remove(page_path_temp)
            cooldown = cooldown_frames
        
        prev_gray = current_gray

    cap.release()
    cv2.destroyAllWindows()
    
    if not saved_pages:
        print("Errore: Impossibile trovare fotogrammi validi da salvare.")
        
    print("\nEstrazione completata. Creazione del PDF...")

    pdf = FPDF('P', 'mm', 'A4')
    a4_width = 210
    a4_height = 297
    margin = 5
    
    for i, page_image_path in enumerate(saved_pages):
        if i % 2 == 0:
            pdf.add_page()
            
        try:
            img = Image.open(page_image_path)
            original_width, original_height = img.size
            
            max_width_mm = a4_width - 2 * margin
            max_height_mm = (a4_height - 3 * margin) / 2

            if (original_width / original_height) > (max_width_mm / max_height_mm):
                new_width_mm = max_width_mm
                new_height_mm = new_width_mm * original_height / original_width
            else:
                new_height_mm = max_height_mm
                new_width_mm = new_height_mm * original_width / original_height
            
            x_pos = margin + (max_width_mm - new_width_mm) / 2
            if i % 2 == 0:
                y_pos = margin
            else:
                y_pos = margin + max_height_mm + margin
            
            pdf.image(page_image_path, x=x_pos, y=y_pos, w=new_width_mm, h=new_height_mm)
            
        except Exception as e:
            print(f"Errore durante l'elaborazione dell'immagine {page_image_path}: {e}")
            continue

    pdf.output(output_pdf_name)
    print(f"PDF creato con successo: {output_pdf_name}")

    for file in os.listdir(temp_dir):
        os.remove(os.path.join(temp_dir, file))
    os.rmdir(temp_dir)
    print("File temporanei puliti.")

if __name__ == "__main__":
    video_list_file = "video_list.txt"
    
    try:
        with open(video_list_file, 'r') as f:
            video_paths = [line.strip() for line in f.readlines() if line.strip()]
    except FileNotFoundError:
        print(f"Errore: File '{video_list_file}' non trovato.")
        print("Crea il file e inserisci i percorsi completi dei video, uno per riga.")
        exit()

    if not video_paths:
        print("Il file della lista video è vuoto. Aggiungi i percorsi dei video e riprova.")
    else:
        for video_path in video_paths:
            base_name = os.path.splitext(os.path.basename(video_path))[0]
            output_pdf = f"{base_name}_score.pdf"

            print(f"\nElaborazione del video: {video_path}")
            extract_and_create_score_two_per_page(
                video_path,
                output_pdf,
                threshold=50000,
                cooldown_frames=40,
                brightness_threshold=30,
                initial_jump_frames=40  # Puoi regolare questo valore per il tuo video
            )
