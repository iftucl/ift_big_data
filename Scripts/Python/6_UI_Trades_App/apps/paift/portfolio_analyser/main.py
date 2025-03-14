from shiny import App, ui, Inputs, Outputs, Session, render, reactive

from templates.headers import auth_header_template
from apps.paift.portfolio_analyser.modules.get_traders_ids import get_traders_identifiers

app_ui = ui.page_fluid(
    ui.head_content(ui.tags.link(rel="icon", type="image/x-icon", href="")),
    ui.include_css("./www/styles.css"),
    ui.output_ui("render_headers"),
    ui.h2("Trade Monitor Dashboard", class_="dashboard-title"),
    ui.layout_sidebar(
        ui.sidebar(
            ui.card(
                ui.card_header("Traders"),
                ui.input_selectize(id="traders_ids", label="Traders", choices=[], selected=None),
                class_="sidebar-card"
            )
        ),
    ui.layout_columns(
        ui.card(
            ui.card_header("Trader trades", class_="body-card-header"),
            ui.row(ui.output_data_frame("get_trades_by_trader")),
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

        traders_ids = get_traders_identifiers(endpoint="http://localhost:8010/traders/ids", user=current_user, group=current_group)        
        ui.update_selectize(id="traders_ids", label="Traders", choices=traders_ids, selected=None, server=True)
    @reactive.effect
    @reactive.event(input.traders_ids)
    def _get_trades_trader():
        pass

    @output
    @render.data_frame
    def get_trades_by_trader():
        pass




paift_run_details = App(app_ui, server)