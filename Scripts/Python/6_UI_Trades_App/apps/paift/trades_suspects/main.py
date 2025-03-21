from shiny import App, ui, Inputs, Outputs, Session, render, reactive, req
import pandas as pd

from templates.headers import auth_header_template
from apps.paift.trades_suspects.modules.get_traders_ids import get_traders_identifiers, get_trades_suspects_by_trader


LAMBRO_ENDPOINT = "http://localhost:8010"

app_ui = ui.page_fluid(
    ui.head_content(ui.tags.link(rel="icon", type="image/x-icon", href="")),
    ui.include_css("./www/styles.css"),
    ui.output_ui("render_headers"),
    ui.h2("Suspects Monitor Dashboard", class_="dashboard-title"),
    ui.layout_sidebar(
        ui.sidebar(
            ui.card(
                ui.card_header("Traders"),
                ui.input_selectize(id="traders_ids", label="Traders", choices=[], selected=None),
                height=600,
                class_="sidebar-card"
            )
        ),
    ui.layout_columns(
        ui.card(
            ui.card_header("Trader Suspects", class_="body-card-header"),
            ui.row(ui.output_data_frame("render_trades_by_trader_df")),
            full_screen=True
        )
    )
    )
)

def server(input: Inputs, output: Outputs, session: Session):
    current_user = session.http_conn.headers.get("x-forwarded-email", "").replace("@ucl.ac.uk", "")
    current_group = session.http_conn.scope["auth"].scopes[0]

    @render.ui
    def render_headers():
        return ui.HTML(auth_header_template.format(username = current_user, group=current_group))
    @reactive.effect
    def _():
        traders_ids = get_traders_identifiers(endpoint=f"{LAMBRO_ENDPOINT}/traders/ids", user=current_user, group=current_group)        
        ui.update_selectize(id="traders_ids", label="Traders", choices=traders_ids, selected=None, server=True)
    @reactive.calc    
    def dynamic_get_trades_suspects_trader():
        req(input.traders_ids())
        return get_trades_suspects_by_trader(trader_id=input.traders_ids(), endpoint=LAMBRO_ENDPOINT, user=current_user, group=current_group)

    @output
    @render.data_frame
    def render_trades_by_trader_df():
        list_trades = dynamic_get_trades_suspects_trader()
        return render.DataGrid(pd.DataFrame(list_trades))




paift_trades_suspects = App(app_ui, server)