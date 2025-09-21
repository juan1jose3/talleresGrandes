# main.py
from controller.client_controller import ClientController
from view.logger import Logger
def main():
    client = ClientController()
    if not client.join_index():
        Logger.error("No se pudo registrar en el Index. Saliendo.")
        return

    client.show_state()
    client.run(negotiate_interval=5)

if __name__ == "__main__":
    main()

