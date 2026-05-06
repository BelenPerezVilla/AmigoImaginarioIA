# ============================================================
# reset_admin.py
# Script para resetear o crear el usuario administrador.
# Compatible con las dos versiones del proyecto:
# - versión donde hash_password devuelve "salt$hash"
# - versión donde hash_password devuelve (password_hash, salt)
# ============================================================

from database.chat_db import get_connection, hash_password, initialize_database


# ------------------------------------------------------------
# Datos del superadmin
# ------------------------------------------------------------
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "Admin12345"
ADMIN_DISPLAY_NAME = "Administrador"


def get_table_columns(cursor, table_name: str) -> set[str]:
    """
    Obtiene las columnas existentes de una tabla SQLite.

    Parámetros:
        cursor: cursor activo de SQLite
        table_name (str): nombre de la tabla

    Retorna:
        set[str]: nombres de columnas existentes
    """
    cursor.execute(f"PRAGMA table_info({table_name});")
    rows = cursor.fetchall()

    return {row["name"] for row in rows}


def build_password_values(password: str) -> tuple[str, str | None]:
    """
    Genera el hash de contraseña de forma compatible con el proyecto.

    Algunas versiones de chat_db.py devuelven:
        "salt$hash"

    Otras versiones devuelven:
        (password_hash, salt)

    Retorna:
        tuple[str, str | None]: password_hash y salt opcional
    """
    result = hash_password(password)

    # --------------------------------------------------------
    # Caso nuevo: hash_password devuelve tupla/lista de 2 valores
    # --------------------------------------------------------
    if isinstance(result, (tuple, list)) and len(result) == 2:
        return str(result[0]), str(result[1])

    # --------------------------------------------------------
    # Caso actual de tu proyecto: devuelve un solo string
    # Ejemplo: "salt$hash"
    # --------------------------------------------------------
    return str(result), None


def reset_admin_user() -> None:
    """
    Resetea o crea el usuario admin como superadmin.
    """
    # --------------------------------------------------------
    # Inicializa tablas y migraciones antes de tocar usuarios
    # --------------------------------------------------------
    initialize_database()

    # --------------------------------------------------------
    # Genera contraseña compatible con tu versión del proyecto
    # --------------------------------------------------------
    password_hash, salt = build_password_values(ADMIN_PASSWORD)

    connection = get_connection()
    cursor = connection.cursor()

    user_columns = get_table_columns(cursor, "users")

    # --------------------------------------------------------
    # Verificar si existe el usuario admin
    # --------------------------------------------------------
    cursor.execute(
        """
        SELECT id
        FROM users
        WHERE username = ?;
        """,
        (ADMIN_USERNAME,),
    )

    admin = cursor.fetchone()

    if admin:
        # ----------------------------------------------------
        # Armar UPDATE dinámico según columnas existentes
        # ----------------------------------------------------
        update_fields = []
        params = []

        if "password_hash" in user_columns:
            update_fields.append("password_hash = ?")
            params.append(password_hash)

        if "salt" in user_columns and salt is not None:
            update_fields.append("salt = ?")
            params.append(salt)

        if "display_name" in user_columns:
            update_fields.append("display_name = ?")
            params.append(ADMIN_DISPLAY_NAME)

        if "is_admin" in user_columns:
            update_fields.append("is_admin = 1")

        if "role" in user_columns:
            update_fields.append("role = 'superadmin'")

        if "account_type" in user_columns:
            update_fields.append("account_type = 'permanent'")

        if "guest_type" in user_columns:
            update_fields.append("guest_type = NULL")

        if "guest_status" in user_columns:
            update_fields.append("guest_status = 'none'")

        if "guest_created_by" in user_columns:
            update_fields.append("guest_created_by = NULL")

        if "guest_hours" in user_columns:
            update_fields.append("guest_hours = 0")

        if "guest_expires_at" in user_columns:
            update_fields.append("guest_expires_at = NULL")

        if "is_active" in user_columns:
            update_fields.append("is_active = 1")

        if "updated_at" in user_columns:
            update_fields.append("updated_at = CURRENT_TIMESTAMP")

        params.append(ADMIN_USERNAME)

        cursor.execute(
            f"""
            UPDATE users
            SET {", ".join(update_fields)}
            WHERE username = ?;
            """,
            params,
        )

        print("Usuario admin actualizado correctamente.")

    else:
        # ----------------------------------------------------
        # Armar INSERT dinámico según columnas existentes
        # ----------------------------------------------------
        insert_columns = []
        placeholders = []
        params = []

        def add_value(column_name: str, value):
            """
            Agrega una columna al INSERT solo si existe en la tabla.
            """
            if column_name in user_columns:
                insert_columns.append(column_name)
                placeholders.append("?")
                params.append(value)

        add_value("username", ADMIN_USERNAME)
        add_value("password_hash", password_hash)

        if salt is not None:
            add_value("salt", salt)

        add_value("display_name", ADMIN_DISPLAY_NAME)

        if "is_admin" in user_columns:
            insert_columns.append("is_admin")
            placeholders.append("1")

        add_value("friend_name", "Lumi")
        add_value("favorite_color", "")
        add_value("favorite_activity", "")
        add_value("encouragement_style", "")
        add_value("preferred_comfort", "cuentos")
        add_value("role", "superadmin")
        add_value("account_type", "permanent")
        add_value("guest_status", "none")

        if "is_active" in user_columns:
            insert_columns.append("is_active")
            placeholders.append("1")

        if "created_at" in user_columns:
            insert_columns.append("created_at")
            placeholders.append("CURRENT_TIMESTAMP")

        if "updated_at" in user_columns:
            insert_columns.append("updated_at")
            placeholders.append("CURRENT_TIMESTAMP")

        cursor.execute(
            f"""
            INSERT INTO users (
                {", ".join(insert_columns)}
            )
            VALUES (
                {", ".join(placeholders)}
            );
            """,
            params,
        )

        print("Usuario admin creado correctamente.")

    connection.commit()
    connection.close()

    print("----------------------------------------")
    print("Credenciales listas:")
    print(f"Usuario: {ADMIN_USERNAME}")
    print(f"Contraseña: {ADMIN_PASSWORD}")
    print("----------------------------------------")


if __name__ == "__main__":
    reset_admin_user()