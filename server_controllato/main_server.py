# server_controllato/main_server.py
"""
Server per l'applicazione di assistenza remota.
Cattura lo schermo, lo codifica e lo invia al client connesso.
"""
# pylint: disable=invalid-name

import socket
import pickle
import struct
import mss  # Per catturare lo schermo
import numpy as np
import cv2  # OpenCV per l'elaborazione delle immagini # pylint: disable=import-error

# Costanti del server
HOST = '0.0.0.0'  # Ascolta su tutte le interfacce di rete disponibili
PORT = 9999       # Porta su cui ascoltare (puoi cambiarla se necessario)
# Qualità JPEG (0-100), più bassa = più veloce ma meno qualità
JPEG_QUALITY = 75


def main():
    """
    Funzione principale del server.
    Attende connessioni, cattura lo schermo e invia i frame.
    """
    # Crea un socket TCP/IP
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        # Permetti il riutilizzo dell'indirizzo per riavvii rapidi del server
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        try:
            s.bind((HOST, PORT))
            s.listen(1)  # Accetta una sola connessione per semplicità
            print(f"[*] Server in ascolto su {HOST}:{PORT}")
        except OSError as e:
            print(
                f"[!] Errore durante il bind del server: {e}. La porta potrebbe essere in uso.")
            return
        except Exception as e:  # pylint: disable=broad-exception-caught
            print(f"[!] Errore imprevisto all'avvio del server: {e}")
            return

        conn, addr = s.accept()
        with conn:
            print(f"[*] Connessione stabilita da: {addr}")

            # Oggetto per catturare lo schermo
            with mss.mss() as sct:
                # sct.monitors[0] è l'intero desktop virtuale (tutti i monitor)
                # sct.monitors[1] è il monitor primario.
                # Adatta l'indice se hai più monitor o vuoi un monitor specifico.
                monitor_definition = sct.monitors[1]

                print(f"[*] Cattura del monitor: {monitor_definition}")

                while True:
                    try:
                        # Cattura lo screenshot
                        sct_img = sct.grab(monitor_definition)

                        # Converte l'immagine catturata (BGRA) in un array NumPy
                        img_np = np.array(sct_img)

                        # Converte da BGRA a BGR per OpenCV
                        # pylint: disable=no-member
                        img_bgr = cv2.cvtColor(img_np, cv2.COLOR_BGRA2BGR)

                        # Codifica l'immagine in formato JPEG
                        encode_param = [
                            int(cv2.IMWRITE_JPEG_QUALITY), JPEG_QUALITY]  # pylint: disable=no-member
                        result, frame_encoded = cv2.imencode(
                            '.jpg', img_bgr, encode_param)  # pylint: disable=no-member

                        if not result:
                            print(
                                "[!] Errore durante la codifica JPEG dell'immagine")
                            continue

                        # Serializza il frame codificato
                        # frame_encoded è un numpy.ndarray
                        data_to_send = pickle.dumps(
                            frame_encoded, protocol=pickle.HIGHEST_PROTOCOL)

                        # Prepara il messaggio: prima la dimensione del frame, poi il frame
                        message_size = struct.pack(">L", len(data_to_send))

                        # Invia la dimensione del messaggio
                        conn.sendall(message_size)
                        # Invia i dati del frame
                        conn.sendall(data_to_send)

                        # print(f"Frame inviato: {len(data_to_send)} bytes") # Decommenta per debug
                        # Per controllare il frame rate (es. ~30 FPS):
                        # import time
                        # time.sleep(0.033)

                    except (socket.error, ConnectionResetError, BrokenPipeError) as e:
                        print(f"[!] Errore di connessione: {e}")
                        break
                    except mss.exception.ScreenShotError as e:
                        print(
                            f"[!] Errore durante la cattura dello schermo: {e}")
                        # Potrebbe succedere se lo schermo è bloccato, ecc.
                        break
                    except Exception as e:  # pylint: disable=broad-exception-caught
                        print(f"[!] Errore generico nel server: {e}")
                        # Considera di loggare l'eccezione completa per il debug:
                        # import traceback
                        # print(traceback.format_exc())
                        break
            print(f"[-] Connessione con {addr} chiusa.")


if __name__ == '__main__':
    main()
