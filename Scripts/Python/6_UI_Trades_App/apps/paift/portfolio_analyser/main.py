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
        print(traders_ids)
        ui.update_selectize(id="traders_ids", label="Traders", choices=traders_ids, selected=None, server=True)



paift_run_details = App(app_ui, server)