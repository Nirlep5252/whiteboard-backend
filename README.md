# Realtime whiteboard backend

## How to run?

- Make sure the Keycloak docker is running.

- Prepare the `.env` file that contains the following variables:

    ```env
    KEYCLOAK_URL=""
    KEYCLOAK_REALM=""
    KEYCLOAK_CLIENT=""
    KEYCLOAK_PUBLIC_KEY=""
    DATABASE_URL=""
    ```

- Install the requirements:

    ```bash
    pip install -r requirements.txt
    ```

- Start the server

    ```bash
    python3 -m uvicorn main:app --reload
    ```
