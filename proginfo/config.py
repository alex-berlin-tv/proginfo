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
    radio_description_header: str
    radio_description_footer: str
    radio_set_title: bool
    data_encoding: str
    next_count: int
    log_level: str
    two_titles_window_start_minutes: int
    two_titles_window_end_minutes: int


settings = ts.load(
    Settings,
    appname="proginfo",
    config_files=["settings.toml"],
)
