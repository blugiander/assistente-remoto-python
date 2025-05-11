# client_controllante/main_client.py
"""
Client per l'applicazione di assistenza remota.
Si connette a un server, riceve lo stream video dello schermo remoto
e lo visualizza.
"""
# pylint: disable=invalid-name, too-many-locals

import socket
import pickle
import struct
import cv2  # pylint: disable=import-error
# numpy è necessario perché cv2.imdecode si aspetta un array numpy
# che viene prodotto da pickle.loads(frame_data)
import numpy as np  # pylint: disable=unused-import

# Costanti del server
# MODIFICA QUI: Inserisci l'indirizzo IP del PC server
SERVER_HOST = '192.168.1.200'  # Esempio: cambia con l'IP effettivo del server!
SERVER_PORT = 9999  # Deve corrispondere alla porta del server


def main():
    """
    Funzione principale del client.
    Si connette al server e gestisce lo streaming video.
    """
    payload_size = struct.calcsize(
        ">L")  # Calcola la dimensione dell'header (unsigned long)

    # Crea un socket TCP/IP
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            print(f"[*] Connessione a {SERVER_HOST}:{SERVER_PORT}...")
            s.connect((SERVER_HOST, SERVER_PORT))
            print("[*] Connesso al server.")
        except ConnectionRefusedError:
            print(
                "[!] Connessione rifiutata. Assicurati che il server sia in esecuzione "
                "e l'IP/porta siano corretti."
            )
            return
        except socket.gaierror:  # Errore risoluzione nome host
            print(
                f"[!] Errore: Impossibile risolvere l'hostname '{SERVER_HOST}'. "
                "Verifica l'indirizzo IP."
            )
            return
        except socket.timeout:
            print("[!] Errore: Timeout durante la connessione al server.")
            return
        except Exception as e:  # pylint: disable=broad-exception-caught
            print(f"[!] Errore generico durante la connessione: {e}")
            return

        data = b""  # Buffer per i dati ricevuti

        # pylint: disable=no-member
        cv2.namedWindow("Streaming Schermo Remoto", cv2.WINDOW_NORMAL)

        while True:
            try:
                # 1. Ricevi la dimensione del frame
                while len(data) < payload_size:
                    packet = s.recv(4096)  # Ricevi fino a 4KB
                    if not packet:  # Connessione chiusa
                        print(
                            "[-] Connessione chiusa dal server (ricezione dimensione).")
                        cv2.destroyAllWindows()  # pylint: disable=no-member
                        return
                    data += packet

# Estrai la dimensione del messaggio
                packed_msg_size = data[:payload_size]
                data = data[payload_size:]  # Rimuovi la dimensione dal buffer

                msg_size = struct.unpack(">L", packed_msg_size)[0]

                # 2. Ricevi i dati del frame
                while len(data) < msg_size:
                    packet = s.recv(4096)  # Ricevi fino a 4KB
                    if not packet:  # Connessione chiusa
                        print("[-] Connessione chiusa dal server (ricezione dati).")
                        cv2.destroyAllWindows()  # pylint: disable=no-member
                        return
                    data += packet

                frame_data = data[:msg_size]  # Estrai il frame
                data = data[msg_size:]  # Rimuovi il frame dal buffer

                # Deserializza il frame
                # frame_encoded è un numpy array dopo la deserializzazione
                frame_encoded = pickle.loads(frame_data)

                # Decodifica l'immagine JPEG
                # pylint: disable=no-member
                frame = cv2.imdecode(frame_encoded, cv2.IMREAD_COLOR)

                if frame is not None:
                    # Mostra il frame
                    cv2.imshow('Streaming Schermo Remoto',
                               frame)  # pylint: disable=no-member
                else:
                    print("[!] Errore nella decodifica del frame.")

                # Interrompi il loop se viene premuto 'q'
                if cv2.waitKey(1) & 0xFF == ord('q'):  # pylint: disable=no-member
                    break

            except (socket.error, ConnectionResetError, BrokenPipeError) as e:
                print(f"[!] Errore di connessione durante lo streaming: {e}")
                break
            except pickle.UnpicklingError:
                print(
                    "[!] Errore durante la deserializzazione del frame. "
                    "Dati corrotti o formato non valido."
                )
                data = b""  # Prova a resettare il buffer
                continue
            except struct.error as e:
                print(f"[!] Errore di unpacking dei dati: {e}")
                break
            except Exception as e:  # pylint: disable=broad-exception-caught
                print(
                    f"[!] Errore generico nel client durante lo streaming: {e}")
                break

        print("[-] Streaming terminato.")
        cv2.destroyAllWindows()  # pylint: disable=no-member


if __name__ == '__main__':
    main()
