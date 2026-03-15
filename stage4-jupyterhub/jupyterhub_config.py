import os

c = get_config()  # noqa: F821

# Общие настройки
c.JupyterHub.ip = "0.0.0.0"
c.JupyterHub.port = 8000

# Токен для proxy
c.ConfigurableHTTPProxy.auth_token = os.environ.get(
    "CONFIGURABLE_PROXY_AUTH_TOKEN",
    os.environ.get("JUPYTERHUB_SECRET_TOKEN", ""),
)

# Spawner — SimpleLocalProcessSpawner для запуска в одном контейнере
c.JupyterHub.spawner_class = "simple"
c.Spawner.default_url = "/lab"
c.Spawner.http_timeout = 120
c.Spawner.start_timeout = 120
c.Spawner.args = ["--allow-root"]

# Аутентификация — DummyAuthenticator (для разработки)
c.JupyterHub.authenticator_class = "dummy"

admin_user = os.environ.get("JUPYTERHUB_ADMIN_USER", "admin")
admin_password = os.environ.get("JUPYTERHUB_ADMIN_PASSWORD", "admin")

c.DummyAuthenticator.password = admin_password
c.Authenticator.admin_users = {admin_user}
c.JupyterHub.admin_access = True

# БД — SQLite в примонтированном volume
c.JupyterHub.db_url = "sqlite:///jupyterhub.sqlite"
