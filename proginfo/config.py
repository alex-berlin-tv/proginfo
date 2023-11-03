import typed_settings as ts


@ts.settings
class Settings:
    domain_id: str
    api_secret: str
    session_id: str
    tv_data_url: str
    tv_id: int
    tv_prefix: str
    tv_description_footer: str
    radio_data_url: str
    radio_id: int
    radio_prefix: str
    radio_description_footer: str
    data_encoding: str
    next_count: int
    log_level: str


settings = ts.load(
    Settings,
    appname="proginfo",
    config_files=["settings.toml"],
)
