import typed_settings as ts


@ts.settings
class Settings:
    domain_id: str
    api_secret: str
    session_id: str
    tv_data_url: str
    radio_data_url: str


settings = ts.load(
    Settings,
    appname="proginfo",
    config_files=["settings.settings.toml"],
)
