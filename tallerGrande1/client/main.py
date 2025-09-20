# main.py
from controller.controller import ClientController, SERVE_AFTER_JOIN, CLIENT_PORT, CLIENT_NAME
from view.logger import Logger

def main():
    client = ClientController()
    ok = client.join_index()
    if not ok:
        Logger.error("No se pudo registrar en el Index. Saliendo.")
        return

    client.show_state()

    if SERVE_AFTER_JOIN:
        # Si queremos que el cliente se quede escuchando para futuras negociaciones
        client.start_peer_server(port=CLIENT_PORT)
    else:
        Logger.info("Fin (no se inició servidor de peers).")

if __name__ == "__main__":
    main()
